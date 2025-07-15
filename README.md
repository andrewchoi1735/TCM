# TCM

This Flask-based Test Case Management application uses SQLAlchemy for data storage. 

## Configuration

The application reads configuration from environment variables with the following defaults:

- `SECRET_KEY`: defaults to `change-me`.
- `SQLALCHEMY_DATABASE_URI`: defaults to `sqlite:///test_management.db`.

Set these variables in your environment when running the app to customize the secret key and database location.

## Running

Create a virtual environment and install dependencies (Flask, Flask-Login, Flask-Migrate, SQLAlchemy). Then run:

```bash
python app.py
```

The database file will be created automatically if it does not exist.
