import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from utils.financial_processor import load_transactions, load_budget, generate_financial_summary, dataframe_to_text
from utils.rag_engine import build_vector_store, ask_finwise

st.set_page_config(
    page_title="WealthLens — See Your Finances Clearly",
    page_icon="🔍",
    layout="wide"
)

st.markdown("""
<div style='padding: 1rem 0 0.5rem 0;'>
    <h1 style='color: #f0c040; font-size: 2.2rem; font-weight: 800; margin: 0;
    text-shadow: 0 0 30px rgba(240,192,64,0.4);'>
        🔍 WealthLens
    </h1>
    <p style='color: #7c6a9e; font-size: 0.95rem; margin: 6px 0 0 0; font-style: italic;'>
        See Your Finances Clearly — RAG-powered financial intelligence
    </p>
</div>
""", unsafe_allow_html=True)

if "vector_store" not in st.session_state:
    st.session_state.vector_store = None
if "messages" not in st.session_state:
    st.session_state.messages = []
if "summary" not in st.session_state:
    st.session_state.summary = None
if "transactions_df" not in st.session_state:
    st.session_state.transactions_df = None
if "budget_df" not in st.session_state:
    st.session_state.budget_df = None

with st.sidebar:
    st.markdown("## 🔍 WealthLens")
    st.caption("See Your Finances Clearly")
    st.divider()
    
    st.subheader("📂 Upload Documents")
    
    transactions_file = st.file_uploader(
        "Transaction CSV",
        type=['csv'],
        help="Upload your bank transaction CSV"
    )
    
    budget_file = st.file_uploader(
        "Budget CSV (optional)",
        type=['csv'],
        help="Upload your budget CSV"
    )
    
    if transactions_file:
        if st.button("🚀 Analyze Documents", use_container_width=True):
            with st.spinner("Processing your financial data..."):
                transactions_df = load_transactions(transactions_file)
                budget_df = load_budget(budget_file) if budget_file else None
                
                st.session_state.transactions_df = transactions_df
                st.session_state.budget_df = budget_df
                
                text = dataframe_to_text(transactions_df, budget_df)
                
                vector_store, _ = build_vector_store(text)
                st.session_state.vector_store = vector_store
                
                summary = generate_financial_summary(transactions_df, budget_df)
                st.session_state.summary = summary
                
                st.success(f"✅ Analyzed {len(transactions_df)} transactions!")
    
    st.divider()
    
    st.subheader("💡 Try asking")
    example_questions = [
    "What was my total spending?",
    "Which category did I spend most on?",
    "What is my net savings?",
    "What were my top 5 largest transactions?",
    "Did I overspend my budget?",
    "What was my highest spending month?",
    "Summarize my spending habits",
    "How much did I spend on groceries?",
    "Which months did I overspend?",
    "What is my average monthly spending?",
    "How much did I spend on restaurants?",
    "Compare my income vs expenses",
            ]
    
    for q in example_questions:
        if st.button(q, use_container_width=True, key=q):
            st.session_state.pending_question = q
    
    st.divider()
    if st.button("🗑️ Clear chat", use_container_width=True):
        st.session_state.messages = []
        st.rerun()

st.title("🔍 WealthLens")
st.caption("See Your Finances Clearly")

if st.session_state.summary is None:
    st.info("👈 Upload your transaction CSV and click Analyze to get started")
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown("""
        ### 📊 What WealthLens can do
        - Analyze spending patterns
        - Track category budgets
        - Identify trends over time
        - Answer natural language questions
        """)
    with col2:
        st.markdown("""
        ### 📁 Supported files
        - Transaction CSV files
        - Bank statement CSVs
        - Budget CSV files
        - Multiple account data
        """)
    with col3:
        st.markdown("""
        ### 🤖 Powered by
        - RAG (Retrieval Augmented Generation)
        - FAISS vector search
        - Llama 3.3 via Groq API
        - Sentence Transformers
        """)
