"""Data access layer and query operations for financial records."""

import csv
import io
import sqlite3
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

class FinanceModel:
    def __init__(self, conn: sqlite3.Connection):
        self.conn = conn

    # ---------------- Accounts ----------------
    def get_accounts(self) -> List[Dict[str, Any]]:
        """Fetch all accounts along with dynamically computed live balance."""
        query = """
        SELECT 
            a.id, a.name, a.type, a.institution, a.account_number, a.color, a.is_active, a.created_at,
            a.initial_balance,
            (
                a.initial_balance 
                + COALESCE((SELECT SUM(amount) FROM transactions WHERE account_id = a.id AND type = 'income'), 0)
                - COALESCE((SELECT SUM(amount) FROM transactions WHERE account_id = a.id AND type = 'expense'), 0)
                + COALESCE((SELECT SUM(amount) FROM transactions WHERE to_account_id = a.id AND type = 'transfer'), 0)
                - COALESCE((SELECT SUM(amount) FROM transactions WHERE account_id = a.id AND type = 'transfer'), 0)
            ) AS current_balance,
            (SELECT COUNT(*) FROM transactions WHERE account_id = a.id OR to_account_id = a.id) as tx_count
        FROM accounts a
        WHERE a.is_active = 1
        ORDER BY current_balance DESC;
        """
        rows = self.conn.execute(query).fetchall()
        return [dict(r) for r in rows]

    def create_account(self, name: str, acc_type: str, institution: str,
                       initial_balance: float = 0.0, account_number: str = "",
                       color: str = "#057a55") -> int:
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO accounts (name, type, institution, initial_balance, account_number, color)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (name, acc_type, institution, float(initial_balance), account_number, color)
        )
        self.conn.commit()
        return cur.lastrowid

    def update_account(self, account_id: int, **kwargs) -> bool:
        allowed = {"name", "type", "institution", "account_number", "color", "is_active", "initial_balance"}
        fields = [f"{k} = ?" for k in kwargs if k in allowed]
        if not fields:
            return False
        values = [kwargs[k] for k in kwargs if k in allowed] + [account_id]
        self.conn.execute(f"UPDATE accounts SET {', '.join(fields)} WHERE id = ?", values)
        self.conn.commit()
        return True

    # ---------------- Categories ----------------
    def get_categories(self, cat_type: Optional[str] = None) -> List[Dict[str, Any]]:
        query = "SELECT * FROM categories"
        params = []
        if cat_type:
            query += " WHERE type = ?"
            params.append(cat_type)
        query += " ORDER BY type DESC, name ASC"
        rows = self.conn.execute(query, params).fetchall()
        return [dict(r) for r in rows]

    def create_category(self, name: str, cat_type: str, icon: str, color: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            "INSERT INTO categories (name, type, icon, color) VALUES (?, ?, ?, ?)",
            (name, cat_type, icon, color)
        )
        self.conn.commit()
        return cur.lastrowid

    # ---------------- Transactions ----------------
    def get_transactions(self, 
                         search: str = "",
                         tx_type: str = "",
                         category_id: Optional[int] = None,
                         account_id: Optional[int] = None,
                         start_date: str = "",
                         end_date: str = "",
                         page: int = 1,
                         limit: int = 25) -> Tuple[List[Dict[str, Any]], int]:
        conditions = ["1=1"]
        params = []

        if search:
            conditions.append("(t.description LIKE ? OR t.payee_merchant LIKE ? OR t.notes LIKE ?)")
            term = f"%{search}%"
            params.extend([term, term, term])

        if tx_type:
            conditions.append("t.type = ?")
            params.append(tx_type)

        if category_id:
            conditions.append("t.category_id = ?")
            params.append(category_id)

        if account_id:
            conditions.append("(t.account_id = ? OR t.to_account_id = ?)")
            params.extend([account_id, account_id])

        if start_date:
            conditions.append("t.date >= ?")
            params.append(start_date)

        if end_date:
            conditions.append("t.date <= ?")
            params.append(end_date)

        where_clause = " AND ".join(conditions)

        # Count total records matching criteria
        count_sql = f"SELECT COUNT(*) FROM transactions t WHERE {where_clause}"
        total = self.conn.execute(count_sql, params).fetchone()[0]

        # Fetch paginated rows with joined relations
        offset = (page - 1) * limit
        data_sql = f"""
        SELECT 
            t.id, t.type, t.amount, t.date, t.description, t.payee_merchant, t.notes, t.is_cleared, t.created_at,
            t.account_id, a.name as account_name, a.institution as account_institution, a.color as account_color,
            t.category_id, c.name as category_name, c.icon as category_icon, c.color as category_color,
            t.to_account_id, a2.name as to_account_name
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts a2 ON t.to_account_id = a2.id
        WHERE {where_clause}
        ORDER BY t.date DESC, t.id DESC
        LIMIT ? OFFSET ?;
        """
        data_params = params + [limit, offset]
        rows = self.conn.execute(data_sql, data_params).fetchall()
        return [dict(r) for r in rows], total

    def get_transaction_by_id(self, tx_id: int) -> Optional[Dict[str, Any]]:
        query = """
        SELECT 
            t.*, 
            a.name as account_name, 
            c.name as category_name,
            a2.name as to_account_name
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        LEFT JOIN accounts a2 ON t.to_account_id = a2.id
        WHERE t.id = ?
        """
        row = self.conn.execute(query, (tx_id,)).fetchone()
        return dict(row) if row else None

    def create_transaction(self, account_id: int, category_id: int, tx_type: str,
                           amount: float, date: str, description: str,
                           payee_merchant: str = "", notes: str = "",
                           to_account_id: Optional[int] = None) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO transactions 
               (account_id, category_id, type, amount, date, description, payee_merchant, notes, to_account_id)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (account_id, category_id, tx_type, float(amount), date, description,
             payee_merchant, notes, to_account_id)
        )
        self.conn.commit()
        return cur.lastrowid

    def update_transaction(self, tx_id: int, **kwargs) -> bool:
        allowed = {"account_id", "category_id", "type", "amount", "date", "description",
                   "payee_merchant", "notes", "to_account_id", "is_cleared"}
        fields = [f"{k} = ?" for k in kwargs if k in allowed]
        if not fields:
            return False
        values = [kwargs[k] for k in kwargs if k in allowed] + [tx_id]
        self.conn.execute(f"UPDATE transactions SET {', '.join(fields)} WHERE id = ?", values)
        self.conn.commit()
        return True

    def delete_transaction(self, tx_id: int) -> bool:
        cur = self.conn.cursor()
        cur.execute("DELETE FROM transactions WHERE id = ?", (tx_id,))
        self.conn.commit()
        return cur.rowcount > 0

    # ---------------- Budgets ----------------
    def get_budgets(self, month_year: Optional[str] = None) -> List[Dict[str, Any]]:
        target_month = month_year or datetime.now().strftime("%Y-%m")
        query = """
        SELECT 
            b.id, b.category_id, b.monthly_limit, b.month_year,
            c.name as category_name, c.icon as category_icon, c.color as category_color,
            COALESCE((
                SELECT SUM(t.amount) 
                FROM transactions t 
                WHERE t.category_id = b.category_id 
                  AND t.type = 'expense' 
                  AND strftime('%Y-%m', t.date) = b.month_year
            ), 0.0) AS spent
        FROM budgets b
        JOIN categories c ON b.category_id = c.id
        WHERE b.month_year = ?
        ORDER BY b.monthly_limit DESC;
        """
        rows = self.conn.execute(query, (target_month,)).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            limit = d["monthly_limit"]
            spent = d["spent"]
            pct = round((spent / limit) * 100, 1) if limit > 0 else 0.0
            d["percentage"] = pct
            d["remaining"] = max(0.0, limit - spent)
            d["is_exceeded"] = spent > limit
            result.append(d)
        return result

    def set_budget(self, category_id: int, monthly_limit: float, month_year: str) -> int:
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO budgets (category_id, monthly_limit, month_year)
               VALUES (?, ?, ?)
               ON CONFLICT(category_id, month_year) 
               DO UPDATE SET monthly_limit = excluded.monthly_limit""",
            (category_id, float(monthly_limit), month_year)
        )
        self.conn.commit()
        return cur.lastrowid

    # ---------------- Savings Goals ----------------
    def get_savings_goals(self) -> List[Dict[str, Any]]:
        query = "SELECT * FROM savings_goals ORDER BY is_completed ASC, target_amount DESC"
        rows = self.conn.execute(query).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            target = d["target_amount"]
            cur_amt = d["current_amount"]
            pct = round((cur_amt / target) * 100, 1) if target > 0 else 0.0
            d["percentage"] = min(100.0, pct)
            result.append(d)
        return result

    def create_savings_goal(self, title: str, target_amount: float,
                            current_amount: float = 0.0, target_date: str = "",
                            color: str = "#0284c7") -> int:
        cur = self.conn.cursor()
        cur.execute(
            """INSERT INTO savings_goals (title, target_amount, current_amount, target_date, color)
               VALUES (?, ?, ?, ?, ?)""",
            (title, float(target_amount), float(current_amount), target_date, color)
        )
        self.conn.commit()
        return cur.lastrowid

    def update_savings_goal(self, goal_id: int, **kwargs) -> bool:
        allowed = {"title", "target_amount", "current_amount", "target_date", "color", "is_completed"}
        fields = [f"{k} = ?" for k in kwargs if k in allowed]
        if not fields:
            return False
        values = [kwargs[k] for k in kwargs if k in allowed] + [goal_id]
        self.conn.execute(f"UPDATE savings_goals SET {', '.join(fields)} WHERE id = ?", values)
        self.conn.commit()
        return True

    # ---------------- Executive Financial Summary ----------------
    def get_summary(self, month_year: Optional[str] = None) -> Dict[str, Any]:
        target_month = month_year or datetime.now().strftime("%Y-%m")
        
        # Total Liquid Net Worth across all active accounts
        accounts = self.get_accounts()
        total_net_worth = sum(a["current_balance"] for a in accounts)

        # Monthly income & expense
        cur = self.conn.cursor()
        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0.0) as month_income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0.0) as month_expense,
                COUNT(*) as tx_count
            FROM transactions
            WHERE strftime('%Y-%m', date) = ?
        """, (target_month,))
        row = cur.fetchone()
        month_income = row["month_income"]
        month_expense = row["month_expense"]
        month_tx_count = row["tx_count"]

        net_cashflow = month_income - month_expense
        savings_rate = round((net_cashflow / month_income) * 100, 1) if month_income > 0 else 0.0

        # Previous month comparison for delta
        parts = target_month.split("-")
        year, month = int(parts[0]), int(parts[1])
        if month == 1:
            prev_month = f"{year - 1}-12"
        else:
            prev_month = f"{year}-{month - 1:02d}"

        cur.execute("""
            SELECT 
                COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0.0) as prev_income,
                COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0.0) as prev_expense
            FROM transactions
            WHERE strftime('%Y-%m', date) = ?
        """, (prev_month,))
        prev_row = cur.fetchone()
        prev_expense = prev_row["prev_expense"]
        expense_growth = round(((month_expense - prev_expense) / prev_expense) * 100, 1) if prev_expense > 0 else 0.0

        return {
            "period": target_month,
            "total_net_worth": total_net_worth,
            "month_income": month_income,
            "month_expense": month_expense,
            "net_cashflow": net_cashflow,
            "savings_rate": savings_rate,
            "month_tx_count": month_tx_count,
            "expense_growth_vs_last_month": expense_growth,
            "accounts_count": len(accounts)
        }

    # ---------------- Analytics ----------------
    def get_cashflow_history(self, months: int = 6) -> List[Dict[str, Any]]:
        """Return income vs expense grouped by month for chart plotting."""
        query = """
        SELECT 
            strftime('%Y-%m', date) as month,
            COALESCE(SUM(CASE WHEN type = 'income' THEN amount ELSE 0 END), 0.0) as income,
            COALESCE(SUM(CASE WHEN type = 'expense' THEN amount ELSE 0 END), 0.0) as expense
        FROM transactions
        GROUP BY strftime('%Y-%m', date)
        ORDER BY month DESC
        LIMIT ?;
        """
        rows = self.conn.execute(query, (months,)).fetchall()
        # Return in ascending order for time-series chart
        return [dict(r) for r in reversed(rows)]

    def get_category_breakdown(self, month_year: Optional[str] = None) -> List[Dict[str, Any]]:
        """Return category expense breakdown with percentage share."""
        target_month = month_year or datetime.now().strftime("%Y-%m")
        query = """
        SELECT 
            c.id, c.name, c.icon, c.color,
            COALESCE(SUM(t.amount), 0.0) as total_amount,
            COUNT(t.id) as tx_count
        FROM categories c
        JOIN transactions t ON c.id = t.category_id
        WHERE t.type = 'expense' AND strftime('%Y-%m', t.date) = ?
        GROUP BY c.id
        HAVING total_amount > 0
        ORDER BY total_amount DESC;
        """
        rows = self.conn.execute(query, (target_month,)).fetchall()
        grand_total = sum(r["total_amount"] for r in rows)
        result = []
        for r in rows:
            d = dict(r)
            d["percentage"] = round((d["total_amount"] / grand_total) * 100, 1) if grand_total > 0 else 0.0
            result.append(d)
        return result

    # ---------------- Export Helpers ----------------
    def export_csv(self) -> str:
        """Export all transactions into formatted CSV string."""
        query = """
        SELECT 
            t.id, t.date, t.type, t.amount, t.description, t.payee_merchant, 
            c.name as category, a.name as account, a.institution, t.notes
        FROM transactions t
        JOIN accounts a ON t.account_id = a.id
        LEFT JOIN categories c ON t.category_id = c.id
        ORDER BY t.date DESC;
        """
        rows = self.conn.execute(query).fetchall()
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow(["ID", "Tanggal", "Tipe", "Nominal (IDR)", "Deskripsi", "Merchant/Payee", "Kategori", "Akun/Bank", "Institusi", "Catatan"])
        for r in rows:
            writer.writerow([
                r["id"], r["date"], r["type"].upper(), f"{r['amount']:.2f}",
                r["description"], r["payee_merchant"] or "-",
                r["category"] or "Uncategorized", r["account"], r["institution"], r["notes"] or ""
            ])
        return output.getvalue()
