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
securities = securities.sort_values(by=['maturity_date'], ascending=False)

buy(securities.iloc[46], qty=10)
print(plan)

st.write(plan)
st.write(securities[['cusip', 'rate', 'price', 'maturity_date', 'qty_bought']])