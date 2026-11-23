from functools import wraps
from pathlib import Path
import sqlite3
from flask import Flask, render_template, request, redirect, url_for, session, flash
from database import get_db, init_db
from recommender import predict_next_day_sales

BASE_DIR = Path(__file__).resolve().parent
app = Flask(__name__)
app.secret_key = "change-this-secret-key-before-deployment"

# Demo accounts for this educational project.
USERS = {
    "manager": {"password": "manager123", "role": "Manager", "name": "Charan"},
    "assistant": {"password": "sales123", "role": "Sales Assistant", "name": "Anusha Gaikwad"},
}

def login_required(view):
    @wraps(view)
    def wrapped(*args, **kwargs):
        if "username" not in session:
            flash("Please log in to continue.", "warning")
            return redirect(url_for("login"))
        return view(*args, **kwargs)
    return wrapped

def role_required(*roles):
    def decorator(view):
        @wraps(view)
        def wrapped(*args, **kwargs):
            if session.get("role") not in roles:
                flash("You do not have permission to perform that action.", "danger")
                return redirect(url_for("dashboard"))
            return view(*args, **kwargs)
        return wrapped
    return decorator

@app.context_processor
def inject_globals():
    return {"current_user": session.get("name"), "current_role": session.get("role")}

@app.route("/")
def index():
    return redirect(url_for("dashboard" if "username" in session else "login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username", "").strip().lower()
        password = request.form.get("password", "")
        user = USERS.get(username)
        if user and user["password"] == password:
            session.clear()
            session.update(username=username, role=user["role"], name=user["name"])
            flash(f"Welcome, {user['name']}!", "success")
            return redirect(url_for("dashboard"))
        flash("Invalid username or password.", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    flash("You have been logged out.", "info")
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    db = get_db()
    stats = {
        "products": db.execute("SELECT COUNT(*) FROM products").fetchone()[0],
        "low_stock": db.execute("SELECT COUNT(*) FROM products WHERE stock <= reorder_level").fetchone()[0],
        "sales_today": db.execute("SELECT COALESCE(SUM(total),0) FROM sales WHERE sale_date=date('now','localtime')").fetchone()[0],
        "sales_count": db.execute("SELECT COUNT(*) FROM sales").fetchone()[0],
    }
    low_products = db.execute("SELECT * FROM products WHERE stock <= reorder_level ORDER BY stock ASC LIMIT 8").fetchall()
    recent_sales = db.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 6").fetchall()
    forecast = predict_next_day_sales(db)
    db.close()
    return render_template("dashboard.html", stats=stats, low_products=low_products, recent_sales=recent_sales, forecast=forecast)

@app.route("/products")
@login_required
def products():
    db = get_db()
    q = request.args.get("q", "").strip()
    if q:
        rows = db.execute("SELECT * FROM products WHERE name LIKE ? OR sku LIKE ? OR category LIKE ? ORDER BY name", (f"%{q}%", f"%{q}%", f"%{q}%")).fetchall()
    else:
        rows = db.execute("SELECT * FROM products ORDER BY name").fetchall()
    low_products = db.execute("SELECT * FROM products WHERE stock <= reorder_level ORDER BY stock ASC").fetchall()
    db.close()
    return render_template("products.html", products=rows, low_products=low_products, q=q)

@app.route("/add-product", methods=["POST"])
@login_required
@role_required("Manager")
def add_product():
    sku = request.form.get("sku", "").strip().upper()
    name = request.form.get("name", "").strip()
    category = request.form.get("category", "").strip()
    supplier = request.form.get("supplier", "").strip()
    try:
        price = float(request.form.get("price", 0)); cost = float(request.form.get("cost", 0))
        stock = int(request.form.get("stock", 0)); reorder = int(request.form.get("reorder_level", 10))
        if not sku or not name or not category or price <= 0 or cost < 0 or stock < 0 or reorder < 0:
            raise ValueError
    except (ValueError, TypeError):
        flash("Enter valid product details. Selling price must be positive; stock and cost cannot be negative.", "danger")
        return redirect(url_for("products"))
    db = get_db()
    try:
        db.execute("INSERT INTO products(sku,name,category,price,cost,stock,reorder_level,supplier) VALUES(?,?,?,?,?,?,?,?)", (sku,name,category,price,cost,stock,reorder,supplier))
        db.commit()
        flash(f"{name} was added successfully.", "success")
    except sqlite3.IntegrityError:
        db.rollback(); flash("That SKU already exists. Please use a unique SKU.", "danger")
    finally:
        db.close()
    return redirect(url_for("products"))

@app.route("/restock", methods=["POST"])
@login_required
@role_required("Manager")
def restock():
    product_id = request.form.get("product_id", type=int)
    quantity = request.form.get("quantity", type=int)
    if not product_id or not quantity or quantity <= 0:
        flash("Enter a valid refill quantity.", "danger"); return redirect(url_for("products"))
    db = get_db()
    product = db.execute("SELECT name FROM products WHERE id=?", (product_id,)).fetchone()
    if not product:
        db.close(); flash("Product not found.", "danger"); return redirect(url_for("products"))
    db.execute("UPDATE products SET stock=stock+? WHERE id=?", (quantity, product_id))
    db.commit(); db.close()
    flash(f"Added {quantity} units to {product['name']}. Stock status has been refreshed.", "success")
    return redirect(url_for("products"))

@app.route("/sales", methods=["GET", "POST"])
@login_required
def sales():
    db = get_db()
    if request.method == "POST":
        product_id = request.form.get("product_id", type=int)
        quantity = request.form.get("quantity", type=int)
        customer_id = request.form.get("customer_id", type=int) or None
        if not product_id or not quantity or quantity <= 0:
            flash("Choose a product and enter a valid quantity.", "danger"); db.close(); return redirect(url_for("sales"))
        product = db.execute("SELECT * FROM products WHERE id=?", (product_id,)).fetchone()
        if not product or product["stock"] < quantity:
            flash("Product not found or insufficient stock.", "danger"); db.close(); return redirect(url_for("sales"))
        total = round(product["price"] * quantity, 2)
        try:
            cur = db.execute("INSERT INTO sales(customer_id,employee_name,total) VALUES(?,?,?)", (customer_id, session.get("name", "Staff"), total))
            db.execute("INSERT INTO sale_items(sale_id,product_id,quantity,unit_price,line_total) VALUES(?,?,?,?,?)", (cur.lastrowid, product_id, quantity, product["price"], total))
            db.execute("UPDATE products SET stock=stock-? WHERE id=?", (quantity, product_id))
            db.commit(); flash(f"Sale recorded. Total: ₹{total:,.2f}", "success")
        except sqlite3.Error:
            db.rollback(); flash("Could not record sale. Please try again.", "danger")
        db.close(); return redirect(url_for("sales"))
    product_rows = db.execute("SELECT * FROM products WHERE stock > 0 ORDER BY name").fetchall()
    customers = db.execute("SELECT * FROM customers ORDER BY name").fetchall()
    sale_rows = db.execute("SELECT * FROM sales ORDER BY id DESC LIMIT 30").fetchall()
    db.close()
    return render_template("sales.html", products=product_rows, customers=customers, sales=sale_rows)

@app.route("/customers")
@login_required
def customers():
    db = get_db(); rows = db.execute("SELECT * FROM customers ORDER BY name").fetchall(); db.close()
    return render_template("customers.html", customers=rows)

@app.route("/add-customer", methods=["POST"])
@login_required
@role_required("Manager")
def add_customer():
    name = request.form.get("name", "").strip()
    if not name:
        flash("Customer name is required.", "danger"); return redirect(url_for("customers"))
    db = get_db()
    db.execute("INSERT INTO customers(name,phone,email,address) VALUES(?,?,?,?)", (name, request.form.get("phone", "").strip(), request.form.get("email", "").strip(), request.form.get("address", "").strip()))
    db.commit(); db.close(); flash("Customer added successfully.", "success")
    return redirect(url_for("customers"))

@app.errorhandler(404)
def not_found(_error):
    return render_template("404.html"), 404

if __name__ == "__main__":
    init_db()
    app.run(debug=True)
