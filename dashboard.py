import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# Konfigurasi halaman
st.set_page_config(page_title="Superstore Analytics Dashboard", layout="wide", page_icon="📊")

# Load data dari 1 file Excel
@st.cache_data
def load_data():
    """Load data dari single Excel file"""
    try:
        # Load file
        df = pd.read_excel('superstore_order.xlsx')
        
        # Rename kolom: ganti spasi dengan underscore dan lowercase
        df.columns = df.columns.str.strip().str.replace(' ', '_').str.lower()
        
        # Convert numeric columns
        numeric_cols = ['sales', 'profit', 'quantity', 'discount']
        for col in numeric_cols:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors='coerce')
        
        # Convert date columns
        date_cols = ['order_date', 'ship_date']
        for col in date_cols:
            if col in df.columns:
                df[col] = pd.to_datetime(df[col], errors='coerce')
        
        st.sidebar.success(f"✅ Data loaded: {len(df):,} records")
        st.sidebar.info(f"📋 Columns: {len(df.columns)}")
        
        return df
    except Exception as e:
        st.error(f"Error loading data: {e}")
        st.info("📁 Pastikan file 'superstore_order.xlsx' ada di folder yang sama")
        import traceback
        st.code(traceback.format_exc())
        return None

# Load data
df = load_data()

if df is None:
    st.error("⚠️ Tidak dapat memuat data.")
    st.stop()

# Tampilkan kolom yang ada untuk debugging
with st.expander("🔍 Debug: Lihat Struktur Data"):
    st.write("**Kolom yang tersedia:**")
    st.write(list(df.columns))
    st.write("**Sample data (5 baris pertama):**")
    st.dataframe(df.head())

# Header Dashboard
st.title("📊 Superstore Analytics Dashboard")
st.markdown("---")

# Sidebar
st.sidebar.header("Dashboard Navigation")
view_option = st.sidebar.radio(
    "Pilih Analisis:",
    ["Overview", "Sales Analysis", "Customer Analysis", "Product Analysis", 
     "Shipping Performance", "Time Series Analysis"]
)

# OVERVIEW PAGE
if view_option == "Overview":
    st.header("📈 Business Overview")
    
    col1, col2, col3, col4 = st.columns(4)
    
    total_sales = df['sales'].sum()
    total_profit = df['profit'].sum()
    total_orders = df['order_id'].nunique()
    avg_order_value = total_sales / total_orders if total_orders > 0 else 0
    
    with col1:
        st.metric("Total Sales", f"${total_sales:,.2f}")
    
    with col2:
        st.metric("Total Profit", f"${total_profit:,.2f}")
    
    with col3:
        st.metric("Total Orders", f"{total_orders:,}")
    
    with col4:
        st.metric("Avg Order Value", f"${avg_order_value:,.2f}")
    
    st.markdown("---")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Sales by Region")
        if 'region' in df.columns:
            region_sales = df.groupby('region')['sales'].sum().reset_index()
            fig1 = px.pie(region_sales, values='sales', names='region', 
                         title='Distribution of Sales by Region',
                         color_discrete_sequence=px.colors.sequential.RdBu)
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("Kolom 'region' tidak ditemukan")
    
    with col2:
        st.subheader("🚚 Shipping Performance")
        if 'ship_mode' in df.columns and 'order_date' in df.columns and 'ship_date' in df.columns:
            df['shipping_days'] = (df['ship_date'] - df['order_date']).dt.days
            shipping = df.groupby('ship_mode')['shipping_days'].mean().reset_index()
            fig2 = px.bar(shipping, x='ship_mode', y='shipping_days',
                         title='Average Shipping Days by Mode',
                         color='shipping_days',
                         color_continuous_scale='Reds')
            fig2.update_layout(xaxis_title="Shipping Mode", yaxis_title="Days")
            st.plotly_chart(fig2, use_container_width=True)
        else:
            st.warning("Kolom shipping tidak lengkap")

