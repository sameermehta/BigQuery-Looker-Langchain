import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime, timedelta
import random

st.set_page_config(page_title="Agentic AI Churn Prediction System", layout="wide")

st.title("🤖 Agentic AI Churn Prediction System")
st.markdown("### Modern, Interactive Demo Dashboard")

# Generate demo data
@st.cache_data
def generate_data():
    customers = []
    for i in range(100):
        customer = {
            'customer_id': f'CUST{i+1:03d}',
            'customer_name': f'Company {i+1}',
            'monthly_revenue': random.randint(1000, 10000),
            'churn_probability': random.uniform(0, 1),
            'risk_level': random.choice(['Low', 'Medium', 'High']),
            'status': random.choice(['Active', 'At Risk', 'Critical'])
        }
        customers.append(customer)
    return customers

customers = generate_data()
df = pd.DataFrame(customers)

# Sidebar controls
with st.sidebar:
    st.header("��️ Control Panel")
    
    if st.button("🔄 Refresh Data"):
        st.cache_data.clear()
        st.rerun()
    
    if st.button("🚀 Simulate Analysis"):
        with st.spinner("Running AI analysis..."):
            st.success("Analysis completed!")

# Main dashboard
col1, col2, col3, col4 = st.columns(4)

with col1:
    st.metric("Total Customers", len(customers))
with col2:
    st.metric("At Risk", len([c for c in customers if c['risk_level'] == 'High']))
with col3:
    st.metric("Monthly Revenue", f"${sum(c['monthly_revenue'] for c in customers):,.0f}")
with col4:
    st.metric("Avg Churn Risk", f"{df['churn_probability'].mean():.1%}")

# Charts
col1, col2 = st.columns(2)

with col1:
    st.subheader("📊 Churn Risk Distribution")
    fig = px.histogram(df, x='churn_probability', color='risk_level', 
                      title="Customer Churn Risk Distribution")
    st.plotly_chart(fig, use_container_width=True)

with col2:
    st.subheader("💰 Revenue by Risk Level")
    risk_revenue = df.groupby('risk_level')['monthly_revenue'].sum()
    fig = px.pie(values=risk_revenue.values, names=risk_revenue.index, 
                 title="Revenue Distribution by Risk Level")
    st.plotly_chart(fig, use_container_width=True)

# Customer details
st.subheader("👥 Customer Details")
selected_customer = st.selectbox("Select Customer", 
                                [f"{c['customer_id']} - {c['customer_name']}" for c in customers])

if selected_customer:
    customer_id = selected_customer.split(" - ")[0]
    customer = next(c for c in customers if c['customer_id'] == customer_id)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.info(f"**Customer ID:** {customer['customer_id']}")
    with col2:
        st.warning(f"**Risk Level:** {customer['risk_level']}")
    with col3:
        st.success(f"**Revenue:** ${customer['monthly_revenue']:,.0f}")

st.markdown("---")
st.markdown("**Built with Streamlit, Plotly, and modern design principles**")
