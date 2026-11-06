"""Realistic seed data generator for Valuta Financial Dashboard."""

import os
from datetime import datetime, timedelta
from app.database import get_db, init_db
from app.models import FinanceModel

def seed():
    init_db()
    conn = get_db()
    model = FinanceModel(conn)

    print("Checking existing records...")
    existing = model.get_accounts()
    if existing:
        print(f"Database already contains {len(existing)} accounts. Skipping full seed.")
        conn.close()
        return

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
        ("BCA Rekening Operasional", "bank", "Bank Central Asia", 28500000.0, "8820-412-991", "#005baa"),
        ("Mandiri Tabungan Utama", "bank", "Bank Mandiri", 45000000.0, "137-00-19283-4", "#002b66"),
        ("GoPay & GoPay Tabungan", "ewallet", "GoTo Financial", 3250000.0, "0812-9988-7711", "#00aa13"),
        ("Bibit Portofolio Investasi", "investment", "PT Bibit Tumbuh Bersama", 68400000.0, "RD-BIBIT-9821", "#10b981"),
        ("Kas Tunai & Brankas", "cash", "Dompet Fisik", 2400000.0, "-", "#475569"),
    ]

    acc_ids = {}
    for name, a_type, inst, init_bal, acc_num, color in accounts_data:
        aid = model.create_account(name, a_type, inst, init_bal, acc_num, color)
        acc_ids[name] = aid

    print("Seeding monthly category budgets for 2026-11 and 2026-10...")
    months = ["2026-10", "2026-11"]
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
        ("Dana Darurat 6 Bulan", 90000000.0, 68400000.0, "2027-06-30", "#057a55"),
        ("Renovasi Ruang Kerja Minimalis", 25000000.0, 18500000.0, "2026-12-31", "#2563eb"),
        ("Ekspansi Bisnis Server Lokal", 40000000.0, 12000000.0, "2027-03-31", "#7c3aed"),
    ]
    for title, target, current, target_dt, color in savings_data:
        model.create_savings_goal(title, target, current, target_dt, color)

    print("Seeding realistic transaction history (last 45 days)...")
    bca = acc_ids["BCA Rekening Operasional"]
    mandiri = acc_ids["Mandiri Tabungan Utama"]
    gopay = acc_ids["GoPay & GoPay Tabungan"]
    bibit = acc_ids["Bibit Portofolio Investasi"]
    tunai = acc_ids["Kas Tunai & Brankas"]

    # Generate dates
    today = datetime.now()
    tx_entries = [
        # Incomes
        (-35, mandiri, cat_ids["Gaji & Penghasilan Tetap"], "income", 32500000.0, "Gaji Bulanan Oktober 2026", "PT Teknologi Nusantara", "Payroll resmi"),
        (-32, bca, cat_ids["Freelance & Konsultasi"], "income", 8500000.0, "Desain UI/UX Design System SaaS", "Client Singapore Ltd", "Invoice #INV-2026-88"),
        (-25, bibit, cat_ids["Dividen & Investasi"], "income", 1450000.0, "Dividen Saham Kuartal 3", "KSEI / Bank Kustodian", "Pajak 10% potong"),
        (-5, mandiri, cat_ids["Gaji & Penghasilan Tetap"], "income", 32500000.0, "Gaji Bulanan November 2026", "PT Teknologi Nusantara", "Payroll resmi"),
        (-2, bca, cat_ids["Freelance & Konsultasi"], "income", 12000000.0, "Backend API & Database Optimization", "Fintech Studio Jakarta", "Termin 1"),

        # Expenses - Housing & Utilities
        (-34, bca, cat_ids["Sewa Tempat & Hunian"], "expense", 6500000.0, "Sewa Apartemen & Maintenance Bulanan", "Building Management", "Tower B Lt 18"),
        (-33, bca, cat_ids["Tagihan & Utilitas"], "expense", 850000.0, "Tagihan Listrik PLN Pascabayar", "PLN Persero", "IDPEL 5321889912"),
        (-33, bca, cat_ids["Tagihan & Utilitas"], "expense", 480000.0, "Internet Fiber Optik 100Mbps", "Biznet Networks", "No Pelanggan BZ-9912"),
        (-3, bca, cat_ids["Sewa Tempat & Hunian"], "expense", 6500000.0, "Sewa Apartemen November 2026", "Building Management", "Lunas tepat waktu"),
        (-3, bca, cat_ids["Tagihan & Utilitas"], "expense", 910000.0, "Listrik PLN Token & Air PAM", "PLN Persero", "Token 1jt"),

        # Expenses - Groceries & Food
        (-30, bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 1850000.0, "Belanja Bulanan Dapur & Buah", "GrandLucky Superstore", "Kebutuhan 2 minggu"),
        (-28, gopay, cat_ids["Makanan & Restoran"], "expense", 135000.0, "Makan Siang Nasi Padang Garuda", "RM Garuda Sabang", "Makan bersama tim"),
        (-27, gopay, cat_ids["Makanan & Restoran"], "expense", 85000.0, "Kopi Artisan & Toast", "Kopi Kenangan Mantan", "Espresso double"),
        (-24, bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 1420000.0, "Belanja Sayur Organik & Protein", "Ranch Market Pondok Indah", ""),
        (-22, gopay, cat_ids["Makanan & Restoran"], "expense", 240000.0, "Makan Malam Ramen Seirock-Ya", "Seirock-Ya Ramen", "Toripaitan Extreme"),
        (-18, tunai, cat_ids["Makanan & Restoran"], "expense", 65000.0, "Sate Khas Senayan", "Sate Khas Senayan", "Tunai"),
        (-14, bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 1650000.0, "Stok Sembako & Perlengkapan Rumah", "Lotte Mart Wholesale", ""),
        (-10, gopay, cat_ids["Makanan & Restoran"], "expense", 180000.0, "Brunch Akhir Pekan", "Common Grounds Coffee", "Eggs Benedict"),
        (-6, bca, cat_ids["Kebutuhan Pokok & Belanja"], "expense", 1950000.0, "Belanja Daging & Buah Segar Awal Bulan", "GrandLucky Superstore", "Kebutuhan November"),
        (-4, gopay, cat_ids["Makanan & Restoran"], "expense", 95000.0, "Kopi & Roti Bakar", "Anomali Coffee", "Work from cafe"),
        (-1, gopay, cat_ids["Makanan & Restoran"], "expense", 125000.0, "Makan Siang Ayam Bakar Taliwang", "Ayam Taliwang Rinjani", "GoFood delivery"),

        # Expenses - Tech & Cloud Subscriptions
        (-31, bca, cat_ids["Langganan Software & Cloud"], "expense", 320000.0, "Server VPS Cloud & Domain", "DigitalOcean Cloud", "3 Droplets"),
        (-30, bca, cat_ids["Langganan Software & Cloud"], "expense", 210000.0, "Google Workspace & Storage 2TB", "Google Cloud Indonesia", "Workspace Pro"),
        (-26, bca, cat_ids["Langganan Software & Cloud"], "expense", 240000.0, "Figma Professional Plan", "Figma Inc", "Annual billing"),
        (-2, bca, cat_ids["Langganan Software & Cloud"], "expense", 345000.0, "Server VPS Cloud & AI API Credits", "Anthropic / DigitalOcean", "API Usage November"),
        (-1, bca, cat_ids["Langganan Software & Cloud"], "expense", 195000.0, "GitHub Pro & Copilot Developer", "GitHub Inc", "Subscription"),

        # Expenses - Transport & Fuel
        (-29, bca, cat_ids["Transportasi & Kendaraan"], "expense", 450000.0, "Bensin Full Tank V-Power Nitro+", "Shell Stasiun BSD", "Oktan 98"),
        (-21, gopay, cat_ids["Transportasi & Kendaraan"], "expense", 120000.0, "Tol Trans Jawa & Parkir Bandara", "Jasa Marga E-Toll", "Top up Flazz"),
        (-15, bca, cat_ids["Transportasi & Kendaraan"], "expense", 450000.0, "Bensin Shell V-Power", "Shell Gatot Subroto", ""),
        (-7, bca, cat_ids["Transportasi & Kendaraan"], "expense", 750000.0, "Servis Berkala & Ganti Oli Mesin", "Bengkel Resmi Astra", "10.000 KM"),

        # Expenses - Entertainment & Health
        (-20, bca, cat_ids["Kesehatan & Olahraga"], "expense", 650000.0, "Membership Gym & Kolam Renang", "Fitness First Mega Kuningan", "Bulanan"),
        (-19, bca, cat_ids["Hiburan & Edukasi"], "expense", 186000.0, "Netflix Premium 4K UHD", "Netflix Indonesia", "Autodebit"),
        (-12, bca, cat_ids["Hiburan & Edukasi"], "expense", 54990.0, "Spotify Family Subscription", "Spotify AB", "Autodebit"),
        (-8, bca, cat_ids["Amal & Donasi"], "expense", 500000.0, "Donasi Panti Asuhan & Beasiswa", "Yayasan KitaBisa", "Zakat maal"),
    ]

    for days_ago, acc_id, cat_id, tx_type, amount, desc, merchant, notes in tx_entries:
        tx_date = (today + timedelta(days=days_ago)).strftime("%Y-%m-%d")
        model.create_transaction(acc_id, cat_id, tx_type, amount, tx_date, desc, merchant, notes)

    conn.close()
    print("Database seeding completed with realistic financial dataset!")

if __name__ == "__main__":
    seed()
