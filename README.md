[Bond Ladder](https://www.investopedia.com/investing/build-bond-ladder-boost-returns/) Calculator [![Tests](https://github.com/pathikrit/bond_ladder_calculator/actions/workflows/test.yml/badge.svg)](https://github.com/pathikrit/bond_ladder_calculator/actions/workflows/test.yml)
----

### Running locally

1. Prerequisites: You would need `git`, [`poetry`](https://python-poetry.org/docs/#installation) and [`streamlit`](https://docs.streamlit.io/library/get-started/installation)
2. Checkout + Installtion:
    ```shell
    git clone git@github.com:pathikrit/bond_ladder_calculator.git
    cd bond_ladder_calculator/
    poetry install --with dev
    ```
3. Download spreadsheet(s) of [available bonds from Fidelity](https://fixedincome.fidelity.com/ftgw/fi/FILanding#tbindividual-bonds|treasury) that you want:
![fidelity.png](fidelity.png)
You can directly bookmark [these 2 links from my Chrome extension](https://github.com/pathikrit/chrome_ai/blob/c5cb23f3392d895825ef4d988d3b602c38b9d65c/index.js#L117-L118) that automates this.
4. Run: 
    ```shell
    poetry run streamlit run main.py
    ```
    This will open a browser window: ![output.png](output.png)
5. You can use the above streamlit app to specify your Fidelity export files and specify target cashflow (see example in [tests](tests/test_calculator.py)) 