else:
    summary = st.session_state.summary
    
    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Total Income", f"${summary['total_income']:,.2f}")
    col2.metric("Total Spent", f"${summary['total_spent']:,.2f}")
    col3.metric("Net Savings", f"${summary['net_savings']:,.2f}")
    col4.metric("Transactions", f"{summary['total_transactions']:,}")
    
    st.divider()
    
    tab1, tab2, tab3 = st.tabs(["🤖 AI Chat", "📊 Analytics", "💰 Budget"])
    
    with tab1:
        for msg in st.session_state.messages:
            with st.chat_message(msg["role"]):
                st.markdown(msg["content"])
        
        question = st.chat_input("Ask about your finances...")
        
        if "pending_question" in st.session_state:
            question = st.session_state.pending_question
            del st.session_state.pending_question
        
        if question and st.session_state.vector_store:
            st.session_state.messages.append({"role": "user", "content": question})
            with st.chat_message("user"):
                st.markdown(question)
            
            with st.chat_message("assistant"):
                with st.spinner("Analyzing your financial data..."):
                    answer = ask_finwise(
                        st.session_state.vector_store,
                        question,
                        st.session_state.messages
                    )
                    st.markdown(answer)
                    st.session_state.messages.append({
                        "role": "assistant",
                        "content": answer
                    })
    
    with tab2:
        df = st.session_state.transactions_df
        
        col_a, col_b = st.columns(2)
        
        with col_a:
            st.markdown("#### Spending by Category")
            debits = df[df['Transaction Type'] == 'debit']
            cat_spend = debits.groupby('Category')['Amount'].sum().reset_index()
            cat_spend = cat_spend.sort_values('Amount', ascending=False).head(10)
            
            fig1 = px.bar(
                cat_spend,
                x='Amount',
                y='Category',
                orientation='h',
                color='Amount',
                color_continuous_scale=['#00d4aa', '#0a0e1a'],
                title="Top 10 Spending Categories"
            )
            fig1.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                coloraxis_showscale=False,
                height=400
            )
            st.plotly_chart(fig1, use_container_width=True)
        
        with col_b:
            st.markdown("#### Spending Distribution")
            fig2 = px.pie(
                cat_spend,
                names='Category',
                values='Amount',
                title="Spending Distribution",
                hole=0.4,
                color_discrete_sequence=px.colors.sequential.Teal
            )
            fig2.update_layout(
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=400
            )
            st.plotly_chart(fig2, use_container_width=True)
        
        st.markdown("#### Monthly Spending Trend")
        monthly = debits.groupby(debits['Date'].dt.to_period('M'))['Amount'].sum().reset_index()
        monthly['Date'] = monthly['Date'].astype(str)
        
        fig3 = px.line(
            monthly,
            x='Date',
            y='Amount',
            title="Monthly Spending Over Time",
            markers=True,
            color_discrete_sequence=['#00d4aa']
        )
        fig3.update_layout(
            plot_bgcolor='rgba(0,0,0,0)',
            paper_bgcolor='rgba(0,0,0,0)',
            height=350
        )
        st.plotly_chart(fig3, use_container_width=True)
        
        st.markdown("#### Transaction History")
        st.dataframe(
            df[['Date', 'Description', 'Amount', 'Transaction Type', 'Category', 'Account Name']].sort_values('Date', ascending=False),
            use_container_width=True,
            hide_index=True
        )
    
    with tab3:
        if st.session_state.budget_df is not None and 'budget_comparison' in summary:
            st.markdown("#### Budget vs Actual Spending")
            
            budget_data = pd.DataFrame(summary['budget_comparison'])
            
            over_budget = budget_data[budget_data['status'] == 'Over Budget']
            under_budget = budget_data[budget_data['status'] == 'Under Budget']
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Categories Tracked", len(budget_data))
            col2.metric("Over Budget", len(over_budget), delta=f"{len(over_budget)} categories", delta_color="inverse")
            col3.metric("Under Budget", len(under_budget), delta=f"{len(under_budget)} categories")
            
            fig4 = go.Figure()
            fig4.add_trace(go.Bar(
                name='Budget',
                x=budget_data['category'],
                y=budget_data['budget'],
                marker_color='#3498db'
            ))
            fig4.add_trace(go.Bar(
                name='Actual',
                x=budget_data['category'],
                y=budget_data['actual'],
                marker_color=budget_data['status'].map({
                    'Over Budget': '#e74c3c',
                    'Under Budget': '#2ecc71'
                })
            ))
            fig4.update_layout(
                barmode='group',
                title="Budget vs Actual by Category",
                plot_bgcolor='rgba(0,0,0,0)',
                paper_bgcolor='rgba(0,0,0,0)',
                height=450,
                xaxis_tickangle=45
            )
            st.plotly_chart(fig4, use_container_width=True)
            
            st.markdown("#### Detailed Budget Breakdown")
            st.dataframe(budget_data, use_container_width=True, hide_index=True)
        else:
            st.info("Upload a Budget CSV to see budget vs actual comparison")