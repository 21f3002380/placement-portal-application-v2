from celery import Celery
from celery.schedules import crontab


def make_celery(flask_app):
    celery = Celery(
        flask_app.import_name,
        broker=flask_app.config["CELERY_BROKER_URL"],
        backend=flask_app.config["CELERY_RESULT_BACKEND"],
    )
    celery.conf.update(
        timezone="Asia/Kolkata",
        enable_utc=False,
        beat_schedule={
            "daily-interview-reminders": {
                "task": "backend.jobs.tasks.send_interview_reminders",
                # every day at 08:00 IST
                "schedule": crontab(hour=8, minute=0),
                #"schedule": crontab(minute="*"),
            },
            "monthly-admin-report": {
                "task": "backend.jobs.tasks.generate_monthly_report",
                # 1st of every month at 06:00 IST
                "schedule": crontab(day_of_month=1, hour=6, minute=0),
                #"schedule": crontab(minute="*/2"),
            },
        },
    )

    class ContextTask(celery.Task):
        def __call__(self, *args, **kwargs):
            with flask_app.app_context():
                return self.run(*args, **kwargs)

    celery.Task = ContextTask
    return celery
