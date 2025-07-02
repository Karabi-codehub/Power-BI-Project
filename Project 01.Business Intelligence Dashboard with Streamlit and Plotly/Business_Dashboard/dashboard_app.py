# Import necessary libraries
import streamlit as st
from business_analytics import *  # Custom module with business logic and analytics functions
import plotly.express as px  # For interactive visualizations
import base64  # Used for encoding CSV files for download
import numpy as np  # For numerical operations

# Streamlit page configuration
st.set_page_config(
    page_title="Business Dashboard",
    layout="wide"  # Uses the full browser width
)

# Function to upload and load multiple CSV files from the sidebar
def upload_files():
    uploaded_files = st.sidebar.file_uploader(
        label="upload CSV files",
        type="csv",
        accept_multiple_files=True
    )

    # Initialize variables
    products_df, sales_df, purchases_df = None, None, None

    # Loop through uploaded files and assign to respective variables
    for file in uploaded_files:
        if file.name == 'products.csv':
            products_df = pd.read_csv(file)
        elif file.name == 'sales.csv':
            sales_df = pd.read_csv(file)
            sales_df['sale_date'] = pd.to_datetime(sales_df['sale_date']).dt.date
        elif file.name == 'purchases.csv':
            purchases_df = pd.read_csv(file)
            purchases_df['purchase_date'] = pd.to_datetime(purchases_df['purchase_date']).dt.date

    return products_df, sales_df, purchases_df

# Load data
products_df, sales_df, purchases_df = upload_files()

# ---------------- Sidebar for Filters ---------------- #

st.sidebar.header("Filters")  # Sidebar title

# Default date range
date1 = datetime.strptime('2024-01-01', '%Y-%m-%d').date()
date2 = datetime.strptime('2024-12-31', '%Y-%m-%d').date()

# Date filter input
date_range = st.sidebar.date_input(
    label="Select Date Range",
    value=[date1, date2]
)

# Location multiselect filter
location_filter = st.sidebar.multiselect(
    label="Select Store Location",
    options=['Dhaka', 'Chittagong', 'Sylhet', 'Rajshahi'],
    default=['Dhaka']
)

# Category multiselect filter
category_filter = st.sidebar.multiselect(
    label="Select Product Category",
    options=['Groceries', 'Electronics', 'Clothing', 'Perishables'],
    default=['Groceries', 'Electronics']
)

# ---------------- Main Dashboard Content ---------------- #

st.header("Business Dashboard")  # Main header

