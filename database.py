"""SQLite database models and helpers for patients, reports, and memory."""
import sqlite3
import json
import hashlib
import os
from datetime import datetime
from config import SQLITE_DB_PATH


def get_db():
    """Get a database connection."""
    conn = sqlite3.connect(SQLITE_DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


def create_tables():
    """Create all required tables."""
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS patients (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            email TEXT UNIQUE NOT NULL,
            password_hash TEXT NOT NULL,
            dob TEXT,
            gender TEXT,
            phone TEXT,
            blood_group TEXT,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS reports (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            filename TEXT NOT NULL,
            original_filename TEXT NOT NULL,
            upload_date TEXT DEFAULT CURRENT_TIMESTAMP,
            report_type TEXT DEFAULT 'Blood Test',
            parsed_data TEXT,
            ai_explanation TEXT,
            diet_plan TEXT,
            insights TEXT,
            chart_data TEXT,
            status TEXT DEFAULT 'pending',
            FOREIGN KEY (patient_id) REFERENCES patients(id)
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS memory (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER NOT NULL,
            report_id INTEGER,
            role TEXT NOT NULL,
            content TEXT NOT NULL,
            created_at TEXT DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (patient_id) REFERENCES patients(id),
            FOREIGN KEY (report_id) REFERENCES reports(id)
        )
    """)

    conn.commit()
    conn.close()


def hash_password(password):
    """Hash a password using SHA-256."""
    return hashlib.sha256(password.encode()).hexdigest()


def seed_demo_data():
    """Seed database with demo patients for testing."""
    conn = get_db()
    cursor = conn.cursor()

    # Check if demo data already exists
    cursor.execute("SELECT COUNT(*) FROM patients")
    count = cursor.fetchone()[0]
    if count > 0:
        conn.close()
        return

    demo_patients = [
        ("Richard Kumar", "richard@demo.com", hash_password("demo123"),
         "1985-06-15", "Male", "+91 98765 43210", "O+"),
        ("Priya Sharma", "priya@demo.com", hash_password("demo123"),
         "1990-03-22", "Female", "+91 98765 43211", "B+"),
        ("Arun Raj", "arun@demo.com", hash_password("demo123"),
         "1978-11-08", "Male", "+91 98765 43212", "A+"),
    ]

    for patient in demo_patients:
        cursor.execute("""
            INSERT INTO patients (name, email, password_hash, dob, gender, phone, blood_group)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, patient)

    conn.commit()
    conn.close()


def authenticate_patient(email, password):
    """Authenticate a patient by email and password."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM patients WHERE email = ? AND password_hash = ?",
        (email, hash_password(password))
    )
    patient = cursor.fetchone()
    conn.close()
    if patient:
        return dict(patient)
    return None


def get_patient_by_id(patient_id):
    """Get patient by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM patients WHERE id = ?", (patient_id,))
    patient = cursor.fetchone()
    conn.close()
    if patient:
        return dict(patient)
    return None


def get_all_patients():
    """Get all patients."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, email, dob, gender, phone, blood_group FROM patients")
    patients = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return patients


def add_report(patient_id, filename, original_filename, report_type="Blood Test"):
    """Add a new report for a patient."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO reports (patient_id, filename, original_filename, report_type)
        VALUES (?, ?, ?, ?)
    """, (patient_id, filename, original_filename, report_type))
    report_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return report_id


def update_report(report_id, **kwargs):
    """Update report fields."""
    conn = get_db()
    cursor = conn.cursor()
    for key, value in kwargs.items():
        if isinstance(value, (dict, list)):
            value = json.dumps(value)
        cursor.execute(f"UPDATE reports SET {key} = ? WHERE id = ?", (value, report_id))
    conn.commit()
    conn.close()


def get_reports_for_patient(patient_id):
    """Get all reports for a patient."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT * FROM reports WHERE patient_id = ? ORDER BY upload_date DESC",
        (patient_id,)
    )
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reports


def get_report_by_id(report_id):
    """Get a single report by ID."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM reports WHERE id = ?", (report_id,))
    report = cursor.fetchone()
    conn.close()
    if report:
        return dict(report)
    return None


def get_all_reports():
    """Get all reports with patient names."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT r.*, p.name as patient_name
        FROM reports r
        JOIN patients p ON r.patient_id = p.id
        ORDER BY r.upload_date DESC
    """)
    reports = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return reports


def get_dashboard_stats(patient_id=None):
    """Get dashboard statistics."""
    conn = get_db()
    cursor = conn.cursor()

    if patient_id:
        cursor.execute("SELECT COUNT(*) FROM reports WHERE patient_id = ?", (patient_id,))
        total_reports = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM reports WHERE patient_id = ? AND status = 'analyzed'", (patient_id,))
        analyzed = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM reports WHERE patient_id = ? AND status = 'pending'", (patient_id,))
        pending = cursor.fetchone()[0]
    else:
        cursor.execute("SELECT COUNT(*) FROM reports")
        total_reports = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'analyzed'")
        analyzed = cursor.fetchone()[0]
        cursor.execute("SELECT COUNT(*) FROM reports WHERE status = 'pending'")
        pending = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM patients")
    total_patients = cursor.fetchone()[0]

    conn.close()
    return {
        "total_reports": total_reports,
        "analyzed_reports": analyzed,
        "pending_reports": pending,
        "total_patients": total_patients
    }
