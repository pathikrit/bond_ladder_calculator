from unittest import TestCase

from main import Calculator


class TestCalculator(TestCase):
    def test_calculate(self):
        calculator = Calculator(fidelity_files=[
            'tests/fidelity_downloads/Treasury_6Nov2023.csv',
            'tests/fidelity_downloads/All_7Nov2023.csv'
        ])
        result = calculator.calculate(target_monthly_cashflow_by_year={
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
        self.assertEqual(int(result.total_investment), 5708297)
        self.assertEqual(int(result.total_cashflow), 10364759)
