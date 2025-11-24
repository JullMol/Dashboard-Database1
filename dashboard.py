import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Konfigurasi halaman
st.set_page_config(page_title="Superstore Analytics Dashboard", layout="wide", page_icon="📊")

# Load data dari Excel
@st.cache_data
def load_data():
    """Load data dari Excel files"""
    try:
        # Load files
        orders = pd.read_excel('superstore_order.xlsx')
        products = pd.read_excel('superstore_product.xlsx')
        customers = pd.read_excel('superstore_customer.xlsx')
        stock = pd.read_excel('product_stock.xlsx')
        
        # Debug: tampilkan kolom yang ada
        st.sidebar.write("📋 Kolom di superstore_order:", list(orders.columns))
        
        # Bersihkan nama kolom (hapus spasi dan lowercase)
        orders.columns = orders.columns.str.strip().str.lower()
        products.columns = products.columns.str.strip().str.lower()
        customers.columns = customers.columns.str.strip().str.lower()
        stock.columns = stock.columns.str.strip().str.lower()
        
        # Convert types dengan error handling
        if 'sales' in orders.columns:
            orders['sales'] = pd.to_numeric(orders['sales'], errors='coerce')
        if 'profit' in orders.columns:
            orders['profit'] = pd.to_numeric(orders['profit'], errors='coerce')
        if 'quantity' in orders.columns:
            orders['quantity'] = pd.to_numeric(orders['quantity'], errors='coerce')
        if 'discount' in orders.columns:
            orders['discount'] = pd.to_numeric(orders['discount'], errors='coerce')
        if 'order_date' in orders.columns:
            orders['order_date'] = pd.to_datetime(orders['order_date'], errors='coerce')
        if 'ship_date' in orders.columns:
            orders['ship_date'] = pd.to_datetime(orders['ship_date'], errors='coerce')
        
        return orders, products, customers, stock
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("📁 Pastikan file Excel (.xlsx) ada di folder yang sama dengan script")
        import traceback
        st.code(traceback.format_exc())
        return None, None, None, None

# Load data
orders, products, customers, stock = load_data()

if orders is None:
    st.error("⚠️ Tidak dapat memuat data. Pastikan file Excel ada di folder yang sama dengan script.")
    st.info("📁 File yang diperlukan: superstore_order.xlsx, superstore_product.xlsx, superstore_customer.xlsx, product_stock.xlsx")
    st.stop()

# Merge data dengan safe join
try:
    orders_full = orders.merge(products, on='product_id', how='left', suffixes=('', '_prod'))
    orders_full = orders_full.merge(customers, on='customer_id', how='left', suffixes=('', '_cust'))
except Exception as e:
    st.error(f"Error merging data: {e}")
    st.info("Cek apakah kolom 'product_id' dan 'customer_id' ada di semua file")
    st.stop()

