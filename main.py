from datetime import date, datetime
from dateutil.relativedelta import relativedelta
from dateutil import rrule

import pandas as pd
import streamlit as st

#### This is the input to this program ####

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
PAYOUT_MONTHS = 12  # TODO: remove
CASH_OUT_APR = 1.0 / 100  # APR if we simply hold cash

###########################################

plan = pd.DataFrame(data=list(TARGET_MONTHLY_CASHFLOW_BY_YEAR.items()), columns=['year', 'target_monthly_cashflow'])
plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12
plan['cashflow'] = 0
plan = plan.set_index('year')

securities = pd.concat([pd.read_csv(file) for file in FIDELITY_FIXED_INCOME_SEARCH_RESULTS])
securities['cusip'] = securities['Cusip'].str.replace('="', '').str.replace('"', '')
securities.set_index('cusip') # TODO set index here
securities['rate'] = securities['Coupon'] / 100
securities['price'] = securities['Price Ask']
securities['redemption'] = 100
securities['yield'] = securities['Ask Yield to Worst']
securities['maturity_date'] = pd.to_datetime(securities['Maturity Date'], format='%m/%d/%Y')
securities['buy'] = 0
securities = securities.dropna(subset=['rate'])


def buy(end_date: date):
    if end_date.year < plan.index.min():
        return
    t = datetime.combine(end_date, datetime.max.time())  # TODO: remove this - we should just use date columns for maturity_date
    investable = securities[(securities['maturity_date'] <= t) & (securities['maturity_date'] >= t - relativedelta(months=PAYOUT_MONTHS))]
    print(f'Searching for {end_date}')
    security = investable[investable['yield'] == investable['yield'].max()].sort_values(by=['maturity_date']).iloc[0]
    cusip = security['cusip']
    print(f"Found CUSIP = {cusip} for {end_date} with maturity={security['maturity_date']}")
    plan[f'cashflow_{cusip}'] = 0
    for date in reversed(list(rrule.rrule(rrule.MONTHLY, dtstart=security['maturity_date'].replace(day=1), until=end_date))):
        if not date.year in plan.index: # todo rm this
            continue
        cash_for_this_month = plan.loc[date.year, 'target_cashflow'] / date.month
        plan.loc[date.year, 'target_cashflow'] -= cash_for_this_month
        plan.loc[date.year, f'cashflow_{cusip}'] += cash_for_this_month
        print(f"\tCash needed for {date} = {cash_for_this_month}")

    plan['cashflow'] += plan[f'cashflow_{security.cusip}']
    securities.loc[securities['cusip'] == cusip, 'buy'] = plan[f'cashflow_{cusip}'].sum() // security['redemption']
    buy(security['maturity_date'] - relativedelta(days=1))


class STREAMLIT_FORMATS(object):
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
        data=securities[['cusip', 'Coupon', 'price', 'yield', 'maturity_date', 'buy', 'amount']]
        .assign(bought=securities['buy'] > 0)
        .sort_values(by=['bought', 'maturity_date', 'yield'], ascending=False),
        column_config={
            'cusip': st.column_config.TextColumn(label='CUSIP'),
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
                       plan.columns}
    )

### TODO
# 1. Unit tests
# 2. add function types
# 3. logging
####
