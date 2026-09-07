"""
Local development entry point.

Production runs `gunicorn "run:app"` — the Flask dev server is never
used outside this file's __main__ guard.
"""

from app import create_app

app = create_app()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
