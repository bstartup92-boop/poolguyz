# Poolguyz Flask website

## Start the website

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000` for the website and `http://127.0.0.1:5000/admin` for the admin area.

On the first admin visit, create a password of at least eight characters. The admin dashboard lets you add, edit, hide, reorder, and delete services, recent work, and reviews. Recent-work images can be uploaded directly or added using a public image URL.

The SQLite database is created automatically in `instance/poolguyz.db`. For production, set a permanent `SECRET_KEY` environment variable and serve the Flask app through a production WSGI server.
