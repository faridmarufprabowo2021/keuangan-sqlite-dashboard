"""REST API request handlers and route dispatcher for Valuta Finance."""

import json
import mimetypes
import os
import urllib.parse
from http.server import SimpleHTTPRequestHandler
from typing import Any, Dict

from app.database import DB_PATH, get_db
from app.models import FinanceModel

BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
STATIC_DIR = os.path.join(BASE_DIR, "static")
TEMPLATES_DIR = os.path.join(BASE_DIR, "templates")

class FinanceAPIHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=STATIC_DIR, **kwargs)

    # ---------------- Helpers ----------------
    def send_json(self, data: Any, status: int = 200):
        body = json.dumps(data, ensure_ascii=False).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()
        self.wfile.write(body)

    def send_error_json(self, message: str, status: int = 400):
        self.send_json({"error": True, "message": message}, status=status)

    def read_json_body(self) -> Dict[str, Any]:
        try:
            length = int(self.headers.get("Content-Length", 0))
            if length == 0:
                return {}
            raw = self.rfile.read(length).decode("utf-8")
            return json.loads(raw)
        except Exception as e:
            raise ValueError(f"Invalid JSON payload: {str(e)}")

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "GET, POST, PUT, DELETE, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    # ---------------- Route Dispatcher ----------------
    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path
        query = urllib.parse.parse_qs(parsed.query)

        # Serve Dashboard Root Page
        if path == "/" or path == "/index.html":
            index_path = os.path.join(TEMPLATES_DIR, "index.html")
            if os.path.exists(index_path):
                with open(index_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", "text/html; charset=utf-8")
                self.send_header("Content-Length", str(len(content)))
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "Template index.html not found")
                return

        # Serve Static Files (/static/...)
        if path.startswith("/static/"):
            rel_path = path[len("/static/"):]
            file_path = os.path.join(STATIC_DIR, rel_path)
            if os.path.isfile(file_path):
                mime, _ = mimetypes.guess_type(file_path)
                with open(file_path, "rb") as f:
                    content = f.read()
                self.send_response(200)
                self.send_header("Content-Type", mime or "application/octet-stream")
                self.send_header("Content-Length", str(len(content)))
                self.send_header("Cache-Control", "no-cache")
                self.end_headers()
                self.wfile.write(content)
                return
            else:
                self.send_error(404, "Static file not found")
                return

        # API Routes
        conn = get_db()
        model = FinanceModel(conn)
        try:
            # 1. Executive Summary
            if path == "/api/summary":
                month = query.get("month", [None])[0]
                summary = model.get_summary(month)
                self.send_json({"success": True, "data": summary})
                return

            # 2. Accounts
            if path == "/api/accounts":
                accounts = model.get_accounts()
                self.send_json({"success": True, "data": accounts})
                return

            # 3. Categories
            if path == "/api/categories":
                c_type = query.get("type", [None])[0]
                categories = model.get_categories(c_type)
                self.send_json({"success": True, "data": categories})
                return

            # 4. Transactions List
            if path == "/api/transactions":
                search = query.get("search", [""])[0]
                tx_type = query.get("type", [""])[0]
                cat_id = int(query["category_id"][0]) if "category_id" in query and query["category_id"][0] else None
                acc_id = int(query["account_id"][0]) if "account_id" in query and query["account_id"][0] else None
                start_date = query.get("start_date", [""])[0]
                end_date = query.get("end_date", [""])[0]
                page = int(query.get("page", ["1"])[0])
                limit = int(query.get("limit", ["20"])[0])

                items, total = model.get_transactions(
                    search=search, tx_type=tx_type, category_id=cat_id,
                    account_id=acc_id, start_date=start_date, end_date=end_date,
                    page=page, limit=limit
                )
                pages = max(1, (total + limit - 1) // limit)
                self.send_json({
                    "success": True,
                    "data": items,
                    "meta": {
                        "total": total,
                        "page": page,
                        "limit": limit,
                        "pages": pages
                    }
                })
                return

            # 5. Single Transaction Details
            if path.startswith("/api/transactions/"):
                tx_id = int(path.split("/")[-1])
                item = model.get_transaction_by_id(tx_id)
                if item:
                    self.send_json({"success": True, "data": item})
                else:
                    self.send_error_json("Transaksi tidak ditemukan", status=404)
                return

            # 6. Budgets
            if path == "/api/budgets":
                month = query.get("month", [None])[0]
                budgets = model.get_budgets(month)
                self.send_json({"success": True, "data": budgets})
                return

            # 7. Savings Goals
            if path == "/api/savings":
                goals = model.get_savings_goals()
                self.send_json({"success": True, "data": goals})
                return

            # 8. Cashflow Trend Analytics
            if path == "/api/analytics/cashflow":
                months_cnt = int(query.get("months", ["6"])[0])
                history = model.get_cashflow_history(months_cnt)
                self.send_json({"success": True, "data": history})
                return

            # 9. Category Expense Breakdown
            if path == "/api/analytics/breakdown":
                month = query.get("month", [None])[0]
                breakdown = model.get_category_breakdown(month)
                self.send_json({"success": True, "data": breakdown})
                return

            # 10. CSV Export Download
            if path == "/api/export/csv":
                csv_data = model.export_csv().encode("utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "text/csv; charset=utf-8")
                self.send_header("Content-Disposition", 'attachment; filename="valuta_transactions.csv"')
                self.send_header("Content-Length", str(len(csv_data)))
                self.end_headers()
                self.wfile.write(csv_data)
                return

            # 11. Database SQLite Backup Download
            if path == "/api/export/db":
                if os.path.exists(DB_PATH):
                    with open(DB_PATH, "rb") as f:
                        db_content = f.read()
                    self.send_response(200)
                    self.send_header("Content-Type", "application/x-sqlite3")
                    self.send_header("Content-Disposition", 'attachment; filename="valuta_finance.db"')
                    self.send_header("Content-Length", str(len(db_content)))
                    self.end_headers()
                    self.wfile.write(db_content)
                    return
                else:
                    self.send_error_json("Database file not found", 404)
                    return

            self.send_error_json("Endpoint tidak ditemukan", 404)
        finally:
            conn.close()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            body = self.read_json_body()
        except ValueError as err:
            self.send_error_json(str(err), 400)
            return

        conn = get_db()
        model = FinanceModel(conn)
        try:
            # 1. Create Transaction
            if path == "/api/transactions":
                account_id = body.get("account_id")
                category_id = body.get("category_id")
                tx_type = body.get("type", "expense")
                amount = body.get("amount")
                date = body.get("date")
                description = body.get("description", "").strip()
                payee_merchant = body.get("payee_merchant", "").strip()
                notes = body.get("notes", "").strip()
                to_account_id = body.get("to_account_id")

                if not account_id or not category_id or not amount or not date or not description:
                    self.send_error_json("Field account_id, category_id, amount, date, dan description wajib diisi")
                    return

                try:
                    amount_float = float(amount)
                    if amount_float <= 0:
                        raise ValueError()
                except Exception:
                    self.send_error_json("Amount harus berupa angka positif lebih dari 0")
                    return

                tx_id = model.create_transaction(
                    account_id=int(account_id),
                    category_id=int(category_id),
                    tx_type=tx_type,
                    amount=amount_float,
                    date=date,
                    description=description,
                    payee_merchant=payee_merchant,
                    notes=notes,
                    to_account_id=int(to_account_id) if to_account_id else None
                )
                self.send_json({"success": True, "message": "Transaksi berhasil disimpan", "id": tx_id}, status=201)
                return

            # 2. Create Account
            if path == "/api/accounts":
                name = body.get("name", "").strip()
                acc_type = body.get("type", "bank")
                institution = body.get("institution", "").strip()
                initial_balance = float(body.get("initial_balance", 0.0))
                account_number = body.get("account_number", "").strip()
                color = body.get("color", "#057a55")

                if not name or not institution:
                    self.send_error_json("Nama akun dan institusi wajib diisi")
                    return

                aid = model.create_account(name, acc_type, institution, initial_balance, account_number, color)
                self.send_json({"success": True, "message": "Akun berhasil dibuat", "id": aid}, status=201)
                return

            # 3. Set Budget Limit
            if path == "/api/budgets":
                category_id = body.get("category_id")
                monthly_limit = body.get("monthly_limit")
                month_year = body.get("month_year")

                if not category_id or not monthly_limit or not month_year:
                    self.send_error_json("category_id, monthly_limit, dan month_year wajib diisi")
                    return

                bid = model.set_budget(int(category_id), float(monthly_limit), month_year)
                self.send_json({"success": True, "message": "Budget berhasil diperbarui", "id": bid})
                return

            # 4. Create Savings Goal
            if path == "/api/savings":
                title = body.get("title", "").strip()
                target_amount = body.get("target_amount")
                current_amount = float(body.get("current_amount", 0.0))
                target_date = body.get("target_date", "")
                color = body.get("color", "#0284c7")

                if not title or not target_amount:
                    self.send_error_json("Judul dan target_amount wajib diisi")
                    return

                gid = model.create_savings_goal(title, float(target_amount), current_amount, target_date, color)
                self.send_json({"success": True, "message": "Target tabungan berhasil dibuat", "id": gid}, status=201)
                return

            # 5. Seed / Reset Data
            if path == "/api/seed":
                from seed import seed
                seed()
                self.send_json({"success": True, "message": "Database berhasil diseed ulang"})
                return

            self.send_error_json("Endpoint POST tidak ditemukan", 404)
        finally:
            conn.close()

    def do_PUT(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        try:
            body = self.read_json_body()
        except ValueError as err:
            self.send_error_json(str(err), 400)
            return

        conn = get_db()
        model = FinanceModel(conn)
        try:
            # 1. Update Transaction
            if path.startswith("/api/transactions/"):
                tx_id = int(path.split("/")[-1])
                success = model.update_transaction(tx_id, **body)
                if success:
                    self.send_json({"success": True, "message": "Transaksi berhasil diperbarui"})
                else:
                    self.send_error_json("Gagal memperbarui transaksi", 400)
                return

            # 2. Update Account
            if path.startswith("/api/accounts/"):
                acc_id = int(path.split("/")[-1])
                success = model.update_account(acc_id, **body)
                if success:
                    self.send_json({"success": True, "message": "Akun berhasil diperbarui"})
                else:
                    self.send_error_json("Gagal memperbarui akun", 400)
                return

            # 3. Update Savings Goal
            if path.startswith("/api/savings/"):
                gid = int(path.split("/")[-1])
                success = model.update_savings_goal(gid, **body)
                if success:
                    self.send_json({"success": True, "message": "Target tabungan berhasil diperbarui"})
                else:
                    self.send_error_json("Gagal memperbarui target tabungan", 400)
                return

            self.send_error_json("Endpoint PUT tidak ditemukan", 404)
        finally:
            conn.close()

    def do_DELETE(self):
        parsed = urllib.parse.urlparse(self.path)
        path = parsed.path

        conn = get_db()
        model = FinanceModel(conn)
        try:
            # 1. Delete Transaction
            if path.startswith("/api/transactions/"):
                tx_id = int(path.split("/")[-1])
                success = model.delete_transaction(tx_id)
                if success:
                    self.send_json({"success": True, "message": "Transaksi berhasil dihapus"})
                else:
                    self.send_error_json("Transaksi tidak ditemukan", 404)
                return

            self.send_error_json("Endpoint DELETE tidak ditemukan", 404)
        finally:
            conn.close()
