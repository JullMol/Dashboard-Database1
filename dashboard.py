import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import psycopg2
from datetime import datetime

# Konfigurasi halaman
st.set_page_config(page_title="Superstore Analytics Dashboard", layout="wide", page_icon="📊")

# Fungsi koneksi database
@st.cache_resource
def get_connection():
    """Koneksi database menggunakan Streamlit secrets atau environment variables"""
    try:
        # Untuk Streamlit Cloud, gunakan secrets
        if 'postgres' in st.secrets:
            return psycopg2.connect(
                host=st.secrets["postgres"]["host"],
                database=st.secrets["postgres"]["database"],
                user=st.secrets["postgres"]["user"],
                password=st.secrets["postgres"]["password"],
                port=st.secrets["postgres"].get("port", 5432)
            )
        else:
            # Untuk development lokal
            return psycopg2.connect(
                host="localhost",
                database="superstore",
                user="postgres",
                password="rafizzul00"
            )
    except Exception as e:
        st.error(f"Database connection error: {e}")
        st.info("💡 Pastikan database credentials sudah dikonfigurasi di Streamlit Secrets")
        return None

# Fungsi untuk menjalankan query
@st.cache_data(ttl=600)
def run_query(query):
    conn = get_connection()
    if conn is None:
        return pd.DataFrame()  # Return empty dataframe jika koneksi gagal
    try:
        df = pd.read_sql_query(query, conn)
        return df
    except Exception as e:
        st.error(f"Query error: {e}")
        return pd.DataFrame()

# Header Dashboard
st.title("📊 Superstore Analytics Dashboard")
st.markdown("---")

# Sidebar untuk filter (opsional)
st.sidebar.header("Dashboard Navigation")
view_option = st.sidebar.radio(
    "Pilih Analisis:",
    ["Overview", "Profitability Analysis", "Customer Analysis", "Inventory Management", 
     "Discount Impact", "Shipping Performance", "Premium Customers"]
)

# QUERY DEFINITIONS
queries = {
    "profit_by_category": """
        SELECT
            sp.category,
            sp.sub_category,
            SUM(so.sales::NUMERIC) AS total_sales,
            SUM(so.profit::NUMERIC) AS total_profit,
            ROUND((SUM(so.profit::NUMERIC) / SUM(so.sales::NUMERIC)) * 100, 2) AS profit_margin_percentage
        FROM superstore_order so
        JOIN superstore_product sp ON so.product_id = sp.product_id
        GROUP BY sp.category, sp.sub_category
        ORDER BY total_profit DESC;
    """,
    "top_customers": """
        SELECT 
            sc.customer_name, 
            sc.segment,
            COUNT(DISTINCT so.order_id) AS total_orders,
            SUM(so.sales::NUMERIC) AS total_spend
        FROM superstore_order so
        JOIN superstore_customer sc ON so.customer_id = sc.customer_id
        GROUP BY sc.customer_name, sc.segment
        ORDER BY total_spend DESC
        LIMIT 10;
    """,
    "inventory_stock": """
        SELECT
            ps.product_name,
            ps.stock AS current_stock,
            COALESCE(SUM(so.quantity::NUMERIC), 0) AS total_units_sold
        FROM product_stock ps
        LEFT JOIN superstore_order so ON ps.product_id = so.product_id
        GROUP BY ps.product_id, ps.product_name, ps.stock
        ORDER BY ps.stock ASC
        LIMIT 15;
    """,
    "discount_analysis": """
        SELECT 
            sp.category,
            sp.sub_category,
            ROUND(AVG(so.discount::NUMERIC) * 100, 2) AS avg_discount_percentage,
            ROUND(AVG(so.profit::NUMERIC), 2) AS avg_profit_per_item
        FROM superstore_order so
        JOIN superstore_product sp ON so.product_id = sp.product_id
        GROUP BY sp.category, sp.sub_category
        ORDER BY avg_profit_per_item DESC;
    """,
    "shipping_performance": """
        SELECT 
            ship_mode,
            COUNT(order_id) AS total_orders,
            ROUND(AVG(ship_date::DATE - order_date::DATE), 1) AS avg_shipping_days
        FROM superstore_order
        GROUP BY ship_mode
        ORDER BY avg_shipping_days ASC;
    """,
    "premium_customers": """
        SELECT 
            customer_name,
            COUNT(DISTINCT order_id) AS total_transactions,
            SUM(sales::NUMERIC) AS total_spent,
            ROUND(AVG(sales::NUMERIC), 2) AS avg_sales_per_item 
        FROM superstore_order
        GROUP BY customer_name
        HAVING COUNT(DISTINCT order_id) > 5 
        ORDER BY total_spent DESC
        LIMIT 15;
    """
}