# Header Dashboard
st.title("📊 Superstore Analytics Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("Dashboard Navigation")
view_option = st.sidebar.radio(
    "Pilih Analisis:",
    ["Overview", "Profitability Analysis", "Customer Analysis", "Inventory Management", 
     "Discount Impact", "Shipping Performance", "Premium Customers"]
)

# OVERVIEW PAGE
if view_option == "Overview":
    st.header("📈 Business Overview")
    
    col1, col2, col3 = st.columns(3)
    
    total_sales = orders_full['sales'].sum()
    total_profit = orders_full['profit'].sum()
    avg_margin = (total_profit / total_sales * 100) if total_sales > 0 else 0
    
    with col1:
        st.metric("Total Sales", f"${total_sales:,.2f}")
    
    with col2:
        st.metric("Total Profit", f"${total_profit:,.2f}")
    
    with col3:
        st.metric("Avg Profit Margin", f"{avg_margin:.2f}%")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Sales by Category")
        category_sales = orders_full.groupby('category')['sales'].sum().reset_index()
        fig1 = px.pie(category_sales, values='sales', names='category', 
                     title='Distribution of Sales',
                     color_discrete_sequence=px.colors.sequential.RdBu)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("🚚 Shipping Performance")
        orders_full['shipping_days'] = (orders_full['ship_date'] - orders_full['order_date']).dt.days
        shipping = orders_full.groupby('ship_mode')['shipping_days'].mean().reset_index()
        fig2 = px.bar(shipping, x='ship_mode', y='shipping_days',
                     title='Average Shipping Days by Mode',
                     color='shipping_days',
                     color_continuous_scale='Reds')
        fig2.update_layout(xaxis_title="Shipping Mode", yaxis_title="Days")
        st.plotly_chart(fig2, use_container_width=True)

# PROFITABILITY ANALYSIS
elif view_option == "Profitability Analysis":
    st.header("💼 Profitability Analysis by Category & Sub-Category")
    
    df = orders_full.groupby(['category', 'sub_category']).agg({
        'sales': 'sum',
        'profit': 'sum'
    }).reset_index()
    df.columns = ['category', 'sub_category', 'total_sales', 'total_profit']
    df['profit_margin_percentage'] = (df['total_profit'] / df['total_sales'] * 100).round(2)
    df = df.sort_values('total_profit', ascending=False)
    
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
    
    st.subheader("📊 Sales vs Profit Analysis")
    df_scatter = df.copy()
    df_scatter['profit_margin_percentage'] = df_scatter['profit_margin_percentage'].fillna(0).abs()
    fig3 = px.scatter(df_scatter, x='total_sales', y='total_profit',
                     size='profit_margin_percentage',
                     color='category',
                     hover_data=['sub_category'],
                     title='Sales vs Profit by Sub-Category')
    st.plotly_chart(fig3, use_container_width=True)
    
    st.subheader("📋 Detailed Data")
    st.dataframe(df, use_container_width=True)

# CUSTOMER ANALYSIS
elif view_option == "Customer Analysis":
    st.header("👥 Customer Analysis")
    
    df = orders_full.groupby(['customer_name', 'segment']).agg({
        'order_id': 'nunique',
        'sales': 'sum'
    }).reset_index()
    df.columns = ['customer_name', 'segment', 'total_orders', 'total_spend']
    df = df.sort_values('total_spend', ascending=False).head(10)
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💎 Top 10 Customers by Total Spend")
        fig1 = px.bar(df, x='customer_name', y='total_spend',
                     color='segment',
                     title='Top Customers')
        fig1.update_layout(xaxis_tickangle=-45)
        st.plotly_chart(fig1, use_container_width=True)
    
    with col2:
        st.subheader("🎯 Customer Segments Distribution")
        segment_data = df.groupby('segment')['total_spend'].sum().reset_index()
        fig2 = px.pie(segment_data, values='total_spend', names='segment',
                     title='Spend by Segment',
                     color_discrete_sequence=px.colors.sequential.Blues_r)
        st.plotly_chart(fig2, use_container_width=True)
    
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

# INVENTORY MANAGEMENT
elif view_option == "Inventory Management":
    st.header("📦 Inventory & Stock Management")
    
    df = stock.merge(
        orders_full.groupby('product_id')['quantity'].sum().reset_index(),
        on='product_id',
        how='left'
    )
    df['quantity'] = df['quantity'].fillna(0)
    df.columns = ['product_id', 'category', 'sub_category', 'product_name', 'current_stock', 'total_units_sold']
    df = df.sort_values('current_stock').head(15)
    
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
    
    st.dataframe(df, use_container_width=True)

# DISCOUNT IMPACT
elif view_option == "Discount Impact":
    st.header("🏷️ Discount Impact on Profitability")
    
    df = orders_full.groupby(['category', 'sub_category']).agg({
        'discount': 'mean',
        'profit': 'mean'
    }).reset_index()
    df.columns = ['category', 'sub_category', 'avg_discount_percentage', 'avg_profit_per_item']
    df['avg_discount_percentage'] = (df['avg_discount_percentage'] * 100).round(2)
    df['avg_profit_per_item'] = df['avg_profit_per_item'].round(2)
    df = df.sort_values('avg_profit_per_item', ascending=False)
    
    st.subheader("💡 Discount vs Profit Analysis")
    
    df_scatter = df.copy()
    df_scatter['avg_profit_per_item'] = df_scatter['avg_profit_per_item'].fillna(0).abs()
    df_scatter = df_scatter[df_scatter['avg_profit_per_item'] > 0]
    
    fig1 = px.scatter(df_scatter, x='avg_discount_percentage', y='avg_profit_per_item',
                     size='avg_profit_per_item',
                     color='category',
                     hover_data=['sub_category'],
                     title='Impact of Discounts on Profit')
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

# SHIPPING PERFORMANCE
elif view_option == "Shipping Performance":
    st.header("🚚 Shipping Performance Analysis")
    
    orders_full['shipping_days'] = (orders_full['ship_date'] - orders_full['order_date']).dt.days
    df = orders_full.groupby('ship_mode').agg({
        'order_id': 'count',
        'shipping_days': 'mean'
    }).reset_index()
    df.columns = ['ship_mode', 'total_orders', 'avg_shipping_days']
    df['avg_shipping_days'] = df['avg_shipping_days'].round(1)
    df = df.sort_values('avg_shipping_days')
    
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
    
    st.dataframe(df, use_container_width=True)

# PREMIUM CUSTOMERS
elif view_option == "Premium Customers":
    st.header("⭐ Premium Customer Analysis")
    st.markdown("*Customers with more than 5 transactions*")
    
    df = orders_full.groupby('customer_name').agg({
        'order_id': 'nunique',
        'sales': ['sum', 'mean']
    }).reset_index()
    df.columns = ['customer_name', 'total_transactions', 'total_spent', 'avg_sales_per_item']
    df = df[df['total_transactions'] > 5]
    df['avg_sales_per_item'] = df['avg_sales_per_item'].round(2)
    df = df.sort_values('total_spent', ascending=False).head(15)
    
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
    
    st.subheader("📈 Customer Purchase Patterns")
    df_scatter = df.copy()
    df_scatter['avg_sales_per_item'] = df_scatter['avg_sales_per_item'].fillna(1)
    df_scatter = df_scatter[df_scatter['avg_sales_per_item'] > 0]
    
    fig3 = px.scatter(df_scatter, x='total_transactions', y='total_spent',
                     size='avg_sales_per_item',
                     hover_data=['customer_name'],
                     title='Transaction Frequency vs Total Spend')
    st.plotly_chart(fig3, use_container_width=True)
    
    st.dataframe(df, use_container_width=True)

# Footer
st.markdown("---")
st.markdown("Dashboard created with Streamlit & Plotly | Data: Superstore Excel Files")