import pandas as pd
import streamlit as st

#### This is the input to this program ####

TARGET_CASHFLOW = [(year, 48000 - (2039 - year) * 1000 if year < 2040 else 51000 - (2048 - year) * 1000) for year in range(2025, 2049)]
FIDELITY_FIXED_INCOME_SEARCH_RESULTS = '~/Downloads/Fidelity_FixedIncome_SearchResults.csv'

###########################################

plan = pd.DataFrame(data=TARGET_CASHFLOW, columns=['year', 'target_monthly_cashflow'])
plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12
plan['cashflow'] = 0
plan.set_index('year')

def buy(security, qty):
    plan[f'cashflow_{security.cusip}'] = plan.apply(lambda row: 0 if row.year > security.maturity_date.year else ((row.year == security.maturity_date.year) + security.rate) * security.redemption * qty, axis=1)
    plan['cashflow'] += plan[f'cashflow_{security.cusip}']
    # security['qty_bought'] = qty


securities = pd.read_csv(FIDELITY_FIXED_INCOME_SEARCH_RESULTS)
securities['cusip'] = securities['Cusip'].str.replace('="', '').str.replace('"', '')
securities.set_index('cusip')
securities['rate'] = securities['Coupon'] / 100
securities['price'] = securities['Price Ask']
securities['redemption'] = 100
securities['maturity_date'] = pd.to_datetime(securities['Maturity Date'], format='%m/%d/%Y')
securities['qty_bought'] = 0
securities = securities.dropna(subset=['rate'])
#securities = securities.sort_values(by=['maturity_date'], ascending=False)

buy(securities.iloc[467], qty=10)

class STREAMLIT_FORMATS(object):
    CURRENCY = '$%.0f'
    PERCENT = '%.2f%%'
    NUMBER = '%d'

st.dataframe(
    data=securities[['cusip', 'Coupon', 'price', 'Ask Yield to Worst', 'maturity_date', 'qty_bought']],
    column_config={
        'cusip': st.column_config.TextColumn(label='CUSIP'),
        'Coupon': st.column_config.NumberColumn(format=STREAMLIT_FORMATS.PERCENT),
        'maturity_date': st.column_config.DateColumn(label='Maturity', format='YYYY-MM-DD'),
        'price': st.column_config.NumberColumn(label='Price', format=STREAMLIT_FORMATS.CURRENCY),
        'Ask Yield to Worst': st.column_config.NumberColumn(label='Yield', format=STREAMLIT_FORMATS.PERCENT),
        'qty_bought': st.column_config.NumberColumn(label='Buy', format=STREAMLIT_FORMATS.NUMBER),
    }
)

st.dataframe(
    data=plan,
    column_config={col: st.column_config.NumberColumn(format=STREAMLIT_FORMATS.CURRENCY if 'cashflow' in col else STREAMLIT_FORMATS.NUMBER) for col in plan.columns}
)

### TODO
# 1. Read from dir
# 2. Print total amount needed to buy using st.metric
####
