from datetime import datetime, date
import pandas as pd

def bond_cashflow(rate: float, price: float, maturity: datetime, settlement: datetime = date.today(), redemption: float = 100, cusip: str = None):
    df = pd.DataFrame(data={'year': range(settlement.year, maturity.year + 1)})
    df['cashflow'] = df.apply(lambda row: rate * redemption + (0 if row['year'] < maturity.year else redemption), axis=1)
    df[f'cashflow_{cusip}'] = df.apply(lambda row: rate * redemption + (0 if row['year'] < maturity.year else redemption), axis=1)
    return df

if __name__ == '__main__':
    securities = pd.read_csv('~/Downloads/Fidelity_FixedIncome_SearchResults.csv')
    securities['cusip'] = securities['Cusip'].str.replace('="', '').str.replace('"', '')
    securities['rate'] = securities['Coupon']/100
    securities['price'] = securities['Price Ask']
    securities['maturity_date'] = pd.to_datetime(securities['Maturity Date'], format='%m/%d/%Y')

    security = securities.iloc[467]
    print(bond_cashflow(rate=security['rate'], price=security['price'], maturity=security['maturity_date'], cusip=security['cusip']))
