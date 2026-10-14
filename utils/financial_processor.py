import pandas as pd
import json
from datetime import datetime

def load_transactions(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    df['Date'] = pd.to_datetime(df['Date'])
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce').fillna(0)
    return df

def load_budget(csv_path):
    df = pd.read_csv(csv_path)
    df.columns = df.columns.str.strip()
    return df

def generate_financial_summary(transactions_df, budget_df=None):
    df = transactions_df.copy()
    
    debits = df[df['Transaction Type'] == 'debit']
    credits = df[df['Transaction Type'] == 'credit']
    
    total_spent = debits['Amount'].sum()
    total_income = credits['Amount'].sum()
    net_savings = total_income - total_spent
    
    category_spending = debits.groupby('Category')['Amount'].sum().sort_values(ascending=False)
    top_categories = category_spending.head(5).to_dict()
    
    monthly_spending = debits.groupby(
        debits['Date'].dt.to_period('M')
    )['Amount'].sum()
    
    account_breakdown = df.groupby(['Account Name', 'Transaction Type'])['Amount'].sum().unstack(fill_value=0)
    
    summary = {
        'total_transactions': len(df),
        'date_range': f"{df['Date'].min().strftime('%b %Y')} to {df['Date'].max().strftime('%b %Y')}",
        'total_spent': round(total_spent, 2),
        'total_income': round(total_income, 2),
        'net_savings': round(net_savings, 2),
        'top_spending_categories': top_categories,
        'avg_monthly_spending': round(monthly_spending.mean(), 2),
        'highest_spending_month': str(monthly_spending.idxmax()),
        'lowest_spending_month': str(monthly_spending.idxmin()),
        'total_categories': df['Category'].nunique(),
        'accounts': df['Account Name'].unique().tolist(),
    }
    
    if budget_df is not None:
        budget_comparison = []
        for _, row in budget_df.iterrows():
            category = row['Category']
            budget = row['Budget']
            actual = category_spending.get(category, 0)
            status = 'Over Budget' if actual > budget else 'Under Budget'
            budget_comparison.append({
                'category': category,
                'budget': budget,
                'actual': round(actual, 2),
                'difference': round(actual - budget, 2),
                'status': status
            })
        summary['budget_comparison'] = budget_comparison
    
    return summary

def dataframe_to_text(transactions_df, budget_df=None):
    df = transactions_df.copy()
    summary = generate_financial_summary(df, budget_df)
    
    lines = []
    lines.append("=== FINANCIAL DATA SUMMARY ===")
    lines.append(f"Date Range: {summary['date_range']}")
    lines.append(f"Total Transactions: {summary['total_transactions']}")
    lines.append(f"Total Income: ${summary['total_income']:,.2f}")
    lines.append(f"Total Spent: ${summary['total_spent']:,.2f}")
    lines.append(f"Net Savings: ${summary['net_savings']:,.2f}")
    lines.append(f"Average Monthly Spending: ${summary['avg_monthly_spending']:,.2f}")
    lines.append(f"Highest Spending Month: {summary['highest_spending_month']}")
    lines.append("")
    
    lines.append("=== TOP SPENDING CATEGORIES ===")
    for cat, amt in summary['top_spending_categories'].items():
        lines.append(f"{cat}: ${amt:,.2f}")
    lines.append("")
    
    lines.append("=== ALL TRANSACTIONS ===")
    for _, row in df.iterrows():
        lines.append(
            f"{row['Date'].strftime('%Y-%m-%d')} | {row['Description']} | "
            f"{row['Transaction Type'].upper()} | ${row['Amount']:.2f} | "
            f"{row['Category']} | {row['Account Name']}"
        )
    lines.append("")
    
    if budget_df is not None and 'budget_comparison' in summary:
        lines.append("=== BUDGET vs ACTUAL ===")
        for item in summary['budget_comparison']:
            lines.append(
                f"{item['category']}: Budget ${item['budget']} | "
                f"Actual ${item['actual']} | {item['status']} by ${abs(item['difference'])}"
            )
    
    return "\n".join(lines)