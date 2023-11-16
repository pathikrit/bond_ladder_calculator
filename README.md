Fixed Income to Annuity [![Tests](https://github.com/pathikrit/fixed_income_annuity/actions/workflows/test.yml/badge.svg)](https://github.com/pathikrit/fixed_income_annuity/actions/workflows/test.yml)
----

* Constructs an [annuity](https://www.investopedia.com/investing/overview-of-annuities/) with custom cashflow out of [bonds]([https://fixedincome.fidelity.com/ftgw/fi/FILanding#tbindividual-bonds|treasury](https://www.investopedia.com/financial-edge/0312/the-basics-of-bonds.aspx))

Running this code:

0. Prerequisites: You would need `git`, [`poetry`](https://python-poetry.org/docs/#installation) and [`streamlit`](https://docs.streamlit.io/library/get-started/installation)

1. Checkout this repo:
```
git clone git@github.com:pathikrit/fixed_income_annuity.git
cd fixed_income_annuity/
```

2. Download spreadsheet(s) of [fixed income products from Fidelity](https://fixedincome.fidelity.com/ftgw/fi/FILanding#tbindividual-bonds|treasury) that you want:

![fidelity.png](fidelity.png)

You can directly bookmark [these 2 links from my Chrome extension](https://github.com/pathikrit/chrome_ai/blob/c5cb23f3392d895825ef4d988d3b602c38b9d65c/index.js#L117-L118) that automates this.

3. Modify last few lines of [main.py](main.py#L200) to specify your target cashflow and path to above downloaded files (see example in [tests](tests/test_calculator.py)) 

4. Run: 
```
poetry run streamlit run main.py
```

This will open a browser window with the portfolio construction:
![output.png](output.png)
