#!/usr/bin/env python3
"""
ESPP Optimizer Dashboard - Streamlit App

A comprehensive Employee Stock Purchase Plan calculator that helps you:
- Visualize ESPP proceeds and gain percentages
- Optimize contribution amounts based on IRS limits
- Track actual purchases with grant dates

Setup:
    pip install streamlit yfinance plotly pandas

Run:
    streamlit run espp_app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any, List
import math

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="ESPP Optimizer",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Custom CSS
# ============================================================
st.markdown("""
<style>
    [data-testid="metric-container"] {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 16px;
    }
    [data-testid="metric-container"] label {
        color: #94a3b8 !important;
    }
    [data-testid="metric-container"] [data-testid="stMetricValue"] {
        color: #10b981 !important;
    }
    h1, h2, h3 { color: #f1f5f9 !important; }
    hr { border-color: #334155; }
</style>
""", unsafe_allow_html=True)

# ============================================================
# Constants
# ============================================================
IRS_LIMIT = 25000  # Annual FMV limit for ESPP

# ============================================================
# Data Fetching Functions
# ============================================================
@st.cache_data(ttl=300)
def fetch_stock_data(symbol: str) -> Optional[Dict[str, Any]]:
    """Fetch current stock data using yfinance."""
    try:
        ticker = yf.Ticker(symbol)
        info = ticker.info
        
        current_price = info.get("currentPrice") or info.get("regularMarketPrice")
        previous_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        
        if not current_price:
            return None
        
        day_change = current_price - previous_close if previous_close else 0
        day_change_pct = (day_change / previous_close * 100) if previous_close else 0
        
        market_cap = info.get("marketCap", 0)
        if market_cap >= 1e12:
            market_cap_fmt = f"${market_cap/1e12:.2f}T"
        elif market_cap >= 1e9:
            market_cap_fmt = f"${market_cap/1e9:.2f}B"
        elif market_cap >= 1e6:
            market_cap_fmt = f"${market_cap/1e6:.2f}M"
        else:
            market_cap_fmt = f"${market_cap:,.0f}"
        
        return {
            "symbol": symbol.upper(),
            "companyName": info.get("longName") or info.get("shortName", symbol.upper()),
            "currentPrice": current_price,
            "previousClose": previous_close,
            "dayChange": round(day_change, 2),
            "dayChangePercent": round(day_change_pct, 2),
            "high52Week": info.get("fiftyTwoWeekHigh"),
            "low52Week": info.get("fiftyTwoWeekLow"),
            "marketCap": market_cap,
            "marketCapFormatted": market_cap_fmt,
        }
    except Exception as e:
        st.error(f"Error fetching data for {symbol}: {str(e)}")
        return None


@st.cache_data(ttl=300)
def fetch_historical_data(symbol: str, period: str = "2y") -> Optional[pd.DataFrame]:
    """Fetch historical price data."""
    try:
        ticker = yf.Ticker(symbol)
        hist = ticker.history(period=period)
        
        if hist.empty:
            return None
        
        hist.index = hist.index.tz_localize(None)
        return hist
    except Exception as e:
        st.error(f"Error fetching historical data: {str(e)}")
        return None


def get_price_at_date(hist: pd.DataFrame, target_date: datetime) -> Optional[float]:
    """Get the closing price closest to a target date."""
    try:
        target_ts = pd.Timestamp(target_date)
        closest_idx = hist.index.get_indexer([target_ts], method='nearest')[0]
        if 0 <= closest_idx < len(hist):
            return round(hist.iloc[closest_idx]['Close'], 2)
        return None
    except:
        return None


def get_actual_date_used(hist: pd.DataFrame, target_date: datetime) -> Optional[datetime]:
    """Get the actual trading date closest to target date."""
    try:
        target_ts = pd.Timestamp(target_date)
        closest_idx = hist.index.get_indexer([target_ts], method='nearest')[0]
        if 0 <= closest_idx < len(hist):
            return hist.index[closest_idx].to_pydatetime()
        return None
    except:
        return None


# ============================================================
# ESPP Calculation Functions
# ============================================================
def calculate_purchase(
    grant_price: float,
    purchase_price: float,
    total_contribution: float,
    discount_rate: float,
    has_lookback: bool
) -> Dict[str, Any]:
    """Calculate purchase details for a single ESPP purchase."""
    
    # Determine effective price with lookback
    if has_lookback:
        effective_price = min(grant_price, purchase_price)
    else:
        effective_price = purchase_price
    
    # Apply discount
    discounted_price = effective_price * (1 - discount_rate / 100)
    
    # Calculate shares (only whole shares can be purchased)
    max_shares = total_contribution / discounted_price
    whole_shares = math.floor(max_shares)
    
    # Calculate actual amounts
    cost_of_shares = whole_shares * discounted_price
    cash_left_over = total_contribution - cost_of_shares
    
    # Calculate proceeds (market value at purchase)
    total_proceeds = whole_shares * purchase_price
    
    # Calculate gains
    gain_dollars = total_proceeds - cost_of_shares
    gain_percent = (gain_dollars / cost_of_shares * 100) if cost_of_shares > 0 else 0
    
    # FMV for IRS calculation (based on grant price)
    fmv_used = whole_shares * grant_price
    
    return {
        "effective_price": round(effective_price, 2),
        "discounted_price": round(discounted_price, 2),
        "max_shares_possible": round(max_shares, 4),
        "whole_shares": whole_shares,
        "cost_of_shares": round(cost_of_shares, 2),
        "cash_left_over": round(cash_left_over, 2),
        "total_proceeds": round(total_proceeds, 2),
        "gain_dollars": round(gain_dollars, 2),
        "gain_percent": round(gain_percent, 2),
        "fmv_used": round(fmv_used, 2),
    }


# ============================================================
# Main App
# ============================================================
def main():
    # Header
    st.title("📈 ESPP Optimizer Dashboard")
    st.markdown("*Maximize your Employee Stock Purchase Plan benefits*")
    
    # ============================================================
    # Sidebar - Configuration
    # ============================================================
    with st.sidebar:
        st.header("⚙️ Configuration")
        
        # Stock Selection
        st.subheader("Stock Selection")
        ticker_input = st.text_input(
            "Company Ticker Symbol",
            value="AAPL",
            placeholder="e.g., AAPL, MSFT, GOOGL"
        ).upper()
        
        fetch_button = st.button("🔍 Fetch Stock Data", type="primary", use_container_width=True)
        
        st.divider()
        
        # ESPP Plan Settings
        st.subheader("ESPP Plan Settings")
        
        discount_rate = st.slider(
            "Discount Rate (%)",
            min_value=0,
            max_value=15,
            value=15,
            help="Most ESPPs offer a 15% discount"
        )
        
        has_lookback = st.checkbox(
            "Lookback Provision",
            value=True,
            help="Purchase at lower of grant or purchase date price"
        )
        
        purchase_period_months = st.selectbox(
            "Purchase Period",
            options=[3, 6],
            index=1,
            format_func=lambda x: f"{x} months"
        )
        
        st.divider()
        
        # Your Financials
        st.subheader("💰 Your Financials")
        
        annual_salary = st.number_input(
            "Annual Salary ($)",
            min_value=10000,
            max_value=10000000,
            value=150000,
            step=5000
        )
        
        contribution_pct = st.slider(
            "Contribution Rate (%)",
            min_value=1,
            max_value=15,
            value=10,
            help="Percentage of salary to contribute"
        )
        
        st.divider()
        
        # IRS Tracking
        st.subheader("🏛️ IRS Limit Tracking")
        
        prior_fmv_used = st.number_input(
            "Prior FMV Used This Year ($)",
            min_value=0.0,
            max_value=25000.0,
            value=0.0,
            step=100.0,
            help="FMV already used from previous purchases this calendar year"
        )
    
    # ============================================================
    # Main Content
    # ============================================================
    
    # Initialize session state
    if 'stock_data' not in st.session_state:
        st.session_state.stock_data = None
    if 'hist_data' not in st.session_state:
        st.session_state.hist_data = None
    if 'ticker' not in st.session_state:
        st.session_state.ticker = None
    
    # Fetch data on button click or ticker change
    if fetch_button or st.session_state.ticker != ticker_input:
        with st.spinner(f"Fetching data for {ticker_input}..."):
            st.session_state.stock_data = fetch_stock_data(ticker_input)
            st.session_state.hist_data = fetch_historical_data(ticker_input)
            st.session_state.ticker = ticker_input
    
    stock_data = st.session_state.stock_data
    hist_data = st.session_state.hist_data
    
    if stock_data is None:
        st.warning("⚠️ Could not fetch stock data. Please check the ticker symbol and try again.")
        st.info("💡 Try common tickers like: AAPL, MSFT, GOOGL, AMZN, META, NVDA")
        return
    
    # ============================================================
    # Stock Info Card
    # ============================================================
    st.header(f"🏢 {stock_data['companyName']} ({stock_data['symbol']})")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        change_color = "normal" if stock_data['dayChangePercent'] >= 0 else "inverse"
        st.metric(
            "Current Price",
            f"${stock_data['currentPrice']:,.2f}",
            f"{stock_data['dayChangePercent']:+.2f}%",
            delta_color=change_color
        )
    
    with col2:
        st.metric("52-Week High", f"${stock_data['high52Week']:,.2f}")
    
    with col3:
        st.metric("52-Week Low", f"${stock_data['low52Week']:,.2f}")
    
    with col4:
        st.metric("Market Cap", stock_data['marketCapFormatted'])
    
    st.divider()
    
    # ============================================================
    # Current Offering Period
    # ============================================================
    st.header("📅 Current Offering Period")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Grant date input
        default_grant = datetime.now() - timedelta(days=90)  # Default to ~3 months ago
        grant_date = st.date_input(
            "Grant Date (Offering Start)",
            value=default_grant,
            max_value=datetime.now().date(),
            help="The date your ESPP offering period started"
        )
    
    with col2:
        # Calculate and show purchase date
        purchase_date = datetime.combine(grant_date, datetime.min.time()) + relativedelta(months=purchase_period_months)
        st.date_input(
            "Purchase Date",
            value=purchase_date.date(),
            disabled=True,
            help="Calculated based on purchase period"
        )
    
    # Fetch prices for grant and purchase dates
    if hist_data is not None:
        grant_datetime = datetime.combine(grant_date, datetime.min.time())
        
        grant_price = get_price_at_date(hist_data, grant_datetime)
        actual_grant_date = get_actual_date_used(hist_data, grant_datetime)
        
        # For purchase price: use current price if purchase date is in future, otherwise fetch historical
        if purchase_date.date() >= datetime.now().date():
            purchase_price = stock_data['currentPrice']
            purchase_date_label = "Today (Current)"
        else:
            purchase_price = get_price_at_date(hist_data, purchase_date)
            purchase_date_label = purchase_date.strftime("%Y-%m-%d")
        
        if grant_price is None:
            st.error("Could not fetch grant date price. The date may be too far in the past.")
            return
        
        # Calculate contribution for the period
        periods_per_year = 12 / purchase_period_months
        contribution_per_period = (annual_salary * contribution_pct / 100) / periods_per_year
        
        # Display price info
        st.markdown("---")
        
        price_col1, price_col2, price_col3, price_col4 = st.columns(4)
        
        with price_col1:
            st.metric(
                f"Grant Price ({actual_grant_date.strftime('%Y-%m-%d') if actual_grant_date else 'N/A'})",
                f"${grant_price:,.2f}"
            )
        
        with price_col2:
            st.metric(
                f"Purchase Price ({purchase_date_label})",
                f"${purchase_price:,.2f}"
            )
        
        with price_col3:
            price_change = ((purchase_price - grant_price) / grant_price) * 100
            st.metric(
                "Price Change",
                f"{price_change:+.2f}%",
                delta_color="normal" if price_change >= 0 else "inverse"
            )
        
        with price_col4:
            st.metric(
                "Your Contribution",
                f"${contribution_per_period:,.2f}"
            )
        
        st.divider()
        
        # ============================================================
        # Purchase Details
        # ============================================================
        st.header("💰 Purchase Details")
        
        # Calculate purchase
        purchase = calculate_purchase(
            grant_price=grant_price,
            purchase_price=purchase_price,
            total_contribution=contribution_per_period,
            discount_rate=discount_rate,
            has_lookback=has_lookback
        )
        
        # Show lookback benefit
        if has_lookback:
            lookback_price = "Grant" if grant_price <= purchase_price else "Purchase"
            st.info(f"🔄 **Lookback Applied:** Using {lookback_price} price (${purchase['effective_price']:.2f}) as it's lower")
        
        # Main metrics
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Your Purchase Price (after discount)",
                f"${purchase['discounted_price']:,.2f}",
                f"{discount_rate}% off ${purchase['effective_price']:.2f}"
            )
        
        with col2:
            st.metric(
                "Shares Purchased",
                f"{purchase['whole_shares']:,}",
                f"Max possible: {purchase['max_shares_possible']:.2f}"
            )
        
        with col3:
            st.metric(
                "Cash Left Over",
                f"${purchase['cash_left_over']:,.2f}",
                help="Returned to you (fractional shares not purchased)"
            )
        
        st.markdown("---")
        
        # Financial summary
        fin_col1, fin_col2, fin_col3, fin_col4 = st.columns(4)
        
        with fin_col1:
            st.metric(
                "Cost of Shares",
                f"${purchase['cost_of_shares']:,.2f}",
                help="What you actually paid"
            )
        
        with fin_col2:
            st.metric(
                "Market Value (Proceeds)",
                f"${purchase['total_proceeds']:,.2f}",
                help="Value at purchase price"
            )
        
        with fin_col3:
            st.metric(
                "💵 Gain ($)",
                f"${purchase['gain_dollars']:,.2f}",
                delta_color="normal"
            )
        
        with fin_col4:
            st.metric(
                "📈 Gain (%)",
                f"{purchase['gain_percent']:.2f}%",
                delta_color="normal"
            )
        
        st.divider()
        
        # ============================================================
        # IRS Limit Analysis
        # ============================================================
        st.header("🏛️ IRS Limit Analysis")
        
        # Current year tracking
        current_year = datetime.now().year
        fmv_this_purchase = purchase['fmv_used']
        total_fmv_used = prior_fmv_used + fmv_this_purchase
        remaining_fmv = max(0, IRS_LIMIT - total_fmv_used)
        
        irs_col1, irs_col2 = st.columns([2, 1])
        
        with irs_col1:
            st.subheader(f"📊 {current_year} IRS Limit Usage")
            
            # Show breakdown
            st.markdown(f"""
            | Description | Amount |
            |-------------|--------|
            | Prior FMV Used | ${prior_fmv_used:,.2f} |
            | This Purchase FMV | ${fmv_this_purchase:,.2f} |
            | **Total FMV Used** | **${total_fmv_used:,.2f}** |
            | **Remaining Limit** | **${remaining_fmv:,.2f}** |
            """)
            
            # Progress bar
            usage_pct = min((total_fmv_used / IRS_LIMIT) * 100, 100)
            st.progress(min(usage_pct / 100, 1.0))
            fmv_display = f"{total_fmv_used:,.2f}"
            st.caption(f"IRS Limit Usage: {usage_pct:.1f}% (\\${fmv_display} of \\$25,000)")
            
            if total_fmv_used > IRS_LIMIT:
                st.error(f"⚠️ **Over IRS Limit by ${total_fmv_used - IRS_LIMIT:,.2f}!** You may need to reduce contributions.")
            elif remaining_fmv < 5000:
                st.warning(f"⚠️ **Approaching IRS Limit!** Only ${remaining_fmv:,.2f} FMV remaining for {current_year}.")
            else:
                st.success(f"✅ **Within IRS Limits.** ${remaining_fmv:,.2f} FMV remaining for {current_year}.")
        
        with irs_col2:
            st.info(f"""
            **IRS ESPP Rules:**
            - Max FMV: ${IRS_LIMIT:,}/year
            - Based on **grant date** price
            - FMV = Shares × Grant Price
            - Resets each calendar year
            """)
        
        st.markdown("---")
        
        # ============================================================
        # Next Offering Period Recommendation
        # ============================================================
        st.subheader("🔮 Next Offering Period Recommendation")
        
        # Estimate next offering
        next_grant_date = purchase_date
        next_purchase_date = next_grant_date + relativedelta(months=purchase_period_months)
        
        # Check if next period crosses into new year
        crosses_new_year = next_purchase_date.year > current_year
        
        if crosses_new_year:
            # New year = fresh IRS limit
            available_fmv = IRS_LIMIT
            st.info(f"📅 Next purchase ({next_purchase_date.strftime('%b %Y')}) is in {next_purchase_date.year} - fresh ${IRS_LIMIT:,} IRS limit!")
        else:
            available_fmv = remaining_fmv
        
        if available_fmv <= 0:
            st.warning("⚠️ No IRS limit remaining for this calendar year. Consider pausing contributions until next year.")
            recommended_pct = 0
        else:
            # Estimate max shares based on current price (as proxy for future grant price)
            estimated_grant_price = stock_data['currentPrice']
            max_shares_by_irs = available_fmv / estimated_grant_price
            
            # Estimate discounted price
            estimated_discounted = estimated_grant_price * (1 - discount_rate / 100)
            
            # Max contribution that stays within IRS limit
            max_contribution_by_irs = max_shares_by_irs * estimated_discounted
            
            # Convert to percentage of salary
            annual_contribution = annual_salary * (contribution_pct / 100)
            contribution_per_period_current = annual_contribution / (12 / purchase_period_months)
            
            # Recommended percentage
            max_annual_contribution = max_contribution_by_irs * (12 / purchase_period_months)
            recommended_pct = min(15, (max_annual_contribution / annual_salary) * 100)
            
            rec_col1, rec_col2, rec_col3 = st.columns(3)
            
            with rec_col1:
                st.metric(
                    "Available FMV",
                    f"${available_fmv:,.2f}"
                )
            
            with rec_col2:
                st.metric(
                    "Est. Max Contribution (Period)",
                    f"${max_contribution_by_irs:,.2f}"
                )
            
            with rec_col3:
                current_vs_max = "✅ OK" if contribution_per_period_current <= max_contribution_by_irs else "⚠️ Too High"
                st.metric(
                    "Recommended Contribution %",
                    f"{recommended_pct:.1f}%",
                    f"Current: {contribution_pct}% {current_vs_max}"
                )
            
            if contribution_pct > recommended_pct:
                st.warning(f"""
                📉 **Consider reducing your contribution rate** from {contribution_pct}% to {recommended_pct:.1f}% 
                for the next offering period to stay within IRS limits.
                """)
            else:
                st.success(f"""
                👍 **Your current contribution rate of {contribution_pct}%** should keep you within IRS limits 
                for the next offering period (assuming stock price stays around ${estimated_grant_price:.2f}).
                """)
        
        st.divider()
        
        # ============================================================
        # Historical Chart
        # ============================================================
        st.header("📊 Stock Performance")
        
        fig = go.Figure()
        
        fig.add_trace(go.Candlestick(
            x=hist_data.index,
            open=hist_data['Open'],
            high=hist_data['High'],
            low=hist_data['Low'],
            close=hist_data['Close'],
            name="Price"
        ))
        
        # Mark grant date with a shape instead of vline
        fig.add_shape(
            type="line",
            x0=grant_datetime,
            x1=grant_datetime,
            y0=0,
            y1=1,
            yref="paper",
            line=dict(color="#f59e0b", width=2, dash="dash"),
        )
        fig.add_annotation(
            x=grant_datetime,
            y=1.05,
            yref="paper",
            text=f"Grant: ${grant_price:.2f}",
            showarrow=False,
            font=dict(color="#f59e0b", size=12)
        )
        
        # Mark purchase date if in past
        if purchase_date.date() < datetime.now().date():
            fig.add_shape(
                type="line",
                x0=purchase_date,
                x1=purchase_date,
                y0=0,
                y1=1,
                yref="paper",
                line=dict(color="#10b981", width=2, dash="dash"),
            )
            fig.add_annotation(
                x=purchase_date,
                y=1.05,
                yref="paper",
                text=f"Purchase: ${purchase_price:.2f}",
                showarrow=False,
                font=dict(color="#10b981", size=12)
            )
        
        fig.update_layout(
            title=f"{stock_data['symbol']} Stock Price with ESPP Dates",
            template="plotly_dark",
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            height=450,
            yaxis_title="Price ($)",
            xaxis_rangeslider_visible=False
        )
        
        st.plotly_chart(fig, use_container_width=True)
    
    # ============================================================
    # Footer
    # ============================================================
    st.divider()
    
    st.caption("""
    ⚠️ **Disclaimer:** This calculator is for educational purposes only. 
    Consult a tax professional for personalized advice. ESPP rules vary by company. 
    The $25,000 IRS limit is based on Fair Market Value at the grant/offering date.
    """)
    
    st.caption(f"Data provided by Yahoo Finance • Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()
