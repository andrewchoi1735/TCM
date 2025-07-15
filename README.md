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


The app automatically creates the database when it starts. Run it with
`python app.py` or `flask run` and a new `test_management.db` will appear under
`./instance` if it is missing.

If you previously ran the app before a model was added (for example the
`Project` table), remove the old `instance/test_management.db` so the new
schema can be created or use migrations to upgrade the database.

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
