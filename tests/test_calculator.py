from unittest import TestCase

from main import Calculator


class TestCalculator(TestCase):
    def test_calculate(self):
        calculator = Calculator(fidelity_files=[
            'tests/fidelity_downloads/CD_2023-11-02.csv',
            'tests/fidelity_downloads/TREASURY_2023-11-02.csv'
        ])
        result = calculator.calculate(target_monthly_cashflow_by_year={year: 30000 + 500*i for i, year in enumerate(range(2025, 2050))})
        self.assertEqual(int(result.total_investment), 5542923)
        self.assertEqual(int(result.total_cashflow), 10800387)
