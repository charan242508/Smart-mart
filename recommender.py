from datetime import date, timedelta
from sklearn.ensemble import RandomForestRegressor
import pandas as pd

def predict_next_day_sales(db):
    """Train a small demo model on daily revenue. With little history, return a transparent baseline."""
    rows = db.execute("SELECT sale_date, SUM(total) revenue FROM sales GROUP BY sale_date ORDER BY sale_date").fetchall()
    if len(rows) < 5:
        average = float(sum(r["revenue"] for r in rows) / len(rows)) if rows else 0.0
        return {"amount": round(average, 2), "method": "Average baseline", "note": "Record at least 5 distinct sales dates for a basic ML forecast."}
    df = pd.DataFrame([dict(r) for r in rows])
    df["sale_date"] = pd.to_datetime(df["sale_date"], errors="coerce")
    df = df.dropna().sort_values("sale_date")
    df["day_number"] = (df["sale_date"] - df["sale_date"].min()).dt.days
    df["weekday"] = df["sale_date"].dt.weekday
    X = df[["day_number", "weekday"]]
    y = df["revenue"].astype(float)
    model = RandomForestRegressor(n_estimators=100, random_state=42)
    model.fit(X, y)
    tomorrow = date.today() + timedelta(days=1)
    day_number = (pd.Timestamp(tomorrow) - df["sale_date"].min()).days
    amount = max(0, float(model.predict(pd.DataFrame([{"day_number": day_number, "weekday": tomorrow.weekday()}]))[0]))
    return {"amount": round(amount, 2), "method": "Random Forest Regression", "note": "Estimate based on recorded daily sales; accuracy improves with more history."}
