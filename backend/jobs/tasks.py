import os
import csv
import json
from datetime import datetime, timedelta

import requests
from werkzeug.utils import secure_filename
from backend.extensions import db
from backend.config import Config
from backend.models import Student, Company, Application, PlacementDrive, Interview

# The Celery instance is attached in run.py as `celery`. We import it here.
from run import celery


def _notify(message, webhook_url=None):
    webhook_url = webhook_url or Config.GCHAT_WEBHOOK_URL
    if webhook_url:
        try:
            requests.post(webhook_url, json={"text": message}, timeout=10)
            return True
        except requests.RequestException as e:
            print(f"[notify] webhook failed: {e}")
            return False
    # Fallback: log (stands in for email/SMS in a local demo)
    print(f"[NOTIFY] {message}")
    return True


@celery.task(name="backend.jobs.tasks.send_interview_reminders")
def send_interview_reminders():
    now = datetime.now()
    window_end = now + timedelta(hours=24)
    upcoming = (
        Interview.query
        .filter(Interview.scheduled_at >= now,
                Interview.scheduled_at <= window_end,
                Interview.reminder_sent.is_(False))
        .all()
    )
    sent = 0
    for iv in upcoming:
        student = iv.student
        email = student.user.email if student and student.user else "unknown"
        msg = (f"Reminder: {student.name}, you have an interview for "
               f"'{iv.drive.title}' on {iv.scheduled_at.strftime('%d/%m/%Y %H:%M')} "
               f"({iv.mode}). Contact: {email}")
        if _notify(msg):
            iv.reminder_sent = True
            sent += 1
    db.session.commit()
    return {"reminders_sent": sent, "checked": len(upcoming)}


@celery.task(name="backend.jobs.tasks.generate_monthly_report")
def generate_monthly_report():
    now = datetime.now()
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start = (first_of_this_month - timedelta(days=1)).replace(day=1)  # first of last month
    end = first_of_this_month

    drives = PlacementDrive.query.filter(
        PlacementDrive.created_at >= start, PlacementDrive.created_at < end
    ).count()
    apps = Application.query.filter(
        Application.applied_at >= start, Application.applied_at < end
    ).count()
    selected = Application.query.filter(
        Application.applied_at >= start,
        Application.applied_at < end,
        Application.application_status.in_(["Selected", "Placed"]),
    ).count()

    html = f"""<html><body>
    <h2>Monthly Placement Report — {start.strftime('%B %Y')}</h2>
    <ul>
      <li>Drives conducted: {drives}</li>
      <li>Applications received: {apps}</li>
      <li>Students selected: {selected}</li>
    </ul>
    <p>Generated {now.strftime('%d/%m/%Y %H:%M')}</p>
    </body></html>"""

    os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)
    path = os.path.join(Config.EXPORT_FOLDER,
                        f"monthly_report_{start.strftime('%Y_%m')}.html")
    with open(path, "w") as fh:
        fh.write(html)

    _notify(f"Monthly report for {start.strftime('%B %Y')} generated: {path}")
    return {"report_path": path, "drives": drives, "applications": apps, "selected": selected}


@celery.task(name="backend.jobs.tasks.export_applications_csv", bind=True)
def export_applications_csv(self, student_id):
    """User-triggered async export of a student's application history to CSV."""
    student = Student.query.get(student_id)
    if not student:
        return {"error": "student not found"}

    os.makedirs(Config.EXPORT_FOLDER, exist_ok=True)
    stamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    short_id = str(self.request.id)[:8]
    safe_roll = secure_filename(student.roll_number or f"student{student_id}")
    filename = f"applications_{safe_roll}_{stamp}_{short_id}.csv"
    path = os.path.join(Config.EXPORT_FOLDER, filename)

    apps = Application.query.filter_by(student_id=student_id).all()
    with open(path, "w", newline="") as fh:
        writer = csv.writer(fh)
        writer.writerow(["Student ID", "Company Name", "Drive Title",
                         "Application Status", "Applied Date"])
        for a in apps:
            writer.writerow([
                student_id,
                a.drive.company.company_name if a.drive and a.drive.company else "",
                a.drive.title if a.drive else "",
                a.application_status,
                a.applied_at.strftime("%Y-%m-%d") if a.applied_at else "",
            ])

    _notify(f"CSV export ready for {student.name}: {filename} ({len(apps)} rows)")
    return {"filename": filename, "rows": len(apps)}