# SALES ANALYSIS
elif view_option == "Sales Analysis":
    st.header("💼 Sales Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("📊 Top 10 Products by Sales")
        if 'product_name' in df.columns:
            top_products = df.groupby('product_name')['sales'].sum().sort_values(ascending=False).head(10).reset_index()
            fig1 = px.bar(top_products, x='sales', y='product_name',
                         orientation='h',
                         color='sales',
                         color_continuous_scale='Greens',
                         title='Top 10 Products')
            fig1.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig1, use_container_width=True)
        else:
            st.warning("Kolom 'product_name' tidak ditemukan")
    
    with col2:
        st.subheader("💰 Profit by Product")
        if 'product_name' in df.columns:
            top_profit = df.groupby('product_name')['profit'].sum().sort_values(ascending=False).head(10).reset_index()
            fig2 = px.bar(top_profit, x='profit', y='product_name',
                         orientation='h',
                         color='profit',
                         color_continuous_scale='Blues',
                         title='Top 10 by Profit')
            fig2.update_layout(yaxis={'categoryorder':'total ascending'})
            st.plotly_chart(fig2, use_container_width=True)
    
    # Sales vs Profit scatter
    st.subheader("📈 Sales vs Profit Analysis")
    if 'product_name' in df.columns:
        product_analysis = df.groupby('product_name').agg({
            'sales': 'sum',
            'profit': 'sum'
        }).reset_index()
        product_analysis['profit_margin'] = (product_analysis['profit'] / product_analysis['sales'] * 100).fillna(0)
        
        fig3 = px.scatter(product_analysis.head(50), x='sales', y='profit',
                         size='profit_margin',
                         hover_data=['product_name'],
                         title='Sales vs Profit (Top 50 Products)',
                         color='profit_margin',
                         color_continuous_scale='RdYlGn')
        st.plotly_chart(fig3, use_container_width=True)

# CUSTOMER ANALYSIS
elif view_option == "Customer Analysis":
    st.header("👥 Customer Analysis")
    
    if 'customer_name' in df.columns:
        customer_df = df.groupby('customer_name').agg({
            'order_id': 'nunique',
            'sales': 'sum',
            'profit': 'sum'
        }).reset_index()
        customer_df.columns = ['customer_name', 'total_orders', 'total_sales', 'total_profit']
        customer_df = customer_df.sort_values('total_sales', ascending=False).head(15)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("💎 Top 15 Customers by Sales")
            fig1 = px.bar(customer_df, x='customer_name', y='total_sales',
                         color='total_sales',
                         color_continuous_scale='Viridis',
                         title='Top Customers')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("🎯 Customer Purchase Frequency")
            fig2 = px.bar(customer_df, x='customer_name', y='total_orders',
                         color='total_orders',
                         color_continuous_scale='Blues',
                         title='Number of Orders')
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        
        # State analysis
        if 'state' in df.columns:
            st.subheader("🗺️ Sales by State (Top 10)")
            state_sales = df.groupby('state')['sales'].sum().sort_values(ascending=False).head(10).reset_index()
            fig3 = px.bar(state_sales, x='state', y='sales',
                         color='sales',
                         color_continuous_scale='Plasma',
                         title='Top 10 States by Sales')
            st.plotly_chart(fig3, use_container_width=True)
        
        st.dataframe(customer_df, use_container_width=True)
    else:
        st.warning("Kolom 'customer_name' tidak ditemukan")

# PRODUCT ANALYSIS
elif view_option == "Product Analysis":
    st.header("📦 Product Analysis")
    
    if 'quantity' in df.columns and 'product_name' in df.columns:
        product_qty = df.groupby('product_name').agg({
            'quantity': 'sum',
            'sales': 'sum',
            'profit': 'sum'
        }).reset_index()
        product_qty.columns = ['product_name', 'total_quantity', 'total_sales', 'total_profit']
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Top 15 Products by Quantity Sold")
            top_qty = product_qty.sort_values('total_quantity', ascending=False).head(15)
            fig1 = px.bar(top_qty, x='product_name', y='total_quantity',
                         color='total_quantity',
                         color_continuous_scale='Oranges',
                         title='Most Sold Products')
            fig1.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("🏷️ Discount Impact")
            if 'discount' in df.columns:
                discount_analysis = df.groupby('product_name').agg({
                    'discount': 'mean',
                    'profit': 'mean'
                }).reset_index()
                discount_analysis.columns = ['product_name', 'avg_discount', 'avg_profit']
                discount_analysis['avg_discount'] = (discount_analysis['avg_discount'] * 100).round(2)
                discount_analysis = discount_analysis.sort_values('avg_profit', ascending=False).head(15)
                
                fig2 = px.scatter(discount_analysis, x='avg_discount', y='avg_profit',
                                 hover_data=['product_name'],
                                 title='Discount vs Profit',
                                 labels={'avg_discount': 'Avg Discount (%)', 
                                        'avg_profit': 'Avg Profit ($)'})
                st.plotly_chart(fig2, use_container_width=True)
        
        st.dataframe(product_qty.sort_values('total_sales', ascending=False).head(20), use_container_width=True)
    else:
        st.warning("Data produk tidak lengkap")

