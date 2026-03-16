import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import json
import os

# Configure page
st.set_page_config(
    page_title="Expense Tracker",
    page_icon="💰",
    layout="wide"
)

# Initialize session state for expenses
if 'expenses' not in st.session_state:
    st.session_state.expenses = []

# File to persist data
DATA_FILE = 'expenses.json'

# Expense categories
CATEGORIES = [
    "Food & Dining",
    "Transportation",
    "Shopping",
    "Entertainment",
    "Bills & Utilities",
    "Healthcare",
    "Education",
    "Travel",
    "Other"
]

# Load data from file if exists
def load_data():
    if os.path.exists(DATA_FILE):
        try:
            with open(DATA_FILE, 'r') as f:
                data = json.load(f)
                st.session_state.expenses = data
        except:
            st.session_state.expenses = []

# Save data to file
def save_data():
    with open(DATA_FILE, 'w') as f:
        json.dump(st.session_state.expenses, f, default=str)

# Load data on startup
if 'data_loaded' not in st.session_state:
    load_data()
    st.session_state.data_loaded = True

# Title and description
st.title("💰 Simple Expense Tracker")
st.markdown("Track your expenses, categorize them, and visualize your spending patterns.")

# Sidebar for adding new expense
with st.sidebar:
    st.header("+ Add New Expense")
    
    with st.form("expense_form"):
        description = st.text_input("Description", placeholder="e.g., Grocery shopping")
        amount = st.number_input("Amount ($)", min_value=0.01, step=0.01)
        category = st.selectbox("Category", CATEGORIES)
        date = st.date_input("Date", value=datetime.now())
        notes = st.text_area("Notes (optional)", placeholder="Additional details...")
        
        submitted = st.form_submit_button("Add Expense", use_container_width=True)
        
        if submitted:
            if description and amount > 0:
                expense = {
                    "id": datetime.now().timestamp(),
                    "description": description,
                    "amount": amount,
                    "category": category,
                    "date": str(date),
                    "notes": notes,
                    "timestamp": datetime.now().isoformat()
                }
                st.session_state.expenses.append(expense)
                save_data()
                st.success("✅ Expense added successfully!")
                st.rerun()
            else:
                st.error("Please enter description and amount")


