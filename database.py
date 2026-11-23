import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).with_name("smartmart.db")

def get_db():
    db = sqlite3.connect(DB_PATH)
    db.row_factory = sqlite3.Row
    db.execute("PRAGMA foreign_keys = ON")
    return db

def init_db():
    db = get_db()
    db.executescript("""
    CREATE TABLE IF NOT EXISTS products(
        id INTEGER PRIMARY KEY AUTOINCREMENT, sku TEXT UNIQUE NOT NULL, name TEXT NOT NULL,
        category TEXT NOT NULL, price REAL NOT NULL, cost REAL NOT NULL, stock INTEGER NOT NULL DEFAULT 0,
        reorder_level INTEGER NOT NULL DEFAULT 10, supplier TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS customers(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, phone TEXT DEFAULT '',
        email TEXT DEFAULT '', address TEXT DEFAULT '', created_at TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS employees(
        id INTEGER PRIMARY KEY AUTOINCREMENT, name TEXT NOT NULL, role TEXT NOT NULL,
        phone TEXT DEFAULT '', email TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS sales(
        id INTEGER PRIMARY KEY AUTOINCREMENT, customer_id INTEGER,
        sale_date TEXT DEFAULT (date('now','localtime')), employee_name TEXT NOT NULL,
        total REAL NOT NULL, FOREIGN KEY(customer_id) REFERENCES customers(id));
    CREATE TABLE IF NOT EXISTS sale_items(
        id INTEGER PRIMARY KEY AUTOINCREMENT, sale_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
        quantity INTEGER NOT NULL, unit_price REAL NOT NULL, line_total REAL NOT NULL,
        FOREIGN KEY(sale_id) REFERENCES sales(id), FOREIGN KEY(product_id) REFERENCES products(id));
    """)
    if db.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
        products = [
            ("GRO001","Basmati Rice 5kg","Groceries",520,430,35,8,"FreshFields Distributors"),
            ("GRO002","Wheat Flour 5kg","Groceries",245,190,40,10,"FreshFields Distributors"),
            ("DAI001","Milk 1L","Dairy",62,48,50,12,"DailyDairy Co."),
            ("DAI002","Butter 500g","Dairy",285,230,18,6,"DailyDairy Co."),
            ("BEV001","Orange Juice 1L","Beverages",120,85,22,6,"Sunrise Beverages"),
            ("SNK001","Potato Chips","Snacks",30,18,80,20,"SnackHub"),
            ("HOU001","Laundry Detergent 1kg","Household",155,112,25,8,"CleanHome Supply"),
            ("PER001","Shampoo 180ml","Personal Care",135,92,20,6,"CarePlus Supply"),
            ("FRU001","Apples 1kg","Fresh Produce",180,125,30,10,"GreenBasket Farm"),
            ("BAK001","Bread Loaf","Bakery",45,28,26,8,"DailyBake"),
            ("FRO001","Frozen Peas 500g","Frozen Foods",95,68,16,5,"FrostLine"),
            ("ELE001","LED Bulb 9W","Electronics",110,72,25,12,"BrightLife")
        ]
        db.executemany("""INSERT INTO products(sku,name,category,price,cost,stock,reorder_level,supplier)
            VALUES(?,?,?,?,?,?,?,?)""", products)
    if db.execute("SELECT COUNT(*) FROM employees").fetchone()[0] == 0:
        db.executemany("INSERT INTO employees(name,role,phone,email) VALUES(?,?,?,?)", [
            ("Priya Sharma","Manager","9000000001","priya@smartmart.example"),
            ("Rahul Verma","Sales Assistant","9000000002","rahul@smartmart.example"),
            ("Ananya Singh","Inventory Assistant","9000000003","ananya@smartmart.example")
        ])
    if db.execute("SELECT COUNT(*) FROM customers").fetchone()[0] == 0:
        db.executemany("INSERT INTO customers(name,phone,email,address) VALUES(?,?,?,?)", [
            ("Aarav Patel","9111111111","aarav@example.com","Demo address, India"),
            ("Meera Reddy","9222222222","meera@example.com","Demo address, India"),
            ("Walk-in Demo","", "", "")
        ])
    db.commit()
    db.close()
