from flask import Flask, render_template, request, jsonify
from textblob import TextBlob
import sqlite3
from pathlib import Path

app = Flask(__name__)
DATABASE = Path(__file__).with_name("reviews.db")


def init_db():
    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS reviews (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                product_name TEXT NOT NULL,
                review_text TEXT NOT NULL,
                sentiment TEXT NOT NULL,
                polarity REAL,
                subjectivity REAL,
                flagged INTEGER DEFAULT 0
            )
        """)


init_db()


@app.route("/")
def home():
    return render_template("login.html")


@app.route("/store")
def store():
    return render_template("store.html")


@app.route("/submit-review", methods=["POST"])
def submit_review():
    data = request.get_json(silent=True) or {}
    product = data.get("product", "").strip()
    text = data.get("text", "").strip()

    if not product or not text:
        return jsonify({"error": "Product name and review text are required"}), 400

    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    subjectivity = blob.sentiment.subjectivity
    text_lower = text.lower()

    complaint_keywords = [
        "broken", "defective", "bad", "poor", "worst", "delay",
        "damaged", "useless", "terrible", "horrible", "awful",
        "disappointed", "stop", "stopped", "didn't work", "doesn't work"
    ]
    has_negative_word = any(word in text_lower for word in complaint_keywords)

    low_ratings = ["1 star", "one star", "2 star", "two stars", "1/5", "2/5", "one / five"]
    has_low_rating = any(rating in text_lower for rating in low_ratings)

    high_ratings = [
        "5 star", "5 stars", "five star", "five stars", "4 star", "4 stars",
        "four star", "four stars", "5/5", "4/5", "five / five"
    ]
    has_high_rating = any(rating in text_lower for rating in high_ratings)

    is_negative = polarity < 0 or has_negative_word or has_low_rating
    is_positive = (polarity > 0.15 or has_high_rating) and not is_negative

    if is_positive:
        sentiment, color = "Positive", "success"
    elif is_negative:
        sentiment, color = "Negative", "danger"
    else:
        sentiment, color = "Neutral", "secondary"

    flagged = int(sentiment == "Negative")

    with sqlite3.connect(DATABASE) as conn:
        conn.execute("""
            INSERT INTO reviews
            (product_name, review_text, sentiment, polarity, subjectivity, flagged)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (product, text, sentiment, round(polarity, 2),
              round(subjectivity, 2), flagged))

    return jsonify({
        "sentiment": sentiment,
        "polarity": round(polarity, 2),
        "subjectivity": round(subjectivity, 2),
        "flagged": bool(flagged),
        "color": color
    })


@app.route("/analytics")
def analytics():
    with sqlite3.connect(DATABASE) as conn:
        total, positive, negative = conn.execute("""
            SELECT COUNT(*),
                   SUM(CASE WHEN sentiment = 'Positive' THEN 1 ELSE 0 END),
                   SUM(CASE WHEN sentiment = 'Negative' THEN 1 ELSE 0 END)
            FROM reviews
        """).fetchone()

        rows = conn.execute("""
            SELECT product_name, review_text, sentiment, polarity, flagged
            FROM reviews ORDER BY id DESC LIMIT 10
        """).fetchall()

    reviews = [{
        "product": row[0],
        "text": row[1],
        "sentiment": row[2],
        "polarity": row[3],
        "flagged": bool(row[4])
    } for row in rows]

    return jsonify({
        "total": total or 0,
        "positive": positive or 0,
        "negative": negative or 0,
        "reviews": reviews
    })


if __name__ == "__main__":
    app.run(debug=True)
