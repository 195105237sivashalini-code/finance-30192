import psycopg2
from psycopg2 import sql
import pandas as pd
from datetime import datetime
from decimal import Decimal 

# IMPORTANT: Update these details with your PostgreSQL database credentials.
connection_details = {
    'database': 'Finance',
    'user': 'postgres',
    'password': 'sindhu',
    'host': 'localhost',
    'port': '5432'
}

class FinancialPortfolioTracker:
    def __init__(self):
        """Initializes the database connection."""
        self.conn = None
        self.cursor = None
        self.connect()

    def connect(self):
        """Establishes a connection to the PostgreSQL database."""
        try:
            self.conn = psycopg2.connect(**connection_details)
            self.cursor = self.conn.cursor()
            print("Successfully connected to the database.")
        except psycopg2.Error as e:
            print(f"Error connecting to database: {e}")
            self.conn = None
            self.cursor = None
            raise Exception("Failed to connect to the database. Please check your credentials.")

    def close(self):
        """Closes the database connection."""
        if self.cursor:
            self.cursor.close()
        if self.conn:
            self.conn.close()
            print("Database connection closed.")

    # --- CRUD Operations ---

    def create_asset(self, ticker, purchase_date, shares, cost_basis, asset_class):
        """
        CREATE operation: Adds a new asset to the portfolio.
        The ON CONFLICT clause prevents duplicate entries.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO assets (ticker, purchase_date, shares, cost_basis, asset_class)
                VALUES (%s, %s, %s, %s, %s)
                ON CONFLICT (ticker) DO NOTHING;
                """,
                (ticker, purchase_date, shares, cost_basis, asset_class)
            )
            self.conn.commit()
            print(f"Asset '{ticker}' created successfully.")
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error creating asset: {e}")
            return False

    def read_all_assets(self):
        """READ operation: Retrieves all assets from the database."""
        try:
            self.cursor.execute("SELECT * FROM assets ORDER BY ticker;")
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return pd.DataFrame(rows, columns=columns)
        except psycopg2.Error as e:
            print(f"Error reading assets: {e}")
            return pd.DataFrame()

    def update_asset(self, original_ticker, new_ticker, purchase_date, shares, cost_basis, asset_class):
        """
        UPDATE operation: Modifies an existing asset's details.
        """
        try:
            self.cursor.execute(
                """
                UPDATE assets
                SET ticker = %s, purchase_date = %s, shares = %s, cost_basis = %s, asset_class = %s
                WHERE ticker = %s;
                """,
                (new_ticker, purchase_date, shares, cost_basis, asset_class, original_ticker)
            )
            self.conn.commit()
            print(f"Asset '{original_ticker}' updated successfully.")
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error updating asset: {e}")
            return False

    def delete_asset(self, ticker):
        """
        DELETE operation: Removes an asset. The database will handle transaction deletion.
        """
        try:
            self.cursor.execute("DELETE FROM assets WHERE ticker = %s;", (ticker,))
            self.conn.commit()
            print(f"Asset '{ticker}' deleted successfully.")
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error deleting asset: {e}")
            return False

    def add_transaction(self, ticker, transaction_type, amount, notes=None):
        """
        Adds a new transaction for an asset.
        """
        try:
            self.cursor.execute(
                """
                INSERT INTO transactions (ticker, transaction_date, transaction_type, amount, notes)
                VALUES (%s, %s, %s, %s, %s);
                """,
                (ticker, datetime.now().date(), transaction_type, amount, notes)
            )
            self.conn.commit()
            print(f"Transaction for '{ticker}' added successfully.")
            return True
        except psycopg2.Error as e:
            self.conn.rollback()
            print(f"Error adding transaction: {e}")
            return False

    def get_all_transactions(self):
        """Retrieves all transactions from the database."""
        try:
            self.cursor.execute("SELECT * FROM transactions ORDER BY transaction_date DESC;")
            rows = self.cursor.fetchall()
            columns = [desc[0] for desc in self.cursor.description]
            return pd.DataFrame(rows, columns=columns)
        except psycopg2.Error as e:
            print(f"Error retrieving transactions: {e}")
            return pd.DataFrame()

    # --- Business Insights using Aggregate Functions ---

    def get_portfolio_summary(self):
        """
        Provides portfolio insights using COUNT, SUM, and AVG.
        Note: For a real application, a financial data API would be used to fetch real-time prices.
        This function uses a simplified calculation for demonstration.
        """
        try:
            # Query assets to get the necessary data for calculations
            self.cursor.execute("SELECT ticker, shares, cost_basis, asset_class FROM assets;")
            rows = self.cursor.fetchall()
            assets_df = pd.DataFrame(rows, columns=['ticker', 'shares', 'cost_basis', 'asset_class'])

            if assets_df.empty:
                return {
                    'total_assets_count': 0,
                    'total_cost_basis': 0,
                    'total_market_value': 0,
                    'total_gain_loss': 0,
                    'avg_cost_basis': 0
                }

            # For demonstration, we'll assume a 10% gain for all assets
            assets_df['current_price'] = assets_df['cost_basis'].apply(lambda x: x * Decimal('1.10'))
            assets_df['current_value'] = assets_df['shares'] * assets_df['current_price']
            assets_df['gain_loss'] = assets_df['current_value'] - assets_df['cost_basis']

            return {
                'total_assets_count': len(assets_df),
                'total_cost_basis': assets_df['cost_basis'].sum(),
                'total_market_value': assets_df['current_value'].sum(),
                'total_gain_loss': assets_df['gain_loss'].sum(),
                'avg_cost_basis': assets_df['cost_basis'].mean()
            }
        except psycopg2.Error as e:
            print(f"Error getting portfolio summary: {e}")
            return {}

    def get_asset_allocation(self):
        """
        Provides a breakdown of the portfolio by asset class.
        """
        try:
            self.cursor.execute("SELECT asset_class, SUM(cost_basis) FROM assets GROUP BY asset_class;")
            allocation = self.cursor.fetchall()
            return {row[0]: float(row[1]) for row in allocation}
        except psycopg2.Error as e:
            print(f"Error getting asset allocation: {e}")
            return {}

    def get_insights(self):
        """
        Calculates and returns various business insights using SQL aggregate functions.
        """
        try:
            self.cursor.execute("SELECT COUNT(*), SUM(cost_basis), AVG(cost_basis), MIN(shares), MAX(shares) FROM assets;")
            result = self.cursor.fetchone()
            
            if result and result[0] is not None:
                return {
                    "total_assets": result[0],
                    "total_cost_basis": float(result[1]) if result[1] is not None else 0.0,
                    "avg_cost_basis": float(result[2]) if result[2] is not None else 0.0,
                    "min_shares": float(result[3]) if result[3] is not None else 0.0,
                    "max_shares": float(result[4]) if result[4] is not None else 0.0
                }
            else:
                return {
                    "total_assets": 0,
                    "total_cost_basis": 0.0,
                    "avg_cost_basis": 0.0,
                    "min_shares": 0.0,
                    "max_shares": 0.0
                }
        except psycopg2.Error as e:
            print(f"Error getting business insights: {e}")
            return {}