import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
from backend import FinancialPortfolioTracker

st.set_page_config(layout="wide", page_title="Financial Portfolio Tracker - Siva Shalini 30192")

# Initialize the backend tracker
@st.cache_resource
def get_tracker():
    """Create a single instance of the tracker and cache it."""
    try:
        return FinancialPortfolioTracker()
    except Exception as e:
        st.error(f"Application failed to connect to the database. Please check your credentials in 'backward_fin.py'. Error: {e}")
        st.stop()

tracker = get_tracker()

# --- Functions to display different sections ---

def display_portfolio_dashboard():
    """Displays the main portfolio summary and allocation chart."""
    st.header("📊 Portfolio Dashboard")
    summary = tracker.get_portfolio_summary()
    
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Market Value", f"${summary.get('total_market_value', 0):,.2f}")
    with col2:
        st.metric("Total Gain/Loss", f"${summary.get('total_gain_loss', 0):,.2f}")
    with col3:
        st.metric("Total Cost Basis", f"${summary.get('total_cost_basis', 0):,.2f}")
    with col4:
        st.metric("Number of Assets", f"{summary.get('total_assets_count', 0)}")

    st.markdown("---")
    st.subheader("Asset Allocation by Cost Basis")
    allocation_data = tracker.get_asset_allocation()
    if allocation_data:
        allocation_df = pd.DataFrame(allocation_data.items(), columns=['Asset Class', 'Cost Basis'])
        fig = px.pie(allocation_df, names='Asset Class', values='Cost Basis', title="Asset Allocation")
        st.plotly_chart(fig, use_container_width=True)

    else:
        st.info("No assets to display. Add some assets to see your allocation.")

def display_manage_assets():
    """Displays forms for CRUD operations on assets."""
    st.header("➕ Manage Assets")

    # CREATE Section
    st.subheader("Add New Asset")
    with st.form("add_asset_form", clear_on_submit=True):
        col_c1, col_c2, col_c3 = st.columns(3)
        with col_c1:
            ticker = st.text_input("Ticker Symbol", key="add_ticker").upper()
            shares = st.number_input("Number of Shares", min_value=0.01, format="%.4f", key="add_shares")
        with col_c2:
            purchase_date = st.date_input("Purchase Date", datetime.now().date(), key="add_date")
            asset_class = st.selectbox(
                "Asset Class", 
                ["Equities", "Fixed Income", "Crypto", "Real Estate", "Other"],
                key="add_class"
            )
        with col_c3:
            cost_basis = st.number_input("Total Cost Basis", min_value=0.01, format="%.2f", key="add_cost")

        submitted = st.form_submit_button("Add Asset")
        if submitted:
            if ticker and shares and cost_basis:
                if tracker.create_asset(ticker, purchase_date, shares, cost_basis, asset_class):
                    st.success(f"Asset '{ticker}' added successfully!")
                else:
                    st.error("Failed to add asset. Ticker might already exist.")
            else:
                st.warning("Please fill in all fields.")

    st.markdown("---")
    
    # READ/UPDATE/DELETE Section
    st.subheader("View, Update, or Delete Existing Assets")
    assets_df = tracker.read_all_assets()
    if not assets_df.empty:
        st.dataframe(assets_df, use_container_width=True)

        st.markdown("---")
        
        with st.form("update_delete_form"):
            selected_ticker = st.selectbox("Select Asset to Update/Delete", assets_df['ticker'].tolist(), key="select_asset")
            
            selected_row = assets_df[assets_df['ticker'] == selected_ticker].iloc[0]
            
            col_ud1, col_ud2, col_ud3 = st.columns(3)
            with col_ud1:
                new_ticker = st.text_input("New Ticker Symbol", value=selected_row['ticker'], key="update_ticker").upper()
                new_shares = st.number_input("New Shares", value=float(selected_row['shares']), format="%.4f", key="update_shares")
            with col_ud2:
                new_date = st.date_input("New Purchase Date", value=selected_row['purchase_date'], key="update_date")
                new_class = st.selectbox(
                    "New Asset Class", 
                    ["Equities", "Fixed Income", "Crypto", "Real Estate", "Other"],
                    index=["Equities", "Fixed Income", "Crypto", "Real Estate", "Other"].index(selected_row['asset_class']),
                    key="update_class"
                )
            with col_ud3:
                new_cost = st.number_input("New Total Cost Basis", value=float(selected_row['cost_basis']), format="%.2f", key="update_cost")

            col_ud_btn1, col_ud_btn2 = st.columns(2)
            with col_ud_btn1:
                update_btn = st.form_submit_button("Update Asset")
            with col_ud_btn2:
                delete_btn = st.form_submit_button("Delete Asset")

            if update_btn:
                if tracker.update_asset(selected_ticker, new_ticker, new_date, new_shares, new_cost, new_class):
                    st.success(f"Asset '{selected_ticker}' updated successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to update asset.")
            
            if delete_btn:
                if tracker.delete_asset(selected_ticker):
                    st.success(f"Asset '{selected_ticker}' deleted successfully!")
                    st.experimental_rerun()
                else:
                    st.error("Failed to delete asset.")
    else:
        st.info("No assets in the portfolio. Use the form above to add one.")

