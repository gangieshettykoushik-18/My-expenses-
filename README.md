# My-expenses-
A tool that lets users log daily expenses, store them in a database, and analyze spending habits.

# Personal Expense Tracker (Python + SQLite)

## Features

- Add expenses (date, category, amount, notes)
- View all expenses
- Filter/search by date, category, amount range
- Analytics:
  - Total spending
  - Spending by category
  - Monthly trend
- Charts saved as PNG (`category_pie.png`, `monthly_trend.png`)
- Export all records to CSV

## Tech stack
- Python 3.8+
- SQLite (built-in)
- pandas
- matplotlib

---

## Setup & Run

1. Clone or download this repo.

2. (Optional) Create and activate a virtual environment:
```bash
python -m venv venv
# Linux / macOS
source venv/bin/activate
# Windows (PowerShell)
venv\Scripts\Activate.ps1
