from datetime import date
from dateutil.relativedelta import relativedelta
from dateutil import rrule
import logging

import numpy as np
import numpy_financial as npf
import pandas as pd
import streamlit as st


class Calculator:
    def __init__(self, fidelity_files):
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
        securities = securities[securities['Attributes'].str.contains('CP')]  # Call Protected bonds only
        self.securities = securities

    def calculate(self, target_monthly_cashflow_by_year, cash_yield=1.0 / 100):
        """
        :param target_monthly_cashflow_by_year: kv of year to monthly cashflow needed for that year
        :param cash_yield: yield if we simply hold cash (e.g. in a savings account)
        :return: 2 dataframes - (plan, securities)
        """
        plan = pd.DataFrame(data=list(target_monthly_cashflow_by_year.items()), columns=['year', 'target_monthly_cashflow'])
        plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12
        plan['cashflow'] = 0
        start_date = date(year=plan['year'].min(), month=1, day=1)
        end_date = date(year=plan['year'].max(), month=12, day=31)
        plan = plan.set_index('year')
        securities = self.securities.copy()

        for year in range(start_date.year, end_date.year + 1):
            securities[f'cashflow_{year}'] = 0.0

        def buy(max_maturity_date: date):  # TODO: add tests
            if max_maturity_date < start_date:  # Done buying
                securities['amount'] = securities['price'] * securities['buy']
                plan['target_cashflow'] = plan['target_monthly_cashflow'] * 12
                return plan, securities

            def cashout_adjusted_yield(row):
                months_in_between = max_maturity_date.month - row['maturity_date'].month + 12 * (max_maturity_date.year - row['maturity_date'].year)
                return 0 if months_in_between <= 0 else row['yield'] / 100 - months_in_between * cash_yield / 12

            securities['cash_adjusted_yield'] = securities.apply(cashout_adjusted_yield, axis=1)
            security = securities[securities['cash_adjusted_yield'] == securities['cash_adjusted_yield'].max()].iloc[0]
            cusip = security.name
            maturity_date = security['maturity_date'].date()

            logging.debug(f"Found CUSIP={cusip} with maturity_date={maturity_date} to cover until end_date={max_maturity_date}")

            def update(dt, amount):
                securities.loc[cusip, f'cashflow_{dt.year}'] += amount
                plan.loc[dt.year, 'cashflow'] += amount
                plan.loc[dt.year, 'target_cashflow'] -= amount
                plan['target_cashflow'] = plan['target_cashflow'].clip(lower=0)  # sometimes dividend payout may exceed our needs by a bit

            cash_needed_at_maturity = 0.0
            for dt in reversed(list(rrule.rrule(rrule.MONTHLY, dtstart=maturity_date.replace(day=1), until=max_maturity_date))):
                if dt.year not in plan.index:
                    continue
                cash_needed_for_this_month = plan.loc[dt.year, 'target_cashflow'] / dt.month
                update(dt=dt, amount=cash_needed_for_this_month)
                cash_needed_at_maturity += cash_needed_for_this_month
                logging.debug(f"\tCash needed for {dt} = {cash_needed_for_this_month}")

            securities.loc[cusip, 'buy'] = cash_needed_at_maturity // security['redemption']

            if security['coupon'] > 0:  # if this pays dividends
                for dt in rrule.rrule(rrule.YEARLY, dtstart=start_date, until=maturity_date):
                    update(dt=dt, amount=security['redemption'] * securities.loc[cusip, 'buy'] * security['coupon'] / 100)

            return buy(max_maturity_date=maturity_date - relativedelta(days=1))  # buy next security with max maturity date 1 day before this one matures

        return buy(max_maturity_date=end_date)

    @staticmethod
    def render(plan, securities):
        total_investment = securities['amount'].sum()
        total_cashflow = plan['cashflow'].sum()
        irr = npf.irr([-total_investment] + plan['cashflow'].tolist())

        col1, col2 = st.columns(2)
        col1.metric(
            label='Investment',
            value=Styles.money().format(total_investment),
            delta='IRR ' + Styles.percent().format(irr * 100)
        )
        col2.metric(
            label='Total Payout',
            value=Styles.money().format(total_cashflow),
            delta='MOIC ' + Styles.num(decimals=2).format(total_cashflow / total_investment) + 'x'
        )

        st.dataframe(
            data=plan
            .replace(0, np.nan)
            .style.format({col: Styles.money() for col in plan.columns}),
            column_config={
                '_index': st.column_config.NumberColumn(format='%d')
            }
        )

        cashflow_cols = list(filter(lambda col: col.startswith('cashflow'), securities.columns))
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
            data=securities[['coupon', 'price', 'yield', 'maturity_date', 'buy', 'amount', 'Description'] + cashflow_cols]
            .rename(columns=str.lower)
            .assign(bought=securities['buy'] > 0)
            .assign(link=securities.index.to_series().map(Styles.security))
            .sort_values(by=['bought', 'maturity_date', 'yield'], ascending=False)
            .style.format(securities_style),
            column_config={
                "link": st.column_config.LinkColumn()
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
        return lambda t: t.strftime("%Y-%m-%d")

    @staticmethod
    def string():
        return lambda d: ' '.join(d.split())

    @staticmethod
    def security(cusip):
        return f'https://oltx.fidelity.com/ftgw/fbc/oftrade/EntrOrder?ORDER_TYPE=F&ORDERSYSTEM=TORD&BROKERAGE_ORDER_ACTION=B&SECURITY_ID={cusip}'


if __name__ == "__main__":
    calculator = Calculator(fidelity_files=[
        '~/Downloads/Treasury_6Nov2023.csv',
        # '~/Downloads/All_7Nov2023.csv'
    ])
    # {year: 30000 + (year - 2025) * 200 for year in range(2025, 2049)}
    plan, securities = calculator.calculate(target_monthly_cashflow_by_year={
        2025: 33000,
        2026: 33500,
        2027: 34000,
        2028: 34500,
        2029: 35000,
        2030: 35500,
        2031: 36000,
        2032: 36500,
        2033: 37000,
        2034: 37500,
        2035: 38000,
        2036: 38500,
        2037: 39000,
        2038: 39500,
        2039: 40000,
        2040: 33000,
        2041: 33500,
        2042: 34000,
        2043: 34500,
        2044: 35000,
        2045: 35500,
        2046: 36000,
        2047: 36500,
        2048: 37000
    })
    Calculator.render(plan=plan, securities=securities)
