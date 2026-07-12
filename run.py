"""
Entry point.

Run the web app:      python run.py
Run a Celery worker:  celery -A run.celery worker --loglevel=info
Run Celery beat:      celery -A run.celery beat --loglevel=info
"""
from backend.app import create_app, seed_admin
from backend.celery_app import make_celery

app = create_app()
celery = make_celery(app)

# Ensure task module is imported so tasks register with this celery instance.
# (Imported lazily to avoid circular import at module top.)
def _register_tasks():
    import backend.jobs.tasks  # noqa: F401


_register_tasks()

if __name__ == "__main__":
    seed_admin(app)
    app.run(host="0.0.0.0", port=5000, debug=True, use_reloader=False)
