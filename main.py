from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dateutil import rrule

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
    '~/Downloads/Fidelity_FixedIncome_SearchResults.csv'
]
CASH_OUT_APR = 1.0 / 100  # APR if we simply hold cash

###########################################

plan = pd.DataFrame(data=list(TARGET_MONTHLY_CASHFLOW_BY_YEAR.items()), columns=['year', 'target_monthly_cashflow'])
plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12
plan['cashflow'] = 0
plan = plan.set_index('year')

securities = pd.concat([pd.read_csv(file) for file in FIDELITY_FIXED_INCOME_SEARCH_RESULTS])
securities = securities.dropna(subset=['rate'])
securities = securities[securities['Attributes'].str.contains('CP')]  # Non-callable bonds only
securities['cusip'] = securities['Cusip'].str.replace('="', '').str.replace('"', '')
securities = securities.set_index('cusip')
securities['rate'] = securities['Coupon'] / 100
securities['price'] = securities['Price Ask']
securities['redemption'] = 100
securities['yield'] = securities['Ask Yield to Worst'] / 100
securities['maturity_date'] = pd.to_datetime(securities['Maturity Date'], format='%m/%d/%Y')
securities['buy'] = 0


def buy(end_date: date):
    if end_date.year < plan.index.min():
        return

    def cash_adjusted_yield(row):
        months_in_between = end_date.month - row['maturity_date'].month + 12 * (end_date.year - row['maturity_date'].year)
        return 0 if months_in_between <= 0 else row['yield'] - months_in_between * CASH_OUT_APR / 12

    securities['cash_adjusted_yield'] = securities.apply(cash_adjusted_yield, axis=1)
    security = securities[securities['cash_adjusted_yield'] == securities['cash_adjusted_yield'].max()].sort_values(by=['maturity_date'], ascending=False).iloc[0]
    cusip = security.name

    print(f"Found CUSIP = {cusip} for {end_date} with maturity={security['maturity_date']}")
    plan[f'cashflow_{cusip}'] = 0
    for date in reversed(list(rrule.rrule(rrule.MONTHLY, dtstart=security['maturity_date'].replace(day=1), until=end_date))):
        if not date.year in plan.index:
            continue
        cash_for_this_month = plan.loc[date.year, 'target_cashflow'] / date.month
        plan.loc[date.year, 'target_cashflow'] -= cash_for_this_month
        plan.loc[date.year, f'cashflow_{cusip}'] += cash_for_this_month
        print(f"\tCash needed for {date} = {cash_for_this_month}")

    plan['cashflow'] += plan[f'cashflow_{cusip}']
    securities.loc[cusip, 'buy'] = plan[f'cashflow_{cusip}'].sum() // security['redemption']
    buy(security['maturity_date'] - relativedelta(days=1))


class STREAMLIT_FORMATS(object):  # TODO use Styler
    CURRENCY = '$ %d'
    PERCENT = '%.2f%%'
    NUMBER = '%d'


if __name__ == "__main__":
    buy(date(plan.index.max(), 12, 31))
    securities['amount'] = securities['price'] * securities['buy']
    plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12

    st.metric(
        label='Total Investment',
        value='$ ' + str(int(securities['amount'].sum()))
    )

    st.dataframe(
        data=securities[['Coupon', 'price', 'yield', 'maturity_date', 'buy', 'amount']]
        .assign(bought=securities['buy'] > 0)
        .sort_values(by=['bought', 'maturity_date', 'yield'], ascending=False),
        column_config={
            '_index': st.column_config.TextColumn(label='CUSIP'),
            'Coupon': st.column_config.NumberColumn(format=STREAMLIT_FORMATS.PERCENT),
            'maturity_date': st.column_config.DateColumn(label='Maturity', format='YYYY-MM-DD'),
            'price': st.column_config.NumberColumn(label='Price', format=STREAMLIT_FORMATS.CURRENCY),
            'yield': st.column_config.NumberColumn(label='Yield', format=STREAMLIT_FORMATS.PERCENT),
            'buy': st.column_config.NumberColumn(label='Buy', format=STREAMLIT_FORMATS.NUMBER),
            'amount': st.column_config.NumberColumn(label='Amount', format=STREAMLIT_FORMATS.CURRENCY),
        }
    )

    st.dataframe(
        data=plan,
        column_config={col: st.column_config.NumberColumn(format=STREAMLIT_FORMATS.CURRENCY if 'cashflow' in col else STREAMLIT_FORMATS.NUMBER) for col in
                       (plan.columns + ['_index'])}  # TODO: format year
    )

### TODO
# 1. Unit tests
# 2. add function types
# 3. logging
####
