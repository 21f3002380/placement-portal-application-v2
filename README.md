# Placement Portal Application — V2

A campus recruitment portal built for the Modern Application Development II
project. It connects three roles — **Admin** (institute placement cell),
**Company**, and **Student** — so placement drives, applications, interviews,
and placement records can be managed in one system instead of spreadsheets
and email.

## Roles

- **Admin** — pre-seeded superuser. Approves/rejects companies and placement
  drives, manages and searches students & companies, blacklists accounts,
  views placement reports.
- **Company** — registers a profile (approved by admin before first login),
  creates placement drives, reviews applications, shortlists/selects
  candidates, schedules interviews.
- **Student** — self-registers, browses and applies to approved drives,
  tracks application status and interview schedule, maintains a profile and
  resume.

## Tech stack

- **Backend:** Flask (JSON API only)
- **Frontend:** Vue 3 (via CDN)
- **Auth:** JWT-based, role-based access control
- **Database:** SQLite (created programmatically via SQLAlchemy)
- **Caching:** Redis
- **Background jobs:** Celery + Redis (interview reminders, monthly reports,
  async CSV export)
- **Styling:** Bootstrap 5

## Author

Sreevatsan T · 21f3002380 · Modern Application Development II