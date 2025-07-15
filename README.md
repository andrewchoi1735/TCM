# TCM

TCM is a Flask based Test Case Management application that stores data using SQLAlchemy.

## Installation

1. Create and activate a virtual environment (Python 3.8+):
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
2. Install the required packages:
   ```bash
   pip install Flask Flask-Login Flask-Migrate Flask-SQLAlchemy
   ```
   These commands also install `Werkzeug` and other transitive dependencies used by the app.

## Configuration

The application reads configuration from environment variables with the following defaults:

- `SECRET_KEY` – defaults to `change-me`.
- `SQLALCHEMY_DATABASE_URI` – defaults to `sqlite:///test_management.db`.

Set these variables when running the app if you need to customize the secret key or database location.

## Database initialization

The bundled `app.py` automatically creates the database if it does not exist:

```bash
python app.py  # creates test_management.db under ./instance
```

If you prefer using migrations, initialize them before running:

```bash
flask db init
flask db migrate -m "initial"
flask db upgrade
```

## Running

Start the Flask development server:

```bash
python app.py
```

The application listens on <http://localhost:5000> by default.

## Importing XML test cases

After logging in, navigate to `/upload_xml` to upload a JUnit-style
`<testsuite>` or `<testsuites>` file (up to 2MB). Uploaded files are
processed and then removed. Duplicate cases are skipped with a warning.