# Ensure data is loaded before proceeding
if products_df is not None:
    # Add business-related metrics and flags to the DataFrames
    products_df, sales_df, purchases_df = add_business_analytics(
        products_df=products_df,
        sales_df=sales_df,
        purchases_df=purchases_df,
    )

    # Extract start and end dates from filter
    start_date = str(date_range[0])
    end_date = str(date_range[1])

    # Filter sales based on selected date range and locations
    filtered_sales = get_sales_between_dates(
        sales_df=sales_df,
        start_date=datetime.strptime(start_date, '%Y-%m-%d').date(),
        end_date=datetime.strptime(end_date, '%Y-%m-%d').date(),
        locations=location_filter
    )

    # Filter products based on selected categories
    filtered_products = get_products_of_selected_categories(
        products_df=products_df,
        categories=category_filter
    )

    # Get products that are understocked
    understocked_products = get_under_stocked_products(
        products_df=filtered_products
    )

    # Calculate summary KPIs: Revenue, Profit, Units Sold, etc.
    key_metrics = get_summary_kpis(
        sales_df=filtered_sales,
        products_df=filtered_products,
    )

    # Show summary KPIs using Streamlit metrics
    revenue_col, profit_col, units_sold_col, low_stock_col = st.columns(4)

    with revenue_col:
        st.metric(
            label='Total Revenue (K)',
            value=f"{key_metrics['Total Revenue (K)']}"
        )
    with profit_col:
        st.metric(
            label='Total Profit (K)',
            value=f"{key_metrics['Total Profit (K)']}"
        )
    with units_sold_col:
        st.metric(
            label='Total Units Sold (K)',
            value=f"{key_metrics['Total Units Sold (K)']}"
        )
    with low_stock_col:
        st.metric(
            label='Total Low Stock Products',
            value=f"{key_metrics['Total Understocked Products']}"
        )

    # ---------------- Visualizations ---------------- #

    # Top 10 products by profit
    st.subheader("Top 10 Products by Profit")
    top_products = filtered_products.nlargest(10, 'profit')[['product_name', 'profit']]
    plot1 = px.bar(top_products, x='product_name', y='profit', title="Top 10 Products by Profit")
    st.plotly_chart(plot1, use_container_width=True)

    # Pie chart of profit by category
    st.subheader("Profit by Category")
    category_profit = filtered_products.groupby('category')['profit'].sum().reset_index()
    plot2 = px.pie(category_profit, values='profit', names='category', title="Profit Distribution by Category")
    st.plotly_chart(plot2, use_container_width=True)

    # ---------------- Tables ---------------- #

    # Display product stock and profit summary
    st.subheader("Product Stock and Profit Summary")
    summary_df = filtered_products[
        ['product_name', 'category', 'current_stock', 'reorder_level', 'profit', 'stock_status']]

    # Color-coding stock status
    summary_df['stock_status'] = summary_df['stock_status'].map({
        'Properly Stocked': '<span style="color:green">Properly Stocked</span>',
        'Understocked': '<span style="color:red">Understocked</span>',
        'Overstocked': '<span style="color:orange">Overstocked</span>'
    })

    # Render the summary table with HTML styling
    st.markdown(summary_df.to_html(escape=False), unsafe_allow_html=True)

    # Display understocked and overstocked product details
    st.subheader("Understocked and Overstocked Products")
    stock_issues = filtered_products[filtered_products['stock_status'].isin(['Understocked', 'Overstocked'])]
    stock_issues = stock_issues[['product_name', 'category', 'current_stock', 'reorder_level', 'stock_status']]
    stock_issues['suggested_reorder'] = np.where(
        stock_issues['stock_status'] == 'Understocked',
        stock_issues['reorder_level'] - stock_issues['current_stock'],
        0
    )
    st.markdown(stock_issues.to_html(escape=False), unsafe_allow_html=True)

    # ---------------- Download Button ---------------- #

    # Function to generate CSV download link for a DataFrame
    def get_table_download_link(df, filename):
        csv = df.to_csv(index=False)
        b64 = base64.b64encode(csv.encode()).decode()
        return f'<a href="data:file/csv;base64,{b64}" download="{filename}.csv">Download {filename}</a>'

    # Render download buttons
    st.markdown(get_table_download_link(summary_df, "product_summary"), unsafe_allow_html=True)
    st.markdown(get_table_download_link(stock_issues, "stock_issues"), unsafe_allow_html=True)

    # ---------------- Business Recommendations ---------------- #

    st.subheader("Business Recommendations")
    recommendations = []

    # Recommend restocking understocked items
    understocked = filtered_products[filtered_products['stock_status'] == 'Understocked']
    if not understocked.empty:
        recommendations.append(
            f"**Restock Urgently**: {len(understocked)} products are understocked. "
            f"Prioritize restocking {understocked['product_name'].iloc[:2].to_list()}."
        )

    # Recommend discontinuing slow-moving products
    slow_moving_products = filtered_products[filtered_products['slow_moving']]
    if not slow_moving_products.empty:
        recommendations.append(
            f"**Consider Discontinuing**: {len(slow_moving_products)} slow-moving products (e.g., "
            f"{slow_moving_products['product_name'].iloc[:2].to_list()}) have low sales."
        )

    # Recommend clearing overstocked items
    overstocked = filtered_products[filtered_products['stock_status'] == 'Overstocked']
    if not overstocked.empty:
        recommendations.append(
            f"**Clear Overstock**: {len(overstocked)} products are overstocked. Consider promotions for "
            f"{overstocked['product_name'].iloc[:2].to_list()} to reduce inventory costs."
        )

    # General inventory strategy advice
    recommendations.append(
        "**Inventory Strategy**: Implement just-in-time restocking for perishables and high-demand items "
        "to minimize waste and improve ROI."
    )

    # Display recommendations as bullet points
    for rec in recommendations:
        st.markdown(f"- {rec}")