# OVERVIEW PAGE
if view_option == "Overview":
    st.header("📈 Business Overview")
    
    col1, col2, col3 = st.columns(3)
    
    # Load data untuk metrics
    try:
        df_profit = run_query(queries["profit_by_category"])
        df_customers = run_query(queries["top_customers"])
        df_shipping = run_query(queries["shipping_performance"])
        
        with col1:
            total_sales = df_profit['total_sales'].sum()
            st.metric("Total Sales", f"${total_sales:,.2f}")
        
        with col2:
            total_profit = df_profit['total_profit'].sum()
            st.metric("Total Profit", f"${total_profit:,.2f}")
        
        with col3:
            avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
            st.metric("Avg Profit Margin", f"{avg_margin:.2f}%")
        
        st.markdown("---")
        
        # Chart: Sales by Category
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💰 Sales by Category")
            category_sales = df_profit.groupby('category')['total_sales'].sum().reset_index()
            fig1 = px.pie(category_sales, values='total_sales', names='category', 
                         title='Distribution of Sales',
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("🚚 Shipping Performance")
            fig2 = px.bar(df_shipping, x='ship_mode', y='avg_shipping_days',
                         title='Average Shipping Days by Mode',
                         color='avg_shipping_days',
                         color_continuous_scale='Reds')
            fig2.update_layout(xaxis_title="Shipping Mode", yaxis_title="Days")
            st.plotly_chart(fig2, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error loading overview data: {e}")

# PROFITABILITY ANALYSIS
elif view_option == "Profitability Analysis":
    st.header("💼 Profitability Analysis by Category & Sub-Category")
    
    try:
        df = run_query(queries["profit_by_category"])
        
        # Top 10 Sub-Categories by Profit
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("🏆 Top 10 Most Profitable Sub-Categories")
            top10 = df.head(10)
            fig1 = px.bar(top10, x='total_profit', y='sub_category',
                         orientation='h',
                         color='profit_margin_percentage',
                         color_continuous_scale='Greens',
                         title='Top 10 by Total Profit')
            fig1.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("📉 Bottom 10 Least Profitable Sub-Categories")
            bottom10 = df.tail(10)
            fig2 = px.bar(bottom10, x='total_profit', y='sub_category',
                         orientation='h',
                         color='total_profit',
                         color_continuous_scale='Reds',
                         title='Bottom 10 by Total Profit')
            fig2.update_layout(yaxis={'categoryorder':'total descending'})
            st.plotly_chart(fig2, use_container_width=True)
        
        # Scatter Plot: Sales vs Profit
        st.subheader("📊 Sales vs Profit Analysis")
        df_scatter = df.copy()
        df_scatter['profit_margin_percentage'] = df_scatter['profit_margin_percentage'].fillna(0).abs()
        fig3 = px.scatter(df_scatter, x='total_sales', y='total_profit',
                         size='profit_margin_percentage',
                         color='category',
                         hover_data=['sub_category'],
                         title='Sales vs Profit by Sub-Category',
                         labels={'total_sales': 'Total Sales ($)', 
                                'total_profit': 'Total Profit ($)'})
        st.plotly_chart(fig3, use_container_width=True)
        
        # Data Table
        st.subheader("📋 Detailed Data")
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {e}")

# CUSTOMER ANALYSIS
elif view_option == "Customer Analysis":
    st.header("👥 Customer Analysis")
    
    try:
        df = run_query(queries["top_customers"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💎 Top 10 Customers by Total Spend")
            fig1 = px.bar(df, x='customer_name', y='total_spend',
                         color='segment',
                         title='Top Customers',
                         labels={'total_spend': 'Total Spend ($)', 
                                'customer_name': 'Customer'})
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Customer Segments Distribution")
            segment_data = df.groupby('segment')['total_spend'].sum().reset_index()
            fig2 = px.pie(segment_data, values='total_spend', names='segment',
                         title='Spend by Segment',
                         color_discrete_sequence=px.colors.sequential.Blues_r)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Orders vs Spend
        st.subheader("📦 Orders vs Total Spend")
        df_scatter = df.copy()
        df_scatter['total_spend'] = df_scatter['total_spend'].fillna(1)
        fig3 = px.scatter(df_scatter, x='total_orders', y='total_spend',
                         size='total_spend',
                         color='segment',
                         hover_data=['customer_name'],
                         title='Customer Purchase Behavior')
        st.plotly_chart(fig3, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {e}")

# INVENTORY MANAGEMENT
elif view_option == "Inventory Management":
    st.header("📦 Inventory & Stock Management")
    
    try:
        df = run_query(queries["inventory_stock"])
        
        st.subheader("⚠️ Low Stock Alert - Top 15 Products")
        
        col1, col2 = st.columns(2)
        
        with col1:
            fig1 = px.bar(df, x='product_name', y='current_stock',
                         color='current_stock',
                         color_continuous_scale='Reds_r',
                         title='Current Stock Levels')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            fig2 = px.bar(df, x='product_name', y='total_units_sold',
                         color='total_units_sold',
                         color_continuous_scale='Blues',
                         title='Total Units Sold')
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Stock vs Sold Comparison
        st.subheader("📊 Stock vs Sales Comparison")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name='Current Stock', x=df['product_name'], 
                             y=df['current_stock'], marker_color='indianred'))
        fig3.add_trace(go.Bar(name='Units Sold', x=df['product_name'], 
                             y=df['total_units_sold'], marker_color='lightsalmon'))
        fig3.update_layout(barmode='group', xaxis_tickangle=-45)
        st.plotly_chart(fig3, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {e}")

# DISCOUNT IMPACT
elif view_option == "Discount Impact":
    st.header("🏷️ Discount Impact on Profitability")
    
    try:
        df = run_query(queries["discount_analysis"])
        
        st.subheader("💡 Discount vs Profit Analysis")
        
        # Scatter plot dengan handling NaN
        df_scatter = df.copy()
        df_scatter['avg_profit_per_item'] = df_scatter['avg_profit_per_item'].fillna(0).abs()
        df_scatter = df_scatter[df_scatter['avg_profit_per_item'] > 0]  # Hapus nilai 0
        
        fig1 = px.scatter(df_scatter, x='avg_discount_percentage', y='avg_profit_per_item',
                         size='avg_profit_per_item',
                         color='category',
                         hover_data=['sub_category'],
                         title='Impact of Discounts on Profit',
                         labels={'avg_discount_percentage': 'Average Discount (%)',
                                'avg_profit_per_item': 'Average Profit per Item ($)'})
        st.plotly_chart(fig1, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📈 Average Discount by Category")
            category_discount = df.groupby('category')['avg_discount_percentage'].mean().reset_index()
            fig2 = px.bar(category_discount, x='category', y='avg_discount_percentage',
                         color='avg_discount_percentage',
                         color_continuous_scale='Oranges',
                         title='Discount Levels by Category')
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            st.subheader("💰 Average Profit by Category")
            category_profit = df.groupby('category')['avg_profit_per_item'].mean().reset_index()
            fig3 = px.bar(category_profit, x='category', y='avg_profit_per_item',
                         color='avg_profit_per_item',
                         color_continuous_scale='Greens',
                         title='Profit Levels by Category')
            st.plotly_chart(fig3, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {e}")

# SHIPPING PERFORMANCE
elif view_option == "Shipping Performance":
    st.header("🚚 Shipping Performance Analysis")
    
    try:
        df = run_query(queries["shipping_performance"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⏱️ Average Shipping Days")
            fig1 = px.bar(df, x='ship_mode', y='avg_shipping_days',
                         color='avg_shipping_days',
                         color_continuous_scale='RdYlGn_r',
                         title='Delivery Speed by Shipping Mode')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("📦 Order Volume by Shipping Mode")
            fig2 = px.pie(df, values='total_orders', names='ship_mode',
                         title='Distribution of Orders',
                         color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Comparison chart
        st.subheader("📊 Shipping Mode Comparison")
        fig3 = go.Figure()
        fig3.add_trace(go.Bar(name='Total Orders', x=df['ship_mode'], 
                             y=df['total_orders'], yaxis='y', offsetgroup=1))
        fig3.add_trace(go.Scatter(name='Avg Days', x=df['ship_mode'], 
                                 y=df['avg_shipping_days'], yaxis='y2', 
                                 mode='lines+markers', marker=dict(size=10)))
        
        fig3.update_layout(
            yaxis=dict(title='Total Orders'),
            yaxis2=dict(title='Average Days', overlaying='y', side='right')
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {e}")

# PREMIUM CUSTOMERS
elif view_option == "Premium Customers":
    st.header("⭐ Premium Customer Analysis")
    st.markdown("*Customers with more than 5 transactions*")
    
    try:
        df = run_query(queries["premium_customers"])
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💎 Top Spenders")
            fig1 = px.bar(df.head(10), x='customer_name', y='total_spent',
                         color='avg_sales_per_item',
                         color_continuous_scale='Viridis',
                         title='Top 10 Premium Customers by Total Spend')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Transaction Frequency")
            fig2 = px.bar(df.head(10), x='customer_name', y='total_transactions',
                         color='total_transactions',
                         color_continuous_scale='Blues',
                         title='Top 10 by Transaction Count')
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Scatter: Transactions vs Spend
        st.subheader("📈 Customer Purchase Patterns")
        df_scatter = df.copy()
        df_scatter['avg_sales_per_item'] = df_scatter['avg_sales_per_item'].fillna(1)
        df_scatter = df_scatter[df_scatter['avg_sales_per_item'] > 0]
        
        fig3 = px.scatter(df_scatter, x='total_transactions', y='total_spent',
                         size='avg_sales_per_item',
                         hover_data=['customer_name'],
                         title='Transaction Frequency vs Total Spend',
                         labels={'total_transactions': 'Number of Transactions',
                                'total_spent': 'Total Spent ($)'})
        st.plotly_chart(fig3, use_container_width=True)
        
        st.dataframe(df, use_container_width=True)
        
    except Exception as e:
        st.error(f"Error: {e}")

# Footer
st.markdown("---")
st.markdown("Dashboard created with Streamlit & Plotly | Data: Superstore Database")