if st.session_state.expenses:
    df = pd.DataFrame(st.session_state.expenses)
    df['date'] = pd.to_datetime(df['date'])
    df['amount'] = pd.to_numeric(df['amount'])
    
    # Filters section
    st.header("🔍 Filters")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        # Date range filter
        date_range = st.date_input(
            "Select Date Range",
            value=(df['date'].min().date(), df['date'].max().date()),
            max_value=datetime.now().date(),
            key="date_filter"
        )
    
    with col2:
        # Category filter
        selected_categories = st.multiselect(
            "Categories",
            options=CATEGORIES,
            default=CATEGORIES,
            key="category_filter"
        )
    
    with col3:
        # Quick date filters
        quick_filter = st.selectbox(
            "Quick Filters",
            ["All Time", "Today", "Last 7 Days", "Last 30 Days", "This Month", "Last Month"]
        )
        
        # Apply quick filter
        if quick_filter == "Today":
            date_range = (datetime.now().date(), datetime.now().date())
        elif quick_filter == "Last 7 Days":
            date_range = ((datetime.now() - timedelta(days=7)).date(), datetime.now().date())
        elif quick_filter == "Last 30 Days":
            date_range = ((datetime.now() - timedelta(days=30)).date(), datetime.now().date())
        elif quick_filter == "This Month":
            date_range = (datetime.now().replace(day=1).date(), datetime.now().date())
        elif quick_filter == "Last Month":
            last_month = datetime.now().replace(day=1) - timedelta(days=1)
            date_range = (last_month.replace(day=1).date(), last_month.date())
    
    # Apply filters
    if len(date_range) == 2:
        filtered_df = df[
            (df['date'].dt.date >= date_range[0]) & 
            (df['date'].dt.date <= date_range[1]) &
            (df['category'].isin(selected_categories))
        ].copy()
    else:
        filtered_df = df[df['category'].isin(selected_categories)].copy()
    
    # Dashboard Summary
    st.header("📊 Dashboard")
    
    # Key metrics
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        total_expenses = filtered_df['amount'].sum()
        st.metric("Total Expenses", f"${total_expenses:,.2f}")
    
    with col2:
        avg_expense = filtered_df['amount'].mean() if len(filtered_df) > 0 else 0
        st.metric("Average Expense", f"${avg_expense:,.2f}")
    
    with col3:
        num_transactions = len(filtered_df)
        st.metric("Transactions", num_transactions)
    
    with col4:
        if len(filtered_df) > 0:
            top_category = filtered_df.groupby('category')['amount'].sum().idxmax()
            st.metric("Top Category", top_category)
        else:
            st.metric("Top Category", "N/A")
    
    # Charts
    if len(filtered_df) > 0:
        col1, col2 = st.columns(2)
        
        with col1:
            # Pie chart for category distribution
            category_summary = filtered_df.groupby('category')['amount'].sum().reset_index()
            fig_pie = px.pie(
                category_summary, 
                values='amount', 
                names='category',
                title="Expenses by Category",
                hole=0.4
            )
            fig_pie.update_traces(textposition='inside', textinfo='percent+label')
            st.plotly_chart(fig_pie, use_container_width=True)
        
        with col2:
            # Bar chart for daily expenses
            daily_expenses = filtered_df.groupby(filtered_df['date'].dt.date)['amount'].sum().reset_index()
            fig_bar = px.bar(
                daily_expenses,
                x='date',
                y='amount',
                title="Daily Expenses",
                labels={'amount': 'Amount ($)', 'date': 'Date'}
            )
            st.plotly_chart(fig_bar, use_container_width=True)
        
        # Category summary table
        st.subheader("📈 Category Summary")
        category_stats = filtered_df.groupby('category').agg({
            'amount': ['sum', 'mean', 'count']
        }).round(2)
        category_stats.columns = ['Total ($)', 'Average ($)', 'Count']
        category_stats = category_stats.sort_values('Total ($)', ascending=False)
        
        st.dataframe(category_stats, use_container_width=True)
    
    # Detailed expense table
    st.header("📋 Expense Details")
    
    # Sorting options
    col1, col2, col3 = st.columns([2, 2, 8])
    with col1:
        sort_by = st.selectbox("Sort by", ["Date", "Amount", "Category"])
    with col2:
        sort_order = st.selectbox("Order", ["Descending", "Ascending"])
    
    # Apply sorting
    ascending = sort_order == "Ascending"
    if sort_by == "Date":
        filtered_df = filtered_df.sort_values('date', ascending=ascending)
    elif sort_by == "Amount":
        filtered_df = filtered_df.sort_values('amount', ascending=ascending)
    else:
        filtered_df = filtered_df.sort_values('category', ascending=ascending)
    
    # Display expense table with delete functionality
    if len(filtered_df) > 0:
        display_df = filtered_df[['date', 'description', 'category', 'amount', 'notes']].copy()
        display_df['date'] = display_df['date'].dt.strftime('%Y-%m-%d')
        display_df['amount'] = display_df['amount'].apply(lambda x: f"${x:,.2f}")
        
        st.dataframe(
            display_df,
            use_container_width=True,
            hide_index=True,
            column_config={
                "date": "Date",
                "description": "Description",
                "category": "Category",
                "amount": "Amount",
                "notes": "Notes"
            }
        )
        
        # Delete expenses section
        with st.expander("🗑️ Delete Expenses"):
            expense_to_delete = st.selectbox(
                "Select expense to delete",
                options=range(len(filtered_df)),
                format_func=lambda x: f"{filtered_df.iloc[x]['date'].strftime('%Y-%m-%d')} - {filtered_df.iloc[x]['description']} - ${filtered_df.iloc[x]['amount']:.2f}"
            )
            
            if st.button("Delete Selected Expense", type="secondary"):
                expense_id = filtered_df.iloc[expense_to_delete]['id']
                st.session_state.expenses = [e for e in st.session_state.expenses if e['id'] != expense_id]
                save_data()
                st.success("Expense deleted!")
                st.rerun()
        
        # Export functionality
        st.download_button(
            label="📥 Download as CSV",
            data=display_df.to_csv(index=False),
            file_name=f"expenses_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
            mime="text/csv"
        )
    else:
        st.info("No expenses found for the selected filters.")
    
else: # No expenses yet
   
    st.info("Start by adding your first expense using the sidebar or load the sample data below")

    if st.button("Load Sample Data"): # Sample data button for testing
        sample_expenses = [
            {"id": 1, "description": "Grocery Store", "amount": 85.50, "category": "Food & Dining", "date": (datetime.now() - timedelta(days=1)).strftime('%Y-%m-%d'), "notes": "Weekly groceries", "timestamp": datetime.now().isoformat()},
            {"id": 2, "description": "Gas Station", "amount": 45.00, "category": "Transportation", "date": (datetime.now() - timedelta(days=2)).strftime('%Y-%m-%d'), "notes": "Full tank", "timestamp": datetime.now().isoformat()},
            {"id": 3, "description": "Restaurant", "amount": 32.75, "category": "Food & Dining", "date": (datetime.now() - timedelta(days=3)).strftime('%Y-%m-%d'), "notes": "Dinner with friends", "timestamp": datetime.now().isoformat()},
            {"id": 4, "description": "Electric Bill", "amount": 120.00, "category": "Bills & Utilities", "date": (datetime.now() - timedelta(days=5)).strftime('%Y-%m-%d'), "notes": "Monthly payment", "timestamp": datetime.now().isoformat()},
            {"id": 5, "description": "Movie Tickets", "amount": 28.00, "category": "Entertainment", "date": (datetime.now() - timedelta(days=7)).strftime('%Y-%m-%d'), "notes": "Weekend movie", "timestamp": datetime.now().isoformat()},
        ]
        st.session_state.expenses = sample_expenses
        save_data()
        st.success("Sample data loaded!")
        st.rerun()

st.markdown("---")
st.markdown("Use the sidebar to add expenses, apply filters to analyze specific periods, and export your data as CSV for external analysis.")
