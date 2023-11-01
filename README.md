Fixed Income to Annuity
----

* Constructs an [annuity](https://www.investopedia.com/investing/overview-of-annuities/) with custom cashflow out of [fixed income, bonds and CDs](https://fixedincome.fidelity.com/ftgw/fi/FILanding)

Running this code:

1. Checkout this repo:
```
git clone
cd 
```

2. Download spreadsheets of [fixed income products from Fidelity](https://fixedincome.fidelity.com/ftgw/fi/FILanding#tbindividual-bonds|treasury) that you want to purchase:

![fidelity.png](fidelity.png)

3. Modify first few lines of [main.py](main.py) to specify your target cashflow and path to above downloaded files. 

4. Run: 
```
poetry run streamlit run main.py
```