# SHIPPING PERFORMANCE
elif view_option == "Shipping Performance":
    st.header("🚚 Shipping Performance Analysis")
    
    if 'ship_mode' in df.columns and 'order_date' in df.columns and 'ship_date' in df.columns:
        df['shipping_days'] = (df['ship_date'] - df['order_date']).dt.days
        
        shipping_df = df.groupby('ship_mode').agg({
            'order_id': 'count',
            'shipping_days': 'mean',
            'sales': 'sum'
        }).reset_index()
        shipping_df.columns = ['ship_mode', 'total_orders', 'avg_shipping_days', 'total_sales']
        shipping_df['avg_shipping_days'] = shipping_df['avg_shipping_days'].round(1)
        shipping_df = shipping_df.sort_values('avg_shipping_days')
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("⏱️ Average Shipping Days")
            fig1 = px.bar(shipping_df, x='ship_mode', y='avg_shipping_days',
                         color='avg_shipping_days',
                         color_continuous_scale='RdYlGn_r',
                         title='Delivery Speed by Shipping Mode',
                         text='avg_shipping_days')
            fig1.update_traces(texttemplate='%{text:.1f} days', textposition='outside')
            st.plotly_chart(fig1, use_container_width=True)
        
        with col2:
            st.subheader("📦 Order Distribution")
            fig2 = px.pie(shipping_df, values='total_orders', names='ship_mode',
                         title='Orders by Shipping Mode',
                         color_discrete_sequence=px.colors.sequential.Plasma)
            st.plotly_chart(fig2, use_container_width=True)
        
        st.subheader("💰 Sales by Shipping Mode")
        fig3 = px.bar(shipping_df, x='ship_mode', y='total_sales',
                     color='total_sales',
                     color_continuous_scale='Greens',
                     title='Revenue by Shipping Method')
        st.plotly_chart(fig3, use_container_width=True)
        
        st.dataframe(shipping_df, use_container_width=True)
    else:
        st.warning("Data shipping tidak lengkap")

# TIME SERIES ANALYSIS
elif view_option == "Time Series Analysis":
    st.header("📅 Time Series Analysis")
    
    if 'order_date' in df.columns:
        # Monthly trend
        df['year_month'] = df['order_date'].dt.to_period('M').astype(str)
        
        monthly_sales = df.groupby('year_month').agg({
            'sales': 'sum',
            'profit': 'sum',
            'order_id': 'nunique'
        }).reset_index()
        monthly_sales.columns = ['month', 'total_sales', 'total_profit', 'total_orders']
        
        st.subheader("📈 Monthly Sales & Profit Trend")
        fig1 = go.Figure()
        fig1.add_trace(go.Scatter(x=monthly_sales['month'], y=monthly_sales['total_sales'],
                                  mode='lines+markers', name='Sales',
                                  line=dict(color='blue', width=2)))
        fig1.add_trace(go.Scatter(x=monthly_sales['month'], y=monthly_sales['total_profit'],
                                  mode='lines+markers', name='Profit',
                                  line=dict(color='green', width=2)))
        fig1.update_layout(title='Sales & Profit Over Time',
                          xaxis_title='Month',
                          yaxis_title='Amount ($)',
                          hovermode='x unified')
        st.plotly_chart(fig1, use_container_width=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("📊 Monthly Order Count")
            fig2 = px.bar(monthly_sales, x='month', y='total_orders',
                         title='Orders per Month',
                         color='total_orders',
                         color_continuous_scale='Blues')
            fig2.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig2, use_container_width=True)
        
        with col2:
            st.subheader("💹 Profit Margin Trend")
            monthly_sales['profit_margin'] = (monthly_sales['total_profit'] / monthly_sales['total_sales'] * 100).round(2)
            fig3 = px.line(monthly_sales, x='month', y='profit_margin',
                          title='Profit Margin % Over Time',
                          markers=True)
            fig3.update_layout(xaxis_tickangle=-45)
            st.plotly_chart(fig3, use_container_width=True)
        
        st.dataframe(monthly_sales, use_container_width=True)
    else:
        st.warning("Kolom 'order_date' tidak ditemukan")

# Footer
st.markdown("---")
st.markdown("Dashboard created with Streamlit & Plotly | Data: Superstore Analytics")