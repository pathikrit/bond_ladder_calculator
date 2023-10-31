from datetime import datetime, date
from dateutil.relativedelta import relativedelta
from statistics import mean

import pandas as pd


def bond_yield(rate: float, price: float, maturity: datetime, frequency, settlement: datetime = date.today(), redemption: float = 100) -> float:
    """
    Similar to excel yield function: Could not find a matching version of package dateutil
    """

    delta = relativedelta(maturity, settlement)
    years = delta.years + delta.months / 12 + delta.days / 365

    return (100 * rate + (redemption - price) / years) / mean([price, redemption])


def bond_cashflow(rate: float, price: float, maturity: datetime, settlement: datetime = date.today(), redemption: float = 100):
    df = pd.DataFrame(data={'year': range(settlement.year, maturity.year + 1)})
    df['cashflow'] = df.apply(lambda row: rate*redemption + (0 if row['year'] < maturity.year else redemption), axis=1)
    return df


if __name__ == '__main__':
    yield_to_worst = bond_yield(
        rate=1.875 / 100,
        price=62.254,
        maturity=datetime(year=2041, month=2, day=15),
        frequency=2
    )
    # assert yield_to_worst == 5.214
    print(yield_to_worst)

    securities = pd.read_csv('~/Downloads/Fidelity_FixedIncome_SearchResults.csv')
    # securities['rate'] = securities['Coupon']/100
    # securities['price'] = securities['Price Ask']
    # securities['maturity_date'] = datetime.strptime(securities['Maturity Date'], '%m/%d/%Y')
    security = securities.iloc[467]
    print(security, bond_cashflow(
        rate=security['Coupon']/100,
        price=security['Price Ask'],
        maturity=datetime.strptime(security['Maturity Date'], '%m/%d/%Y')
    ))

