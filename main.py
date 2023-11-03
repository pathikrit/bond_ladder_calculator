from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dateutil import rrule
import logging

import numpy as np
import pandas as pd
import streamlit as st

######### INPUTS ###########

TARGET_MONTHLY_CASHFLOW_BY_YEAR = {
    2025: 34000,
    2026: 35000,
    2027: 36000,
    2028: 37000,
    2029: 38000,
    2030: 39000,
    2031: 40000,
    2032: 41000,
    2033: 42000,
    2034: 43000,
    2035: 44000,
    2036: 45000,
    2037: 46000,
    2038: 47000,
    2039: 48000,
    2040: 44000,
    2041: 45000,
    2042: 46000,
    2043: 47000,
    2044: 48000,
    2045: 49000,
    2046: 50000,
    2047: 51000,
    2048: 52000
}
FIDELITY_FIXED_INCOME_SEARCH_RESULTS = [
    '~/Downloads/CDs.csv',
    '~/Downloads/Treasury.csv'
]
CASH_OUT_APR = 1.0 / 100  # APR if we simply hold cash

###########################################

plan = pd.DataFrame(data=list(TARGET_MONTHLY_CASHFLOW_BY_YEAR.items()), columns=['year', 'target_monthly_cashflow'])
plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12
plan['cashflow'] = 0
plan = plan.set_index('year')
START_DATE = date(plan.index.min(), 1, 1)

securities = pd.concat([pd.read_csv(file) for file in FIDELITY_FIXED_INCOME_SEARCH_RESULTS])
securities['cusip'] = securities['Cusip'].str.replace('="', '').str.replace('"', '')
securities = securities.set_index('cusip')
securities['rate'] = securities['Coupon'] / 100
securities['price'] = securities['Price Ask']
securities['redemption'] = 100
securities['yield'] = securities['Ask Yield to Worst']
securities['maturity_date'] = pd.to_datetime(securities['Maturity Date'], format='%m/%d/%Y')
securities['buy'] = 0
securities = securities.dropna(subset=['rate'])
securities = securities[securities['Attributes'].str.contains('CP')]  # Non-callable bonds only


def buy(end_date: date):
    if end_date < START_DATE:
        return

    def cash_adjusted_yield(row):
        months_in_between = end_date.month - row['maturity_date'].month + 12 * (end_date.year - row['maturity_date'].year)
        return 0 if months_in_between <= 0 else row['yield'] / 100 - months_in_between * CASH_OUT_APR / 12

    securities['cash_adjusted_yield'] = securities.apply(cash_adjusted_yield, axis=1)
    security = securities[securities['cash_adjusted_yield'] == securities['cash_adjusted_yield'].max()] \
        .sort_values(by=['maturity_date'], ascending=False).iloc[0]
    cusip = security.name

    logging.debug(f"Found CUSIP={cusip} for maturity={security['maturity_date']} to cover until end_date={end_date}")
    plan[f'cashflow_{cusip}'] = 0.0

    cash_needed_at_maturity = 0
    for date in reversed(list(rrule.rrule(rrule.MONTHLY, dtstart=security['maturity_date'].replace(day=1), until=end_date))):
        if not date.year in plan.index:
            continue
        cash_needed_for_this_month = plan.loc[date.year, 'target_cashflow'] / date.month
        plan.loc[date.year, 'target_cashflow'] -= cash_needed_for_this_month
        plan.loc[date.year, f'cashflow_{cusip}'] += cash_needed_for_this_month
        cash_needed_at_maturity += cash_needed_for_this_month
        logging.debug(f"\tCash needed for {date} = {cash_needed_for_this_month}")

    quantity = max(0, cash_needed_at_maturity) // security['redemption']
    securities.loc[cusip, 'buy'] = quantity

    for date in rrule.rrule(rrule.YEARLY, dtstart=START_DATE, until=security['maturity_date']):
        dividend = security['rate'] * security['redemption'] * quantity
        plan.loc[date.year, f'cashflow_{cusip}'] += dividend
        plan.loc[date.year, 'target_cashflow'] -= dividend

    plan['cashflow'] += plan[f'cashflow_{cusip}']
    buy(security['maturity_date'].date() - relativedelta(days=1))


class Styles:
    @staticmethod
    def money(decimals=0):
        return f'$ {{:,.{decimals}f}}'

    @staticmethod
    def percent(decimals=2):
        return f'{{:,.{decimals}f}}%'

    @staticmethod
    def date():
        return lambda t: t.strftime("%Y-%m-%d")

    @staticmethod
    def string():
        return lambda d: ' '.join(d.split())


if __name__ == "__main__":
    buy(date(plan.index.max(), 12, 31))
    securities['amount'] = securities['price'] * securities['buy']
    plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12

    st.metric(
        label='Total Investment',
        value=Styles.money().format(int(securities['amount'].sum()))
    )

    st.dataframe(
        data=securities[['Coupon', 'price', 'yield', 'maturity_date', 'buy', 'amount', 'Description', ]]
        .assign(bought=securities['buy'] > 0)
        .sort_values(by=['bought', 'maturity_date', 'yield'], ascending=False)
        .replace(0, np.nan)
        .style.format({
            'rate': Styles.percent(),
            'price': Styles.money(2),
            'Coupon': Styles.percent(),
            'yield': Styles.percent(),
            'maturity_date': Styles.date(),
            'amount': Styles.money(),
            'Description': Styles.string()
        })
    )

    st.dataframe(
        data=plan
        .replace(0, np.nan)
        .style.format({col: Styles.money() for col in plan.columns}),
        column_config={
            '_index': st.column_config.NumberColumn(label='Year', format='%d')
        }
    )

# TODO: add tests