def display_transactions():
    """Displays the transaction logging and history."""
    st.header("📝 Transactions")

    st.subheader("Log a New Transaction")
    assets_df = tracker.read_all_assets()
    if not assets_df.empty:
        with st.form("add_transaction_form", clear_on_submit=True):
            col_t1, col_t2 = st.columns(2)
            with col_t1:
                selected_ticker = st.selectbox("Select Asset", assets_df['ticker'].tolist(), key="trans_ticker")
                amount = st.number_input("Amount", format="%.2f", key="trans_amount")
            with col_t2:
                trans_type = st.selectbox("Transaction Type", ["Buy", "Sell", "Dividend"], key="trans_type")
                notes = st.text_area("Notes (Optional)", key="trans_notes")
            
            submitted = st.form_submit_button("Log Transaction")
            if submitted:
                if selected_ticker and amount:
                    if tracker.add_transaction(selected_ticker, trans_type, amount, notes):
                        st.success("Transaction logged successfully!")
                    else:
                        st.error("Failed to log transaction.")
                else:
                    st.warning("Please select an asset and enter an amount.")
    else:
        st.info("Add an asset first to log a transaction.")
        
    st.markdown("---")
    st.subheader("Transaction History")
    transactions_df = tracker.get_all_transactions()
    if not transactions_df.empty:
        st.dataframe(transactions_df, use_container_width=True)
    else:
        st.info("No transactions to display.")

def display_business_insights():
    """Displays business insights using aggregate functions."""
    st.header("📈 Business Insights")
    insights = tracker.get_insights()
    
    if insights.get("total_assets", 0) == 0:
        st.info("No data available for insights. Please add some assets.")
        return

    col_i1, col_i2, col_i3, col_i4 = st.columns(4)
    with col_i1:
        st.metric("Total Number of Assets", insights.get('total_assets', 'N/A'))
    with col_i2:
        if insights.get('total_cost_basis') is not None:
            st.metric("Total Cost Basis", f"${insights.get('total_cost_basis', 0):,.2f}")
    with col_i3:
        if insights.get('avg_cost_basis') is not None:
            st.metric("Average Cost Basis", f"${insights.get('avg_cost_basis', 0):,.2f}")
    with col_i4:
        st.metric("Largest Share Holding", insights.get('max_shares', 'N/A'))
        st.metric("Smallest Share Holding", insights.get('min_shares', 'N/A'))

# --- Main App Logic ---
st.title("💰 Financial Portfolio Tracker - Siva Shalini J 30192")

# Create a navigation menu
page = st.sidebar.radio("Navigation", ["Dashboard", "Manage Assets", "Transactions", "Business Insights"])

if page == "Dashboard":
    display_portfolio_dashboard()
elif page == "Manage Assets":
    display_manage_assets()
elif page == "Transactions":
    display_transactions()
elif page == "Business Insights":
    display_business_insights()