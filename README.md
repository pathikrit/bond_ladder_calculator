Fixed Income to Annuity
----

* Constructs an [annuity](https://www.investopedia.com/investing/overview-of-annuities/) with custom cashflow out of [bonds](https://fixedincome.fidelity.com/ftgw/fi/FILanding#tbindividual-bonds|treasury)

Running this code:

1. Checkout this repo:
```
git clone git@github.com:pathikrit/fixed_income_annuity.git
cd fixed_income_annuity/
```

2. Download spreadsheets of [fixed income products from Fidelity](https://fixedincome.fidelity.com/ftgw/fi/FILanding#tbindividual-bonds|treasury) that you want to purchase:

![fidelity.png](fidelity.png)

3. Modify first few lines of [main.py](main.py) to specify your target cashflow and path to above downloaded files. 

4. Run: 
```
poetry run streamlit run main.py
```

This will open a browser window with the portfolio construction:
![output.png](output.png)