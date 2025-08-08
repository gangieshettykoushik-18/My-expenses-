#!/usr/bin/env python3
"""
Personal Expense Tracker (Console App)
- SQLite backend (file: expenses.db)
- Commands: add, view, search, analytics, export, quit
- Charts saved as PNG files (requires matplotlib)
"""
import sqlite3
import os
from datetime import datetime
import pandas as pd
import matplotlib.pyplot as plt
import sys
import csv
from textwrap import dedent

DB_FILE = "expenses.db"

# ---------- Database helpers ----------
def get_conn():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        """
        CREATE TABLE IF NOT EXISTS expenses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            category TEXT NOT NULL,
            amount REAL NOT NULL,
            notes TEXT
        );
        """
    )
    conn.commit()
    conn.close()

# ---------- CRUD ----------
def add_expense(date_str, category, amount, notes=""):
    # date_str expected 'YYYY-MM-DD'
    try:
        # validate date
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise ValueError("Date must be in YYYY-MM-DD format.")
    conn = get_conn()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO expenses (date, category, amount, notes) VALUES (?, ?, ?, ?)",
        (date_str, category.strip(), float(amount), notes.strip() if notes else None),
    )
    conn.commit()
    conn.close()

def fetch_all():
    conn = get_conn()
    df = pd.read_sql_query("SELECT * FROM expenses ORDER BY date DESC, id DESC", conn, parse_dates=['date'])
    conn.close()
    return df

def search_expenses(start_date=None, end_date=None, category=None, min_amt=None, max_amt=None):
    query = "SELECT * FROM expenses WHERE 1=1"
    params = []
    if start_date:
        query += " AND date >= ?"
        params.append(start_date)
    if end_date:
        query += " AND date <= ?"
        params.append(end_date)
    if category:
        query += " AND lower(category) = lower(?)"
        params.append(category)
    if min_amt is not None:
        query += " AND amount >= ?"
        params.append(min_amt)
    if max_amt is not None:
        query += " AND amount <= ?"
        params.append(max_amt)
    query += " ORDER BY date DESC, id DESC"
    conn = get_conn()
    df = pd.read_sql_query(query, conn, params=params, parse_dates=['date'])
    conn.close()
    return df

# ---------- Analytics & Plots ----------
def total_spending(df):
    return df['amount'].sum()

def spending_by_category(df):
    return df.groupby('category', dropna=False)['amount'].sum().sort_values(ascending=False)

def monthly_trend(df):
    df2 = df.copy()
    df2['date'] = pd.to_datetime(df2['date'])
    df2['month'] = df2['date'].dt.to_period('M')
    series = df2.groupby('month')['amount'].sum().sort_index()
    series.index = series.index.astype(str)
    return series

def plot_pie_category(series, out_path="category_pie.png"):
    if series.empty:
        print("No data to plot for category pie chart.")
        return None
    plt.figure(figsize=(6,6))
    series.plot.pie(autopct="%1.1f%%", ylabel="")
    plt.title("Spending by Category")
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return out_path

def plot_monthly_trend(series, out_path="monthly_trend.png"):
    if series.empty:
        print("No data to plot for monthly trend.")
        return None
    plt.figure(figsize=(8,4))
    series.plot(marker='o')
    plt.xlabel("Month")
    plt.ylabel("Total Spending")
    plt.title("Monthly Spending Trend")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(out_path)
    plt.close()
    return out_path

# ---------- Export ----------
def export_csv(df, filename="expenses_export.csv"):
    df.to_csv(filename, index=False)
    return filename

# ---------- Console UI ----------
MENU = dedent("""
    Personal Expense Tracker
    ------------------------
    1. Add expense
    2. View all expenses
    3. Search / Filter expenses
    4. Analytics (totals, charts)
    5. Export to CSV
    6. Help
    7. Quit
""")

def prompt_add():
    print("\nAdd new expense (enter 'q' to cancel)\n")
    date = input("Date (YYYY-MM-DD) [default: today]: ").strip()
    if date.lower() == 'q':
        return
    if date == "":
        date = datetime.now().strftime("%Y-%m-%d")
    category = input("Category (e.g., Food, Travel): ").strip()
    if category.lower() == 'q' or not category:
        print("Cancelled or invalid category.")
        return
    amount = input("Amount (numeric): ").strip()
    if amount.lower() == 'q':
        return
    try:
        amt = float(amount)
    except:
        print("Invalid amount. Aborting.")
        return
    notes = input("Notes (optional): ").strip()
    try:
        add_expense(date, category, amt, notes)
        print("✔ Expense added.")
    except Exception as e:
        print("Error adding expense:", e)

def display_df(df, limit=None):
    if df.empty:
        print("No records found.")
        return
    if limit:
        df = df.head(limit)
    print(df.to_string(index=False))

def prompt_view_all():
    df = fetch_all()
    display_df(df)

def prompt_search():
    print("\nSearch / Filter (press ENTER to skip a filter)\n")
    sdate = input("Start date (YYYY-MM-DD): ").strip() or None
    edate = input("End date (YYYY-MM-DD): ").strip() or None
    cat = input("Category (exact match): ").strip() or None
    mina = input("Min amount: ").strip() or None
    maxa = input("Max amount: ").strip() or None
    try:
        mina_val = float(mina) if mina else None
        maxa_val = float(maxa) if maxa else None
    except:
        print("Invalid amount filters.")
        return
    df = search_expenses(sdate, edate, cat, mina_val, maxa_val)
    display_df(df)

def prompt_analytics():
    df = fetch_all()
    if df.empty:
        print("No data available for analytics.")
        return
    total = total_spending(df)
    print(f"\nTotal spending (all time): {total:.2f}\n")
    print("Spending by category:")
    by_cat = spending_by_category(df)
    print(by_cat.to_string())
    # Plots
    pie_path = plot_pie_category(by_cat, out_path="category_pie.png")
    trend_series = monthly_trend(df)
    trend_path = plot_monthly_trend(trend_series, out_path="monthly_trend.png")
    print("\nCharts saved as:", ", ".join([p for p in [pie_path, trend_path] if p]))
    print("You can open these PNG files in your folder.")

def prompt_export():
    df = fetch_all()
    if df.empty:
        print("No data to export.")
        return
    fname = input("Export filename [default: expenses_export.csv]: ").strip() or "expenses_export.csv"
    export_csv(df, fname)
    print("Exported to", fname)

def print_help():
    print(dedent("""
    Quick usage tips:
    - Dates must be YYYY-MM-DD (you can leave blank when adding to use today's date)
    - Categories are case-insensitive for searching, but stored as entered
    - Charts are saved as PNG files in the current folder:
        - category_pie.png
        - monthly_trend.png
    - Export creates a CSV file readable by Excel / Google Sheets
    """))

def main_loop():
    init_db()
    while True:
        print(MENU)
        choice = input("Enter choice [1-7]: ").strip()
        if choice == '1':
            prompt_add()
        elif choice == '2':
            prompt_view_all()
        elif choice == '3':
            prompt_search()
        elif choice == '4':
            prompt_analytics()
        elif choice == '5':
            prompt_export()
        elif choice == '6':
            print_help()
        elif choice == '7' or choice.lower() in ('q', 'quit', 'exit'):
            print("Bye — remember to commit your changes if you added data!")
            break
        else:
            print("Invalid choice. Try again.")

if __name__ == "__main__":
    try:
        main_loop()
    except KeyboardInterrupt:
        print("\nInterrupted. Exiting.")
        sys.exit(0)
