from dataclasses import dataclass
from datetime import date
from typing import List, Dict

import logging
from dateutil.relativedelta import relativedelta
from dateutil import rrule

import numpy as np
import numpy_financial as npf
import pandas as pd
import streamlit as st


@dataclass
class Result:
    securities: pd.DataFrame
    plan: pd.DataFrame

    @property
    def total_investment(self) -> float:
        return self.securities['amount'].sum()

    @property
    def total_cashflow(self) -> float:
        return self.plan['actual_cashflow'].sum()

    @property
    def irr(self) -> float:
        return npf.irr([-self.total_investment] + self.plan['actual_cashflow'].tolist())


class Calculator:
    def __init__(self, fidelity_files: List[str]):
        securities = pd.concat([pd.read_csv(file) for file in fidelity_files])
        securities = securities.dropna(subset=['Cusip', 'Attributes'])
        securities['cusip'] = securities['Cusip'].str.replace('="', '').str.replace('"', '')
        securities = securities.set_index('cusip')
        securities['coupon'] = pd.to_numeric(securities['Coupon'], errors='coerce').replace(np.nan, 0)
        securities['price'] = securities['Price Ask']
        securities['redemption'] = 100
        securities['yield'] = securities['Ask Yield to Worst']
        securities['maturity_date'] = pd.to_datetime(securities['Maturity Date'], format='%m/%d/%Y')
        securities['buy'] = 0
        securities['cashflow'] = 0.0
        securities = securities[securities['Attributes'].str.contains('CP')]  # Call Protected bonds only
        self.securities = securities

    def calculate(self, target_monthly_cashflow_by_year: Dict[int, float], cash_yield: float = 1.0 / 100) -> Result:
        """
        :param target_monthly_cashflow_by_year: kv of year to monthly cashflow needed for that year
        :param cash_yield: yield if we simply hold cash (e.g. in a savings account)
        :return: 2 dataframes - (plan, securities)
        """
        plan = pd.DataFrame(data=list(target_monthly_cashflow_by_year.items()), columns=['year', 'target_monthly_cashflow'])
        plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12 * 1.0
        plan['actual_cashflow'] = 0.0
        start_date = date(year=plan['year'].min(), month=1, day=1)
        end_date = date(year=plan['year'].max(), month=12, day=31)
        plan = plan.set_index('year')
        securities = self.securities.copy()

        for year in range(start_date.year, end_date.year + 1):
            securities[f'cashflow_{year}'] = 0.0

        def buy(max_maturity_date: date) -> Result:
            if max_maturity_date < start_date:  # Done buying
                securities['amount'] = securities['price'] * securities['buy']
                plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12
                return Result(plan=plan, securities=securities)

            def cashout_adjusted_yield(row) -> float:
                months_in_between = max_maturity_date.month - row['maturity_date'].month + 12 * (max_maturity_date.year - row['maturity_date'].year)
                return 0 if months_in_between <= 0 else row['yield'] / 100 - months_in_between * cash_yield / 12

            securities['cash_adjusted_yield'] = securities.apply(cashout_adjusted_yield, axis=1)
            security = securities[securities['cash_adjusted_yield'] == securities['cash_adjusted_yield'].max()].iloc[0]
            cusip = security.name
            maturity_date = security['maturity_date'].date()

            logging.debug('Found CUSIP=%s with maturity_date=%s to cover until end_date=%s', cusip, maturity_date, max_maturity_date)

            def update(dt: date, amount: float, prefix: str) -> None:
                logging.debug('\t%s for %s = %f', prefix, dt, amount)
                securities.loc[cusip, 'cashflow'] += amount
                securities.loc[cusip, f'cashflow_{dt.year}'] += amount
                plan.loc[dt.year, 'actual_cashflow'] += amount
                plan.loc[dt.year, 'target_cashflow'] -= amount
                plan['target_cashflow'] = plan['target_cashflow'].clip(lower=0)  # sometimes dividend payout may exceed our needs by a bit

            for dt in reversed(list(rrule.rrule(rrule.MONTHLY, dtstart=maturity_date.replace(day=1), until=max_maturity_date))):
                if dt.year in plan.index:
                    update(dt=dt, amount=plan.loc[dt.year, 'target_cashflow'] / dt.month, prefix='Cash needed')

            securities.loc[cusip, 'buy'] = securities.loc[cusip, 'cashflow'] // security['redemption']

            if security['coupon'] > 0:  # if this pays dividends
                for dt in rrule.rrule(rrule.YEARLY, dtstart=start_date, until=maturity_date):
                    update(
                        dt=dt,
                        amount=security['redemption'] * securities.loc[cusip, 'buy'] * security['coupon'] / 100,
                        prefix='Dividend'
                    )

            # buy next security with max maturity date 1 day before this one matures
            return buy(max_maturity_date=maturity_date - relativedelta(days=1))

        return buy(max_maturity_date=end_date)

    @staticmethod
    def render(result: Result) -> None:
        col1, col2 = st.columns(2)
        col1.metric(
            label='Investment',
            value=Styles.money().format(result.total_investment),
            delta='IRR ' + Styles.percent().format(result.irr * 100)
        )
        col2.metric(
            label='Total Payout',
            value=Styles.money().format(result.total_cashflow),
            delta='MOIC ' + Styles.num(decimals=2).format(result.total_cashflow / result.total_investment) + 'x'
        )

        st.dataframe(
            data=result.plan
            .replace(0, np.nan)
            .style.format({col: Styles.money() for col in result.plan.columns}),
            column_config={
                '_index': st.column_config.NumberColumn(format='%d')
            }
        )

        cashflow_cols = list(filter(lambda col: col.startswith('cashflow'), result.securities.columns))
        securities_style = {
            'coupon': Styles.percent(),
            'price': Styles.money(2),
            'yield': Styles.percent(),
            'maturity_date': Styles.date(),
            'buy': Styles.num(),
            'amount': Styles.money(),
            'description': Styles.string()
        }
        for col in cashflow_cols:
            securities_style[col] = Styles.money()
        st.dataframe(
            data=result.securities[['coupon', 'price', 'yield', 'maturity_date', 'buy', 'amount', 'Description'] + cashflow_cols]
            .rename(columns=str.lower)
            .assign(bought=result.securities['buy'] > 0)
            .assign(link=result.securities.index.to_series().map(Styles.security))
            .sort_values(by=['bought', 'maturity_date', 'yield'], ascending=False)
            .style.format(securities_style),
            column_config={
                'link': st.column_config.LinkColumn()
            },
        )


class Styles:
    @staticmethod
    def money(decimals=0):
        return f'$ {{:,.{decimals}f}}'

    @staticmethod
    def percent(decimals=2):
        return f'{{:,.{decimals}f}}%'

    @staticmethod
    def num(decimals=0):
        return f'{{:,.{decimals}f}}'

    @staticmethod
    def date():
        return lambda t: t.strftime('%Y-%m-%d')

    @staticmethod
    def string():
        return lambda d: ' '.join(d.split())

    @staticmethod
    def security(cusip: str):
        return f'https://oltx.fidelity.com/ftgw/fbc/oftrade/EntrOrder?ORDER_TYPE=F&ORDERSYSTEM=TORD&BROKERAGE_ORDER_ACTION=B&SECURITY_ID={cusip}'


def main():
    calculator = Calculator(fidelity_files=[
        '~/Downloads/Treasury_6Nov2023.csv',
        '~/Downloads/All_7Nov2023.csv'
    ])
    Calculator.render(calculator.calculate(
        target_monthly_cashflow_by_year={year: 30000 + (year - 2025) * 250 for year in range(2025, 2050)}
    ))


if __name__ == '__main__':
    main()
