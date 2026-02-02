# ESPP Optimizer Dashboard

A comprehensive Employee Stock Purchase Plan (ESPP) calculator built with Streamlit.

## Features

- 📈 **Live Stock Data** - Fetches real-time prices from Yahoo Finance
- 📅 **Grant Date Tracking** - Input your actual offering start date
- 💰 **Purchase Calculations** - Shows shares purchased, proceeds, and cash left over
- 🏛️ **IRS Limit Analysis** - Track your $25,000 annual FMV limit
- 🔮 **Next Offering Recommendations** - Optimize contribution % for future periods
- 📊 **Interactive Charts** - Visualize stock performance with ESPP dates marked

## How to Use

1. Enter your company's stock ticker (e.g., AAPL, MSFT, GOOGL)
2. Set your ESPP plan details (discount rate, lookback, purchase period)
3. Enter your salary and contribution percentage
4. Select your grant date to see purchase calculations
5. Track IRS limits and get recommendations for next offering

## Run Locally

```bash
pip install -r requirements.txt
streamlit run espp_app.py
```

## Disclaimer

This calculator is for educational purposes only. Consult a tax professional for personalized advice. ESPP rules vary by company.
