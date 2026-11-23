# SmartMart Sales Prediction & Management Dashboard

A Flask + SQLite educational supermarket management project. Includes manager and sales-assistant access, product inventory, low-stock alerts, restocking, new product entry, customer records, sales entry with automatic stock deduction, and a Random Forest sales forecast (with a baseline when there is not enough history).

## Run on Windows using VS Code

1. Extract `SmartMart_Complete_Project.zip`.
2. Open the extracted `SmartMart_Complete_Project` folder in VS Code.
3. Open Terminal → New Terminal.
4. Create a virtual environment:
   ```powershell
   python -m venv .venv
   ```
5. Activate it:
   ```powershell
   .\.venv\Scripts\Activate.ps1
   ```
6. Install dependencies:
   ```powershell
   python -m pip install -r requirements.txt
   ```
7. Start the app:
   ```powershell
   python app.py
   ```
8. Open http://127.0.0.1:5000 in your browser.

If `python` is not recognized, use the full path to your Python executable for the commands above.

## Demo login

- Manager: `manager` / `manager123`
- Sales Assistant: `assistant` / `sales123`

## Inventory workflow

- Manager → Products & Inventory → Add New Product to create a product with a unique SKU.
- Low-stock items are identified when `stock <= reorder_level`.
- Manager → Products & Inventory → Refill Stock to add units to the selected existing product.
- The low-stock status is recalculated automatically from the current stock and reorder level.
- Recording a sale deducts the sold quantity from stock. The application prevents a sale when available stock is insufficient.

## Database

`database.py` uses `smartmart.db` in the project folder and seeds demo data only if the products table is empty. Your uploaded SmartMart database has been included as `smartmart.db`, so the project starts with that database and its existing records. An additional backup copy is included under `data/smartmart_original_backup.db`.

## Important security note

This is a college/demo application. Demo passwords are hard-coded and the Flask secret key is a placeholder. Before real deployment, use password hashing, environment-based secrets, CSRF protection, stronger validation, HTTPS, backups, and audit logging. Do not use sample customer information as real customer data.
