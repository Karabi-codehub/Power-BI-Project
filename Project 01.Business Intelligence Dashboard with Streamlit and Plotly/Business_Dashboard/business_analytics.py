from datetime import datetime,timedelta
import pandas as pd

"""
business_analytics.py

This module contains business analytics functions originally developed in Dashboard_project_ML_code
in Jupyter Notebook for sales and inventory tracking, now refactored
for reuse in production-level code.

Functions include revenue, profit, stock status, KPIs, and sales filters.
"""

from datetime import datetime, timedelta


# 📦 Inventory Tracking
def get_current_stock(sales_df, purchases_df, product_id):
    """
    Calculate current stock of a product.

    Subtracts quantity sold from quantity purchased.

    Parameters:
        sales_df (DataFrame): Sales data
        purchases_df (DataFrame): Purchase data
        product_id (str or int): Product ID

    Returns:
        int: Current stock
    """
    quantity_purchased = purchases_df[purchases_df['product_id'] == product_id]['quantity_purchased'].sum()
    quantity_sold = sales_df[sales_df['product_id'] == product_id]['quantity_sold'].sum()
    current_stock = quantity_purchased - quantity_sold
    return current_stock


# 💰 Profit Calculation
def get_profit(products_df, sales_df, product_id):
    """
    Calculate profit made from a product.

    Parameters:
        products_df (DataFrame): Product details
        sales_df (DataFrame): Sales records
        product_id (str or int): Product ID

    Returns:
        float: Total profit
    """
    quantity_sold = sales_df[sales_df['product_id'] == product_id]['quantity_sold'].sum()
    product = products_df[products_df['product_id'] == product_id]
    profit_per_sale = product['selling_price'] - product['cost_price']
    profit_per_sale = profit_per_sale.iloc[0]
    total_profit = profit_per_sale * quantity_sold
    return total_profit


# 🐢 Slow Moving Product Detection
def is_slow_moving(sales_df, product_id):
    """
    Determine if a product is slow moving (less than 40 units sold in last 90 days).

    Parameters:
        sales_df (DataFrame): Sales records
        product_id (str or int): Product ID

    Returns:
        bool: True if slow moving, False otherwise
    """
    start_date = datetime.strptime('2024-12-31', '%Y-%m-%d').date()
    cutoff_date = start_date - timedelta(days=90)
    last_90_days_sales = sales_df[
        (sales_df['product_id'] == product_id) &
        (sales_df['sale_date'] >= cutoff_date)
        ]
    total_recent_sales = last_90_days_sales['quantity_sold'].sum()
    return total_recent_sales < 40


# 📦 Stock Level Status
def get_stock_status(products_df, product_id):
    """
    Categorize product as Understocked, Overstocked, or Properly Stocked.

    Parameters:
        products_df (DataFrame): Product data with stock and reorder info
        product_id (str or int): Product ID

    Returns:
        str: Stock status
    """
    product = products_df[products_df['product_id'] == product_id].iloc[0]
    stock = product['current_stock']
    reorder = product['reorder_level']
    if stock < reorder:
        return 'Understocked'
    elif stock > reorder * 15:
        return 'Overstocked'
    return 'Properly Stocked'


# 💸 Revenue Calculation
def get_revenue(products_df, sales_df, product_id):
    """
    Calculate revenue generated from a product.

    Parameters:
        products_df (DataFrame): Product pricing info
        sales_df (DataFrame): Sales records
        product_id (str or int): Product ID

    Returns:
        float: Revenue
    """
    selling_price = products_df[products_df['product_id'] == product_id]['selling_price'].iloc[0]
    quantity_sold = sales_df[sales_df['product_id'] == product_id]['quantity_sold'].sum()
    revenue = selling_price * quantity_sold
    return revenue


# 📊 Filter Sales by Date & Location
def get_sales_between_dates(sales_df, start_date, end_date, locations):
    """
    Filter sales within a date range and selected locations.

    Parameters:
        sales_df (DataFrame): Sales data
        start_date (date): Start date
        end_date (date): End date
        locations (list): List of locations

    Returns:
        DataFrame: Filtered sales
    """
    return sales_df[
        (sales_df['sale_date'] >= start_date)
        & (sales_df['sale_date'] <= end_date)
        & (sales_df['location'].isin(locations))
        ]


# 🏷️ Filter Products by Category
def get_products_of_selected_categories(products_df, categories):
    """
    Filter products that belong to selected categories.

    Parameters:
        products_df (DataFrame): Product data
        categories (list): Category names

    Returns:
        DataFrame: Filtered products
    """
    return products_df[products_df['category'].isin(categories)]


# 🛑 Find Understocked Products
def get_under_stocked_products(products_df):
    """
    Get list of understocked products based on 'stock_status'.

    Parameters:
        products_df (DataFrame): Product data

    Returns:
        DataFrame: Understocked products
    """
    return products_df[products_df['stock_status'] == 'Understocked']


# 📈 KPI Summary
def get_summary_kpis(sales_df, products_df):
    """
    Generate a summary of business KPIs.

    Parameters:
        sales_df (DataFrame): Sales data
        products_df (DataFrame): Product data

    Returns:
        dict: KPI summary with total revenue, profit, units sold, understocked count
    """
    total_revenue = products_df['product_id'].apply(
        lambda product_id: get_revenue(products_df, sales_df, product_id)
    ).sum()

    total_profit = products_df['profit'].sum()
    total_units_sold = sales_df['quantity_sold'].sum()
    total_understocked_products = len(get_under_stocked_products(products_df))

    return {
        'Total Revenue (K)': int(total_revenue / 1e3),
        'Total Profit (K)': int(total_profit / 1e3),
        'Total Units Sold (K)': int(total_units_sold / 1e3),
        'Total Understocked Products': total_understocked_products
    }
# key performance metrics, which is an essential step in any Business Analytics Dashboard

def add_business_analytics(products_df, sales_df, purchases_df):
    """
    Enhance the products DataFrame with key business analytics features
    to support dashboard reporting and decision-making.

    This function adds the following calculated columns to `products_df`:
    - current_stock: Inventory available (purchases - sales)
    - profit: Total profit earned from each product
    - slow_moving: Flags products with low recent sales activity
    - stock_status: Classifies inventory as Understocked, Properly Stocked, or Overstocked

    These metrics are crucial for monitoring product performance,
    identifying supply issues, and improving inventory planning in a business analytics dashboard.

    Parameters:
        products_df (DataFrame): Product information table
        sales_df (DataFrame): Sales transactions
        purchases_df (DataFrame): Purchase transactions

    Returns:
        tuple: Updated versions of (products_df, sales_df, purchases_df)
    """

    # Calculate how many units of each product are currently in stock
    products_df['current_stock'] = products_df['product_id'].apply(
        lambda product_id: get_current_stock(sales_df, purchases_df, product_id)
    )

    # Compute total profit earned from each product
    products_df['profit'] = products_df['product_id'].apply(
        lambda product_id: get_profit(products_df, sales_df, product_id)
    )

    # Identify slow-moving products based on last 90 days of sales
    products_df['slow_moving'] = products_df['product_id'].apply(
        lambda product_id: is_slow_moving(sales_df, product_id)
    )

    # Determine the stock level status (e.g., Understocked, Overstocked, etc.)
    products_df['stock_status'] = products_df['product_id'].apply(
        lambda product_id: get_stock_status(products_df, product_id)
    )

    return products_df, sales_df, purchases_df
