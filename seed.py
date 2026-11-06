"""Realistic seed data generator for Valuta Financial Dashboard (6-Month Historical Trajectory)."""

import os
import sys
from datetime import datetime, timedelta
from app.database import DB_PATH, get_db, init_db
from app.models import FinanceModel

def seed(force_reseed: bool = False):
    init_db()
    conn = get_db()
    model = FinanceModel(conn)

    if not force_reseed:
        existing = model.get_accounts()
        if existing and len(existing) >= 4:
            # Check transaction count
            cur = conn.cursor()
            tx_cnt = cur.execute("SELECT COUNT(*) FROM transactions").fetchone()[0]
            if tx_cnt >= 40:
                print(f"Database already contains {len(existing)} accounts and {tx_cnt} transactions. Skipping reseed.")
                conn.close()
                return

    print("Cleaning and initializing fresh database schema for full 6-month seed...")
    with conn:
        conn.execute("DELETE FROM transactions;")
        conn.execute("DELETE FROM budgets;")
        conn.execute("DELETE FROM savings_goals;")
        conn.execute("DELETE FROM accounts;")
        conn.execute("DELETE FROM categories;")
        conn.execute("DELETE FROM sqlite_sequence;")

    print("Seeding standard categories...")
    categories_data = [
        # Income
        ("Gaji & Penghasilan Tetap", "income", "briefcase", "#057a55"),
        ("Freelance & Konsultasi", "income", "laptop", "#0d9488"),
        ("Dividen & Investasi", "income", "trending-up", "#0284c7"),
        ("Penjualan Aset / Bisnis", "income", "shopping-bag", "#7c3aed"),
        # Expense
        ("Kebutuhan Pokok & Belanja", "expense", "shopping-cart", "#d97706"),
        ("Makanan & Restoran", "expense", "coffee", "#ea580c"),
        ("Transportasi & Kendaraan", "expense", "truck", "#4f46e5"),
        ("Sewa Tempat & Hunian", "expense", "home", "#e11d48"),
        ("Tagihan & Utilitas", "expense", "zap", "#ca8a04"),
        ("Langganan Software & Cloud", "expense", "server", "#2563eb"),
        ("Kesehatan & Olahraga", "expense", "activity", "#16a34a"),
        ("Hiburan & Edukasi", "expense", "film", "#9333ea"),
        ("Amal & Donasi", "expense", "heart", "#ec4899"),
    ]

    cat_ids = {}
    for name, c_type, icon, color in categories_data:
        cid = model.create_category(name, c_type, icon, color)
        cat_ids[name] = cid

    print("Seeding bank accounts & digital wallets...")
    accounts_data = [
        ("BCA Rekening Operasional", "bank", "Bank Central Asia", 18500000.0, "8820-412-991", "#005baa"),
        ("Mandiri Tabungan Utama", "bank", "Bank Mandiri", 75000000.0, "137-00-19283-4", "#002b66"),
        ("GoPay & GoPay Tabungan", "ewallet", "GoTo Financial", 3250000.0, "0812-9988-7711", "#00aa13"),
        ("Bibit Portofolio Investasi", "investment", "PT Bibit Tumbuh Bersama", 68400000.0, "RD-BIBIT-9821", "#10b981"),
        ("Kas Tunai & Brankas", "cash", "Dompet Fisik", 2400000.0, "-", "#475569"),
    ]

    acc_ids = {}
    for name, a_type, inst, init_bal, acc_num, color in accounts_data:
        aid = model.create_account(name, a_type, inst, init_bal, acc_num, color)
        acc_ids[name] = aid

    print("Seeding monthly category budgets...")
    months = ["2026-06", "2026-07", "2026-08", "2026-09", "2026-10", "2026-11"]
    budget_limits = {
        "Makanan & Restoran": 4500000.0,
        "Kebutuhan Pokok & Belanja": 5000000.0,
        "Transportasi & Kendaraan": 2000000.0,
        "Tagihan & Utilitas": 1800000.0,
        "Langganan Software & Cloud": 1500000.0,
        "Hiburan & Edukasi": 1200000.0,
    }
    for m in months:
        for cat_name, limit in budget_limits.items():
            if cat_name in cat_ids:
                model.set_budget(cat_ids[cat_name], limit, m)

    print("Seeding savings goals...")
    savings_data = [
        ("Dana Darurat 6 Bulan", 90000000.0, 72000000.0, "2027-06-30", "#057a55"),
        ("Renovasi Studio & Ergonomi", 25000000.0, 18500000.0, "2026-12-31", "#2563eb"),
        ("Portofolio Saham Blue Chip", 50000000.0, 31400000.0, "2027-03-31", "#7c3aed"),
    ]
    for title, target, current, target_dt, color in savings_data:
        model.create_savings_goal(title, target, current, target_dt, color)

    bca = acc_ids["BCA Rekening Operasional"]
    mandiri = acc_ids["Mandiri Tabungan Utama"]
    gopay = acc_ids["GoPay & GoPay Tabungan"]
    bibit = acc_ids["Bibit Portofolio Investasi"]
    tunai = acc_ids["Kas Tunai & Brankas"]

    print("Seeding 6 months of historical transactions (Jun - Nov 2026)...")
    monthly_templates = [
        # June 2026
        ("2026-06", [
            (mandiri, cat_ids["Gaji & Penghasilan Tetap"], "income", 30000000.0, "Gaji Bulanan Juni 2026", "PT Teknologi Nusantara"),
            (bca, cat_ids["Freelance & Konsultasi"], "income", 8000000.0, "Audit Keamanan Web & Cloud", "Client Jakarta"),
            (bca, cat_ids["Sewa Tempat & Hunian"], "expense", 6500000.0, "Sewa Apartemen Juni", "Building Management"),
            (bca, cat_ids["Tagihan & Utilitas"], "expense", 820000.0, "Listrik PLN & WiFi", "PLN Persero"),
            (bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 2400000.0, "Belanja Dapur & Supermarket", "GrandLucky"),
            (gopay, cat_ids["Makanan & Restoran"], "expense", 1650000.0, "Kuliner & Kopi Bulanan", "Berbagai Restoran"),
            (bca, cat_ids["Langganan Software & Cloud"], "expense", 650000.0, "Server Cloud DigitalOcean & AWS", "Cloud Provider"),
            (bca, cat_ids["Transportasi & Kendaraan"], "expense", 750000.0, "Bensin Shell & Tol", "Shell Stasiun"),
        ]),
        # July 2026
        ("2026-07", [
            (mandiri, cat_ids["Gaji & Penghasilan Tetap"], "income", 30000000.0, "Gaji Bulanan Juli 2026", "PT Teknologi Nusantara"),
            (bca, cat_ids["Freelance & Konsultasi"], "income", 11500000.0, "Pembuatan Aplikasi Mobile Flutter", "Studio Kreatif Bandung"),
            (bca, cat_ids["Sewa Tempat & Hunian"], "expense", 6500000.0, "Sewa Apartemen Juli", "Building Management"),
            (bca, cat_ids["Tagihan & Utilitas"], "expense", 890000.0, "Listrik PLN & WiFi", "PLN Persero"),
            (bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 2800000.0, "Belanja Bulanan & Buah Segar", "Lotte Mart"),
            (gopay, cat_ids["Makanan & Restoran"], "expense", 1850000.0, "Makan Siang & Pertemuan Klien", "Berbagai Kafe"),
            (bca, cat_ids["Langganan Software & Cloud"], "expense", 720000.0, "Figma, GitHub, DigitalOcean", "Tech SaaS"),
            (bca, cat_ids["Transportasi & Kendaraan"], "expense", 820000.0, "Bensin & Parkir Bandara", "Shell & Jasa Marga"),
        ]),
        # August 2026
        ("2026-08", [
            (mandiri, cat_ids["Gaji & Penghasilan Tetap"], "income", 32500000.0, "Gaji Bulanan Agustus 2026 (Kenaikan Gaji)", "PT Teknologi Nusantara"),
            (bibit, cat_ids["Dividen & Investasi"], "income", 1200000.0, "Dividen Portofolio Saham", "KSEI"),
            (bca, cat_ids["Sewa Tempat & Hunian"], "expense", 6500000.0, "Sewa Apartemen Agustus", "Building Management"),
            (bca, cat_ids["Tagihan & Utilitas"], "expense", 810000.0, "Listrik PLN & PAM", "PLN Persero"),
            (bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 2150000.0, "Belanja Kebutuhan Rumah Tangga", "GrandLucky"),
            (gopay, cat_ids["Makanan & Restoran"], "expense", 1450000.0, "Makan Malam & Kopi Kenangan", "GoFood"),
            (bca, cat_ids["Langganan Software & Cloud"], "expense", 680000.0, "Langganan Server & Claude AI Pro", "Anthropic / DO"),
            (bca, cat_ids["Transportasi & Kendaraan"], "expense", 650000.0, "Bensin Shell V-Power", "Shell BSD"),
        ]),
        # September 2026
        ("2026-09", [
            (mandiri, cat_ids["Gaji & Penghasilan Tetap"], "income", 32500000.0, "Gaji Bulanan September 2026", "PT Teknologi Nusantara"),
            (bca, cat_ids["Freelance & Konsultasi"], "income", 15000000.0, "Pengembangan Data Pipeline & SQLite API", "Fintech Studio Jakarta"),
            (bca, cat_ids["Sewa Tempat & Hunian"], "expense", 6500000.0, "Sewa Apartemen September", "Building Management"),
            (bca, cat_ids["Tagihan & Utilitas"], "expense", 840000.0, "Listrik & Internet Biznet", "PLN / Biznet"),
            (bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 2950000.0, "Belanja Sembako & Daging Segar", "Ranch Market"),
            (gopay, cat_ids["Makanan & Restoran"], "expense", 1920000.0, "Makan Bersama Keluarga & Rekan", "Restoran Lokal"),
            (bca, cat_ids["Langganan Software & Cloud"], "expense", 840000.0, "Cloud Servers, Domain, & SaaS", "DigitalOcean / AWS"),
            (bca, cat_ids["Kesehatan & Olahraga"], "expense", 650000.0, "Membership Gym Fitness First", "Fitness First"),
        ]),
        # October 2026
        ("2026-10", [
            (mandiri, cat_ids["Gaji & Penghasilan Tetap"], "income", 32500000.0, "Gaji Bulanan Oktober 2026", "PT Teknologi Nusantara"),
            (bca, cat_ids["Freelance & Konsultasi"], "income", 8500000.0, "Desain UI/UX Design System SaaS", "Client Singapore Ltd"),
            (bibit, cat_ids["Dividen & Investasi"], "income", 1450000.0, "Dividen Saham Kuartal 3", "KSEI / Bank Kustodian"),
            (bca, cat_ids["Sewa Tempat & Hunian"], "expense", 6500000.0, "Sewa Apartemen & Maintenance Bulanan", "Building Management"),
            (bca, cat_ids["Tagihan & Utilitas"], "expense", 1330000.0, "Tagihan Listrik PLN & Biznet", "PLN / Biznet"),
            (bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 4920000.0, "Belanja Bulanan Dapur & Perkakas", "GrandLucky & Ace Hardware"),
            (gopay, cat_ids["Makanan & Restoran"], "expense", 2450000.0, "Ramen Seirock-Ya & Kopi Artisan", "Seirock-Ya & Kopi Kenangan"),
            (bca, cat_ids["Langganan Software & Cloud"], "expense", 770000.0, "DigitalOcean, Google Workspace, Figma", "Cloud Providers"),
            (bca, cat_ids["Transportasi & Kendaraan"], "expense", 1200000.0, "Servis Berkala & Ganti Oli Astra", "Bengkel Resmi Astra"),
            (bca, cat_ids["Amal & Donasi"], "expense", 1000000.0, "Zakat Maal & Donasi Panti Asuhan", "KitaBisa"),
        ]),
        # November 2026 (Current)
        ("2026-11", [
            (mandiri, cat_ids["Gaji & Penghasilan Tetap"], "income", 32500000.0, "Gaji Bulanan November 2026", "PT Teknologi Nusantara"),
            (bca, cat_ids["Freelance & Konsultasi"], "income", 12000000.0, "Backend API & Database Optimization", "Fintech Studio Jakarta"),
            (bca, cat_ids["Sewa Tempat & Hunian"], "expense", 6500000.0, "Sewa Apartemen November 2026", "Building Management"),
            (bca, cat_ids["Tagihan & Utilitas"], "expense", 910000.0, "Listrik PLN Token & Air PAM", "PLN Persero"),
            (bca, cat_ids["Langganan Software & Cloud"], "expense", 540000.0, "Server VPS Cloud, GitHub Pro, Copilot", "DigitalOcean & GitHub"),
            (gopay, cat_ids["Makanan & Restoran"], "expense", 220000.0, "Makan Siang Ayam Taliwang & Kopi", "Ayam Taliwang & Anomali"),
        ])
    ]

    for month_str, tx_list in monthly_templates:
        day_counter = 1
        for acc_id, cat_id, tx_type, amount, desc, merchant in tx_list:
            day_str = f"{day_counter:02d}"
            tx_date = f"{month_str}-{day_str}"
            day_counter += 3
            model.create_transaction(acc_id, cat_id, tx_type, amount, tx_date, desc, merchant, "")

    conn.close()
    print("Full 6-month financial trajectory seeded successfully!")

if __name__ == "__main__":
    force = "--reseed" in sys.argv
    seed(force_reseed=force)
