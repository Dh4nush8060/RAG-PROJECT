"""Secure memory module for storing patient context and conversation history."""
import json
from datetime import datetime
from database import get_db


def save_message(patient_id, report_id, role, content):
    """Save a chat message to memory."""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO memory (patient_id, report_id, role, content)
        VALUES (?, ?, ?, ?)
    """, (patient_id, report_id, role, content))
    conn.commit()
    conn.close()


def get_conversation_history(patient_id, report_id=None, limit=20):
    """Get conversation history for a patient."""
    conn = get_db()
    cursor = conn.cursor()

    if report_id:
        cursor.execute("""
            SELECT role, content, created_at FROM memory
            WHERE patient_id = ? AND report_id = ?
            ORDER BY created_at ASC
            LIMIT ?
        """, (patient_id, report_id, limit))
    else:
        cursor.execute("""
            SELECT role, content, created_at FROM memory
            WHERE patient_id = ?
            ORDER BY created_at DESC
            LIMIT ?
        """, (patient_id, limit))

    messages = [{"role": row[0], "content": row[1], "timestamp": row[2]} for row in cursor.fetchall()]
    conn.close()

    if not report_id:
        messages.reverse()

    return messages


def clear_memory(patient_id, report_id=None):
    """Clear conversation memory."""
    conn = get_db()
    cursor = conn.cursor()
    if report_id:
        cursor.execute("DELETE FROM memory WHERE patient_id = ? AND report_id = ?", (patient_id, report_id))
    else:
        cursor.execute("DELETE FROM memory WHERE patient_id = ?", (patient_id,))
    conn.commit()
    conn.close()


def get_patient_context_summary(patient_id):
    """Get a summary of patient's interaction context."""
    conn = get_db()
    cursor = conn.cursor()

    # Count interactions
    cursor.execute("SELECT COUNT(*) FROM memory WHERE patient_id = ?", (patient_id,))
    total_messages = cursor.fetchone()[0]

    # Get report count
    cursor.execute("SELECT COUNT(*) FROM reports WHERE patient_id = ?", (patient_id,))
    total_reports = cursor.fetchone()[0]

    # Get last interaction
    cursor.execute("""
        SELECT created_at FROM memory WHERE patient_id = ? ORDER BY created_at DESC LIMIT 1
    """, (patient_id,))
    last_interaction = cursor.fetchone()
    last_interaction = last_interaction[0] if last_interaction else None

    conn.close()
    return {
        "total_messages": total_messages,
        "total_reports": total_reports,
        "last_interaction": last_interaction
    }
