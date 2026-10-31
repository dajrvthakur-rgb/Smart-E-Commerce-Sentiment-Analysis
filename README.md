# MyStore Pro

## Files
- `app.py` — Flask routes and review sentiment analysis
- `templates/login.html` — existing login/register page
- `templates/store.html` — existing store/cart plus a small review form
- `reviews.db` — SQLite database for reviews
- `requirements.txt` — Python dependencies

## Run
1. Install Python 3.
2. Open a terminal in this folder.
3. Run `pip install -r requirements.txt`
4. Run `python app.py`
5. Open http://127.0.0.1:5000

Login/register and cart data still use browser `localStorage`, as in the original pages. Review analysis and analytics use Flask and SQLite.
