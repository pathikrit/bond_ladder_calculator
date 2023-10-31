from datetime import datetime, date
from dateutil.relativedelta import relativedelta

def bond_yield(rate: float, price: float, maturity: datetime, frequency=1, settlement: datetime=date.today(), redemption: float=100) -> float:
    """
    Similar to excel yield function: Could not find a matching version of package dateutil
    """

    delta = relativedelta(maturity, settlement)
    years = delta.years + delta.months/12 + delta.days/365
    ytw = (rate*redemption + (100 - price) / years*frequency) / ((100 + price) / 2)
    return ytw

if __name__ == '__main__':
    yield_to_worst = bond_yield(
        rate=1.875/100,
        price=62.254,
        maturity=datetime(year=2041, month=2, day=15),
        frequency=2
    )
    # assert yield_to_worst == 5.214
    print(yield_to_worst)




