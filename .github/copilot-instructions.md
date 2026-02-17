# Gestion-Patrimoine: AI Agent Instructions

## Project Overview

**Gestion-Patrimoine** is a Django web application for enterprise asset (patrimoine) management and registration with secure authentication and GPX coordinate tracking capabilities.

- **Framework**: Django 6.0.2
- **Database**: Currently SQLite (development); MySQL config exists but commented out in `settings.py`
- **Language**: Python 3.14.2
- **Key Dependencies**: `mysql-connector-python`, `folium` (mapping), `python-decouple` (environment config)

## Critical Architecture Notes

### Project Structure
```
gestion_patrinoine/          # Main Django project directory
├── settings.py              # Configuration (uses python-decouple for SECRET_KEY, DEBUG)
├── urls.py                  # Root URL router (currently only admin path)
├── asgi.py, wsgi.py        # ASGI/WSGI entry points
└── __init__.py
manage.py                     # Django management CLI
.env                          # Environment variables (SECRET_KEY, DEBUG)
```

### Database Configuration
- **Current**: SQLite (`db.sqlite3`) in development
- **Commented MySQL config exists**: Lines 85-95 in `settings.py` show MySQL connector setup with `config()` variables for `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`
- **Pattern**: Configuration is environment-driven via `.env` file using `python-decouple`'s `config()` function

### No Apps Yet
The project has NO Django apps currently installed in `INSTALLED_APPS` beyond core Django modules. The command `python manage.py startapp geo` was attempted but failed (exit code 1). Future apps must be:
1. Created with `python manage.py startapp <app_name>`
2. Added to `INSTALLED_APPS` in `settings.py`
3. Registered in root `urls.py` via `include()`

## Essential Developer Workflows

### Setup
```bash
python3 -m venv .venv
source .venv/bin/activate          # macOS/Linux
pip install -r requirement.txt
```

### Running the Server
```bash
python manage.py runserver
# Access at http://127.0.0.1:8000 (verify exact URL in console output)
```

### Common Django Commands
```bash
python manage.py startapp <app_name>   # Create new app
python manage.py makemigrations         # Create migration files
python manage.py migrate                # Apply migrations to DB
python manage.py createsuperuser        # Create admin user
python manage.py shell                  # Interactive Python with Django context
```

## Project-Specific Patterns & Conventions

### Configuration Management
- **Pattern**: Use `python-decouple`'s `config()` function for all environment variables
- **Example** (from `settings.py`):
  ```python
  from decouple import config
  SECRET_KEY = config('SECRET_KEY')
  DEBUG = config('DEBUG')
  ```
- **All sensitive values must go in `.env`**, never hardcoded

### Future Database Migration
- MySQL configuration is partially prepared but commented out
- When switching to MySQL, uncomment lines 85-95 in `settings.py` and ensure `.env` contains: `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT`

### Mapping Integration
- `folium` library (v0.20.0) is included for GPX coordinate visualization
- Likely needed for patrimoine location mapping feature

## Cross-Component Communication

### Root URL Router (`urls.py`)
- **Current**: Only admin path configured
- **Pattern**: Apps should be included using:
  ```python
  from django.urls import include, path
  path('app_name/', include('app_name.urls')),
  ```

### Template Configuration
- Templates configured with `APP_DIRS: True` in `TEMPLATES` setting
- Apps should place templates in `<app_name>/templates/<app_name>/` directory (Django convention)

### Static Files
- Static files URL: `/static/`
- Apps should place CSS/JS in `<app_name>/static/<app_name>/` directory

## Common Pitfalls & Solutions

1. **"module not found" errors**: Always ensure virtual environment is activated and dependencies are installed via `pip install -r requirement.txt`
2. **Migration issues**: After adding models, always run `python manage.py makemigrations` before `migrate`
3. **DEBUG=True in production**: Ensure `.env` has `DEBUG=False` for production deployments
4. **Missing app registration**: After creating an app with `startapp`, add it to `INSTALLED_APPS` in `settings.py`

## Key Files to Reference

- `gestion_patrinoine/settings.py` — Configuration source of truth
- `.env` — Secrets and environment-specific settings
- `requirement.txt` — Dependency lock file (update here, not `pip freeze`)
- `README.md` — Installation and quick-start guide
