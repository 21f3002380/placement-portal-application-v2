import os
import csv
import json
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timedelta

import requests
from werkzeug.utils import secure_filename
from backend.extensions import db
from backend.config import Config
from backend.models import Student, Company, Application, PlacementDrive, Interview, Placement

# The Celery instance is attached in run.py as `celery`. We import it here.
from run import celery


def _send_email(to_email, subject, body, html=False):
    if not to_email:
        return False
    msg = MIMEText(body, "html" if html else "plain")
    msg["Subject"] = subject
    msg["From"] = Config.SMTP_FROM
    msg["To"] = to_email
    try:
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT, timeout=10) as server:
            if Config.SMTP_USE_TLS:
                server.starttls()
            if Config.SMTP_USERNAME:
                server.login(Config.SMTP_USERNAME, Config.SMTP_PASSWORD)
            server.send_message(msg)
        return True
    except (smtplib.SMTPException, OSError) as e:
        print(f"[email] failed to send to {to_email}: {e}")
        return False


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
        email = student.user.email if student and student.user else None
        subject = f"Interview Reminder: {iv.drive.title}"
        body = (
            f"Hi {student.name},\n\n"
            f"This is a reminder that you have an interview scheduled:\n\n"
            f"  Drive:     {iv.drive.title}\n"
            f"  Role:      {iv.drive.job_role}\n"
            f"  Company:   {iv.drive.company.company_name if iv.drive.company else '-'}\n"
            f"  When:      {iv.scheduled_at.strftime('%d/%m/%Y %H:%M')}\n"
            f"  Mode:      {iv.mode}\n"
            f"  Location:  {iv.location or '-'}\n\n"
            f"Good luck!\nPlacement Cell"
        )
        emailed = _send_email(email, subject, body)
        logged = _notify(f"[Interview reminder] {student.name} <{email}> — {iv.drive.title} "
                         f"on {iv.scheduled_at.strftime('%d/%m/%Y %H:%M')} (emailed={emailed})")
        if emailed or logged:
            iv.reminder_sent = True
            sent += 1
    db.session.commit()
    return {"reminders_sent": sent, "checked": len(upcoming)}


@celery.task(name="backend.jobs.tasks.generate_monthly_report")
def generate_monthly_report():
    now = datetime.now()
    first_of_this_month = now.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    start = (first_of_this_month - timedelta(days=1)).replace(day=1)
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
    with open(path, "w", encoding="utf-8") as fh:
        fh.write(html)

    from backend.models import User
    admin = User.query.filter_by(role="admin").first()
    admin_email = admin.email if admin else None
    emailed = _send_email(admin_email,
                          f"Monthly Placement Report — {start.strftime('%B %Y')}",
                          html, html=True)
    _notify(f"Monthly report for {start.strftime('%B %Y')} generated: {path} "
           f"(emailed to admin={emailed})")
    return {"report_path": path, "drives": drives, "applications": apps,
           "selected": selected, "emailed": emailed}


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
    with open(path, "w", newline="", encoding="utf-8") as fh:
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


@celery.task(name="backend.jobs.tasks.generate_offer_letter", bind=True)
def generate_offer_letter(self, placement_id):
    """
    Triggered when a company marks an application Selected/Placed.
    Generates a simple HTML placement-confirmation "offer letter",
    saves it so the student can download it later, and emails a copy.
    """
    placement = Placement.query.get(placement_id)
    if not placement:
        return {"error": "placement not found"}

    student = placement.student
    company = placement.company

    os.makedirs(Config.OFFER_FOLDER, exist_ok=True)
    safe_roll = secure_filename(student.roll_number or f"student{student.id}")
    filename = f"offer_{safe_roll}_{placement.id}.html"
    path = os.path.join(Config.OFFER_FOLDER, filename)

    salary_line = f"₹{placement.salary:.2f} LPA" if placement.salary else "as discussed"
    joining_line = placement.joining_date.strftime("%d %B %Y") if placement.joining_date else "To be confirmed"

    html = f"""<html><body style="font-family: Georgia, serif; max-width: 600px; margin: 2rem auto;">
    <h2 style="color:#223247;">Placement Confirmation</h2>
    <p>Dear {student.name},</p>
    <p>Congratulations! We are pleased to confirm your placement with the following details:</p>
    <table style="border-collapse: collapse; width: 100%;">
      <tr><td style="padding:6px 0;"><b>Company</b></td><td>{company.company_name if company else '-'}</td></tr>
      <tr><td style="padding:6px 0;"><b>Position</b></td><td>{placement.position or '-'}</td></tr>
      <tr><td style="padding:6px 0;"><b>Compensation</b></td><td>{salary_line}</td></tr>
      <tr><td style="padding:6px 0;"><b>Joining Date</b></td><td>{joining_line}</td></tr>
    </table>
    <p style="margin-top:2rem;">This letter serves as a placement confirmation issued by the Institute
    Placement Cell on behalf of {company.company_name if company else 'the company'}.</p>
    <p>Congratulations once again!<br/>Placement Cell</p>
    </body></html>"""

    with open(path, "w",encoding="utf-8") as fh:
        fh.write(html)

    placement.offer_filename = filename
    db.session.commit()

    student_email = student.user.email if student and student.user else None
    emailed = _send_email(student_email,
                          f"Placement Confirmation — {company.company_name if company else ''}",
                          html, html=True)
    _notify(f"Offer letter generated for {student.name}: {filename} (emailed={emailed})")
    return {"filename": filename, "emailed": emailed}