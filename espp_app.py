#!/usr/bin/env python3
"""
ESPP Optimizer Dashboard - Streamlit App v2

Clean, minimal design inspired by Bear Blog with 80s typography.
Features waterfall chart for proceeds and lookback highlighting.

Setup:
    pip install streamlit yfinance plotly pandas python-dateutil

Run:
    streamlit run espp_app.py
"""

import streamlit as st
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from typing import Optional, Dict, Any
import math

# ============================================================
# Page Configuration
# ============================================================
st.set_page_config(
    page_title="ESPP Optimizer",
    page_icon="📈",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ============================================================
# Custom CSS - Clean Minimal Design
# ============================================================
def get_css(dark_mode: bool) -> str:
    if dark_mode:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=VT323&family=Space+Mono:wght@400;700&display=swap');
            
            :root {
                --bg: #1a1a1a;
                --card: #252525;
                --text: #e0e0e0;
                --text-muted: #888888;
                --accent: #39ff14;
                --accent-alt: #4ecdc4;
                --border: #333333;
                --bar-base: #444444;
            }
            
            .stApp {
                background-color: var(--bg);
            }
            
            .main-header {
                font-family: 'VT323', monospace;
                font-size: 36px;
                letter-spacing: 2px;
                color: var(--text);
                margin-bottom: 4px;
            }
            
            .sub-header {
                color: var(--text-muted);
                font-size: 14px;
                margin-bottom: 24px;
            }
            
            .card {
                background: var(--card);
                border: 2px solid var(--border);
                padding: 20px;
                margin-bottom: 16px;
                transition: all 0.3s ease;
            }
            
            .card:hover {
                border-color: var(--accent);
            }
            
            .card-highlight {
                border: 2px solid var(--accent-alt) !important;
                position: relative;
            }
            
            .lookback-badge {
                background: var(--accent-alt);
                color: #1a1a1a;
                font-size: 10px;
                padding: 2px 8px;
                letter-spacing: 1px;
                font-family: 'Space Mono', monospace;
                position: absolute;
                top: -10px;
                left: 12px;
            }
            
            .big-number {
                font-family: 'Space Mono', monospace;
                font-size: 48px;
                font-weight: 700;
                line-height: 1;
                letter-spacing: -2px;
                color: var(--text);
            }
            
            .medium-number {
                font-family: 'Space Mono', monospace;
                font-size: 28px;
                font-weight: 700;
                color: var(--text);
            }
            
            .small-number {
                font-family: 'Space Mono', monospace;
                font-size: 18px;
                font-weight: 700;
            }
            
            .label {
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: var(--text-muted);
                margin-bottom: 4px;
            }
            
            .highlight {
                color: var(--accent) !important;
            }
            
            .highlight-alt {
                color: var(--accent-alt) !important;
            }
            
            .divider {
                border: none;
                border-top: 1px dashed var(--border);
                margin: 16px 0;
            }
            
            .inline-stat {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px dotted var(--border);
                color: var(--text);
            }
            
            .inline-stat:last-child {
                border-bottom: none;
            }
            
            .tag {
                display: inline-block;
                padding: 4px 12px;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                border: 1px solid currentColor;
                color: var(--accent-alt);
            }
            
            .progress-container {
                height: 8px;
                background: var(--border);
                overflow: hidden;
                margin-top: 8px;
            }
            
            .progress-fill {
                height: 100%;
                background: var(--accent);
            }
            
            .footer {
                text-align: center;
                color: var(--text-muted);
                font-size: 12px;
                margin-top: 32px;
                padding-top: 16px;
                border-top: 1px solid var(--border);
            }
            
            .footer-brand {
                font-family: 'VT323', monospace;
                font-size: 16px;
                margin-top: 8px;
            }
            
            /* Hide Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display: none;}
            
            /* Style inputs */
            .stTextInput input, .stNumberInput input, .stSelectbox select {
                background-color: var(--card) !important;
                color: var(--text) !important;
                border: 2px solid var(--border) !important;
                font-family: 'Space Mono', monospace !important;
            }
            
            .stDateInput input {
                background-color: var(--card) !important;
                color: var(--text) !important;
                border: 2px solid var(--border) !important;
            }
        </style>
        """
    else:
        return """
        <style>
            @import url('https://fonts.googleapis.com/css2?family=VT323&family=Space+Mono:wght@400;700&display=swap');
            
            :root {
                --bg: #fafafa;
                --card: #ffffff;
                --text: #2d2d2d;
                --text-muted: #666666;
                --accent: #32cd32;
                --accent-alt: #2a9d8f;
                --border: #e0e0e0;
                --bar-base: #e0e0e0;
            }
            
            .stApp {
                background-color: var(--bg);
            }
            
            .main-header {
                font-family: 'VT323', monospace;
                font-size: 36px;
                letter-spacing: 2px;
                color: var(--text);
                margin-bottom: 4px;
            }
            
            .sub-header {
                color: var(--text-muted);
                font-size: 14px;
                margin-bottom: 24px;
            }
            
            .card {
                background: var(--card);
                border: 2px solid var(--border);
                padding: 20px;
                margin-bottom: 16px;
                transition: all 0.3s ease;
            }
            
            .card:hover {
                border-color: var(--accent);
            }
            
            .card-highlight {
                border: 2px solid var(--accent-alt) !important;
                position: relative;
            }
            
            .lookback-badge {
                background: var(--accent-alt);
                color: #ffffff;
                font-size: 10px;
                padding: 2px 8px;
                letter-spacing: 1px;
                font-family: 'Space Mono', monospace;
                position: absolute;
                top: -10px;
                left: 12px;
            }
            
            .big-number {
                font-family: 'Space Mono', monospace;
                font-size: 48px;
                font-weight: 700;
                line-height: 1;
                letter-spacing: -2px;
                color: var(--text);
            }
            
            .medium-number {
                font-family: 'Space Mono', monospace;
                font-size: 28px;
                font-weight: 700;
                color: var(--text);
            }
            
            .small-number {
                font-family: 'Space Mono', monospace;
                font-size: 18px;
                font-weight: 700;
            }
            
            .label {
                font-size: 14px;
                text-transform: uppercase;
                letter-spacing: 2px;
                color: var(--text-muted);
                margin-bottom: 4px;
            }
            
            .highlight {
                color: var(--accent) !important;
            }
            
            .highlight-alt {
                color: var(--accent-alt) !important;
            }
            
            .divider {
                border: none;
                border-top: 1px dashed var(--border);
                margin: 16px 0;
            }
            
            .inline-stat {
                display: flex;
                justify-content: space-between;
                padding: 8px 0;
                border-bottom: 1px dotted var(--border);
                color: var(--text);
            }
            
            .inline-stat:last-child {
                border-bottom: none;
            }
            
            .tag {
                display: inline-block;
                padding: 4px 12px;
                font-size: 12px;
                text-transform: uppercase;
                letter-spacing: 1px;
                border: 1px solid currentColor;
                color: var(--accent-alt);
            }
            
            .progress-container {
                height: 8px;
                background: var(--border);
                overflow: hidden;
                margin-top: 8px;
            }
            
            .progress-fill {
                height: 100%;
                background: var(--accent);
            }
            
            .footer {
                text-align: center;
                color: var(--text-muted);
                font-size: 12px;
                margin-top: 32px;
                padding-top: 16px;
                border-top: 1px solid var(--border);
            }
            
            .footer-brand {
                font-family: 'VT323', monospace;
                font-size: 16px;
                margin-top: 8px;
            }
            
            /* Hide Streamlit elements */
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            .stDeployButton {display: none;}
        </style>
        """

# ============================================================
# Constants
# ============================================================
IRS_LIMIT = 25000

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
        
        return {
            "symbol": symbol.upper(),
            "companyName": info.get("longName") or info.get("shortName", symbol.upper()),
            "currentPrice": current_price,
            "previousClose": previous_close,
            "dayChange": round(day_change, 2),
            "dayChangePercent": round(day_change_pct, 2),
        }
    except Exception as e:
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
    except:
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
# ESPP Calculation
# ============================================================
def calculate_purchase(
    grant_price: float,
    purchase_price: float,
    total_contribution: float,
    discount_rate: float,
    has_lookback: bool
) -> Dict[str, Any]:
    """Calculate purchase details for a single ESPP purchase."""
    
    if has_lookback:
        effective_price = min(grant_price, purchase_price)
        lookback_used = 'grant' if grant_price <= purchase_price else 'purchase'
    else:
        effective_price = purchase_price
        lookback_used = 'purchase'
    
    discounted_price = effective_price * (1 - discount_rate / 100)
    
    max_shares = total_contribution / discounted_price
    whole_shares = math.floor(max_shares)
    
    cost_of_shares = whole_shares * discounted_price
    cash_left_over = total_contribution - cost_of_shares
    
    total_proceeds = whole_shares * purchase_price
    
    gain_dollars = total_proceeds - cost_of_shares
    gain_percent = (gain_dollars / cost_of_shares * 100) if cost_of_shares > 0 else 0
    
    fmv_used = whole_shares * grant_price
    
    return {
        "effective_price": round(effective_price, 2),
        "discounted_price": round(discounted_price, 2),
        "lookback_used": lookback_used,
        "whole_shares": whole_shares,
        "cost_of_shares": round(cost_of_shares, 2),
        "cash_left_over": round(cash_left_over, 2),
        "total_proceeds": round(total_proceeds, 2),
        "gain_dollars": round(gain_dollars, 2),
        "gain_percent": round(gain_percent, 1),
        "fmv_used": round(fmv_used, 2),
    }


# ============================================================
# Chart Functions
# ============================================================
def create_waterfall_chart(cost_basis: float, gain: float, dark_mode: bool):
    """Create a horizontal stacked bar chart showing cost + gain = proceeds."""
    
    colors = {
        'cost': '#444444' if dark_mode else '#e0e0e0',
        'gain': '#39ff14' if dark_mode else '#32cd32',
        'text_cost': '#888888' if dark_mode else '#666666',
        'text_gain': '#1a1a1a' if dark_mode else '#ffffff',
        'bg': 'rgba(0,0,0,0)',
    }
    
    fig = go.Figure()
    
    # Cost basis bar
    fig.add_trace(go.Bar(
        y=['Proceeds'],
        x=[cost_basis],
        orientation='h',
        name='Your Cost',
        marker_color=colors['cost'],
        text=[f'${cost_basis:,.0f}'],
        textposition='inside',
        textfont=dict(color=colors['text_cost'], size=14, family='Space Mono'),
        hoverinfo='skip',
    ))
    
    # Gain bar
    fig.add_trace(go.Bar(
        y=['Proceeds'],
        x=[gain],
        orientation='h',
        name='Gain',
        marker_color=colors['gain'],
        text=[f'+${gain:,.0f}'],
        textposition='inside',
        textfont=dict(color=colors['text_gain'], size=14, family='Space Mono'),
        hoverinfo='skip',
    ))
    
    fig.update_layout(
        barmode='stack',
        showlegend=False,
        height=70,
        margin=dict(l=0, r=0, t=0, b=0),
        paper_bgcolor=colors['bg'],
        plot_bgcolor=colors['bg'],
        xaxis=dict(visible=False),
        yaxis=dict(visible=False),
    )
    
    return fig


# ============================================================
# Main App
# ============================================================
def main():
    # Initialize dark mode in session state
    if 'dark_mode' not in st.session_state:
        st.session_state.dark_mode = True
    
    # Apply CSS
    st.markdown(get_css(st.session_state.dark_mode), unsafe_allow_html=True)
    
    # ============================================================
    # Header
    # ============================================================
    col_title, col_toggle = st.columns([4, 1])
    
    with col_title:
        st.markdown('<div class="main-header">ESPP OPTIMIZER_</div>', unsafe_allow_html=True)
        st.markdown('<div class="sub-header">Employee Stock Purchase Plan Calculator</div>', unsafe_allow_html=True)
    
    with col_toggle:
        if st.button('🌙 DARK' if not st.session_state.dark_mode else '☀️ LIGHT'):
            st.session_state.dark_mode = not st.session_state.dark_mode
            st.rerun()
    
    # ============================================================
    # Inputs - Compact Row
    # ============================================================
    with st.expander("⚙️ Settings", expanded=True):
        col1, col2, col3 = st.columns(3)
        
        with col1:
            ticker_input = st.text_input("Ticker", value="TSLA").upper()
            annual_salary = st.number_input("Annual Salary", value=150000, step=5000, format="%d")
        
        with col2:
            grant_date = st.date_input(
                "Grant Date",
                value=datetime(2025, 9, 1),
                max_value=datetime.now().date()
            )
            contribution_pct = st.slider("Contribution %", 1, 15, 10)
        
        with col3:
            purchase_period = st.selectbox("Purchase Period", [3, 6], index=1, format_func=lambda x: f"{x} months")
            discount_rate = st.slider("Discount %", 0, 15, 15)
        
        has_lookback = st.checkbox("Lookback Provision", value=True)
        prior_fmv = st.number_input("Prior FMV Used This Year", value=0.0, step=100.0)
    
    # Fetch data
    stock_data = fetch_stock_data(ticker_input)
    hist_data = fetch_historical_data(ticker_input)
    
    if stock_data is None or hist_data is None:
        st.error(f"Could not fetch data for {ticker_input}. Please check the ticker.")
        return
    
    # Calculate dates and prices
    grant_datetime = datetime.combine(grant_date, datetime.min.time())
    purchase_date = grant_datetime + relativedelta(months=purchase_period)
    
    grant_price = get_price_at_date(hist_data, grant_datetime)
    actual_grant_date = get_actual_date_used(hist_data, grant_datetime)
    
    if purchase_date.date() >= datetime.now().date():
        purchase_price = stock_data['currentPrice']
        is_future_purchase = True
    else:
        purchase_price = get_price_at_date(hist_data, purchase_date) or stock_data['currentPrice']
        is_future_purchase = False
    
    if grant_price is None:
        st.error("Could not fetch grant date price.")
        return
    
    # Calculate contribution
    periods_per_year = 12 / purchase_period
    contribution = (annual_salary * contribution_pct / 100) / periods_per_year
    
    # Calculate purchase
    purchase = calculate_purchase(
        grant_price=grant_price,
        purchase_price=purchase_price,
        total_contribution=contribution,
        discount_rate=discount_rate,
        has_lookback=has_lookback
    )
    
    # ============================================================
    # Stock Card
    # ============================================================
    change_sign = "+" if stock_data['dayChangePercent'] >= 0 else ""
    
    st.markdown(f'''
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: flex-start;">
            <div>
                <span class="big-number">{stock_data["symbol"]}</span>
                <span class="tag" style="margin-left: 12px;">{change_sign}{stock_data["dayChangePercent"]:.1f}%</span>
                <div style="color: var(--text-muted); margin-top: 4px;">{stock_data["companyName"]}</div>
            </div>
            <div style="text-align: right;">
                <div class="big-number">${stock_data["currentPrice"]:,.2f}</div>
                <div style="color: var(--text-muted); font-size: 14px;">current price</div>
            </div>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # ============================================================
    # Proceeds Waterfall Card
    # ============================================================
    st.markdown(f'''
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: baseline; margin-bottom: 8px;">
            <span class="label">Total Proceeds</span>
            <span class="big-number">${purchase["total_proceeds"]:,.2f}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # Waterfall chart
    fig = create_waterfall_chart(
        purchase['cost_of_shares'],
        purchase['gain_dollars'],
        st.session_state.dark_mode
    )
    st.plotly_chart(fig, use_container_width=True, config={'displayModeBar': False})
    
    # Legend and summary
    accent_color = '#39ff14' if st.session_state.dark_mode else '#32cd32'
    muted_color = '#888888' if st.session_state.dark_mode else '#666666'
    bar_color = '#444444' if st.session_state.dark_mode else '#e0e0e0'
    
    st.markdown(f'''
    <div style="display: flex; justify-content: space-between; margin-bottom: 16px; font-size: 14px;">
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 12px; height: 12px; background: {bar_color};"></div>
            <span style="color: {muted_color};">Your Cost</span>
        </div>
        <div style="display: flex; align-items: center; gap: 8px;">
            <div style="width: 12px; height: 12px; background: {accent_color};"></div>
            <span class="highlight">Gain +{purchase["gain_percent"]:.1f}%</span>
        </div>
    </div>
    <hr class="divider">
    <div style="display: flex; justify-content: space-between; font-size: 14px; color: var(--text);">
        <div>
            <strong>{purchase["whole_shares"]}</strong> shares @ <strong>${purchase["discounted_price"]:,.2f}</strong>
            <span style="color: {muted_color};"> ({discount_rate}% discount)</span>
        </div>
        <div style="color: {muted_color};">
            ${purchase["cash_left_over"]:.2f} cash back
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # ============================================================
    # Date Cards with Lookback Highlight
    # ============================================================
    col_grant, col_purchase = st.columns(2)
    
    grant_highlighted = has_lookback and purchase['lookback_used'] == 'grant'
    purchase_highlighted = has_lookback and purchase['lookback_used'] == 'purchase'
    
    with col_grant:
        highlight_class = 'card-highlight' if grant_highlighted else ''
        badge = '<span class="lookback-badge">✓ LOOKBACK</span>' if grant_highlighted else ''
        price_class = 'highlight-alt' if grant_highlighted else ''
        discount_line = f'<div style="color: var(--accent-alt); font-size: 12px; margin-top: 8px; font-family: Space Mono, monospace;">→ ${purchase["discounted_price"]:.2f} after {discount_rate}% discount</div>' if grant_highlighted else ''
        
        st.markdown(f'''
        <div class="card {highlight_class}" style="position: relative;">
            {badge}
            <div class="label">Grant Date</div>
            <div class="medium-number">{actual_grant_date.strftime("%b %d, %Y") if actual_grant_date else "N/A"}</div>
            <div style="margin-top: 8px;">
                <span class="small-number {price_class}">${grant_price:,.2f}</span>
                <span style="color: var(--text-muted); font-size: 14px; margin-left: 8px;">close</span>
            </div>
            {discount_line}
        </div>
        ''', unsafe_allow_html=True)
    
    with col_purchase:
        highlight_class = 'card-highlight' if purchase_highlighted else ''
        badge = '<span class="lookback-badge">✓ LOOKBACK</span>' if purchase_highlighted else ''
        price_class = 'highlight-alt' if purchase_highlighted else ''
        price_label = 'current' if is_future_purchase else 'close'
        discount_line = f'<div style="color: var(--accent-alt); font-size: 12px; margin-top: 8px; font-family: Space Mono, monospace;">→ ${purchase["discounted_price"]:.2f} after {discount_rate}% discount</div>' if purchase_highlighted else ''
        
        st.markdown(f'''
        <div class="card {highlight_class}" style="position: relative;">
            {badge}
            <div class="label">Purchase Date</div>
            <div class="medium-number">{purchase_date.strftime("%b %d, %Y")}</div>
            <div style="margin-top: 8px;">
                <span class="small-number {price_class}">${purchase_price:,.2f}</span>
                <span style="color: var(--text-muted); font-size: 14px; margin-left: 8px;">{price_label}</span>
            </div>
            {discount_line}
        </div>
        ''', unsafe_allow_html=True)
    
    # ============================================================
    # Purchase Breakdown
    # ============================================================
    st.markdown(f'''
    <div class="card">
        <div class="label" style="margin-bottom: 12px;">Purchase Breakdown</div>
        <div class="inline-stat">
            <span>Your Contribution</span>
            <span class="small-number">${contribution:,.2f}</span>
        </div>
        <div class="inline-stat">
            <span>Shares Purchased</span>
            <span class="small-number">{purchase["whole_shares"]}</span>
        </div>
        <div class="inline-stat">
            <span>Cost Basis</span>
            <span>${purchase["cost_of_shares"]:,.2f}</span>
        </div>
        <div class="inline-stat">
            <span>Market Value</span>
            <span class="highlight-alt">${purchase["total_proceeds"]:,.2f}</span>
        </div>
        <div class="inline-stat">
            <span>Cash Returned</span>
            <span>${purchase["cash_left_over"]:.2f}</span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # ============================================================
    # IRS Limit
    # ============================================================
    current_year = datetime.now().year
    fmv_this_purchase = purchase['fmv_used']
    total_fmv_used = prior_fmv + fmv_this_purchase
    remaining_fmv = max(0, IRS_LIMIT - total_fmv_used)
    usage_pct = min((total_fmv_used / IRS_LIMIT) * 100, 100)
    
    # Calculate next offering recommendation
    next_purchase_date = purchase_date + relativedelta(months=purchase_period)
    crosses_new_year = next_purchase_date.year > current_year
    available_fmv = IRS_LIMIT if crosses_new_year else remaining_fmv
    
    if available_fmv > 0:
        estimated_grant_price = stock_data['currentPrice']
        max_shares_by_irs = available_fmv / estimated_grant_price
        estimated_discounted = estimated_grant_price * (1 - discount_rate / 100)
        max_contribution_by_irs = max_shares_by_irs * estimated_discounted
        max_annual_contribution = max_contribution_by_irs * periods_per_year
        recommended_pct = min(15, (max_annual_contribution / annual_salary) * 100)
    else:
        recommended_pct = 0
    
    fmv_used_display = f"{total_fmv_used:,.2f}"
    
    st.markdown(f'''
    <div class="card">
        <div style="display: flex; justify-content: space-between; align-items: baseline;">
            <span class="label">IRS Limit ({current_year})</span>
            <span style="font-size: 14px; color: var(--text-muted);">
                \\${fmv_used_display} of \\$25,000
            </span>
        </div>
        <div class="progress-container">
            <div class="progress-fill" style="width: {usage_pct}%;"></div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 12px; font-size: 14px;">
            <span>
                <span class="highlight-alt" style="font-weight: bold;">${remaining_fmv:,.2f}</span> remaining
            </span>
            <span>
                Next offering: <strong>{recommended_pct:.0f}%</strong> recommended
            </span>
        </div>
    </div>
    ''', unsafe_allow_html=True)
    
    # ============================================================
    # Footer
    # ============================================================
    st.markdown(f'''
    <div class="footer">
        <div>For educational purposes only. Consult a tax professional.</div>
        <div class="footer-brand">ESPP OPTIMIZER v2.0 // {datetime.now().year}</div>
    </div>
    ''', unsafe_allow_html=True)


if __name__ == "__main__":
    main()
