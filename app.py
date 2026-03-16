"""Flask application - Domain Adaptive Enterprise LLM Assistant."""
import os
import json
import uuid
from datetime import datetime
from flask import (
    Flask, request, jsonify, render_template, session,
    redirect, url_for, send_file, flash
)
from flask_cors import CORS
from werkzeug.utils import secure_filename

from config import *
from database import (
    create_tables, seed_demo_data, authenticate_patient,
    get_patient_by_id, get_all_patients, add_report, update_report,
    get_reports_for_patient, get_report_by_id, get_all_reports,
    get_dashboard_stats
)
from pdf_extractor import process_uploaded_pdf
from embedding_engine import get_or_create_collection
from rag_engine import build_rag_context, embed_report
from llm_engine import generate_explanation, chat_followup
from tools import generate_chart_data, generate_diet_plan, generate_insights
from memory import save_message, get_conversation_history, get_patient_context_summary
from pdf_generator import generate_patient_report_pdf

app = Flask(__name__)
app.secret_key = SECRET_KEY
CORS(app)

# Ensure directories exist
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(CHROMA_DB_PATH, exist_ok=True)
os.makedirs("sample_reports", exist_ok=True)

# Initialize database
create_tables()
seed_demo_data()


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def login_required(f):
    """Decorator to require login for routes."""
    from functools import wraps
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'patient_id' not in session and 'admin' not in session:
            if request.is_json:
                return jsonify({"error": "Not authenticated"}), 401
            return redirect(url_for('login_page'))
        return f(*args, **kwargs)
    return decorated_function


# ==================== PAGE ROUTES ====================

@app.route('/')
def index():
    if 'patient_id' in session or 'admin' in session:
        return redirect(url_for('dashboard_page'))
    return redirect(url_for('login_page'))


@app.route('/login')
def login_page():
    return render_template('login.html')


@app.route('/dashboard')
@login_required
def dashboard_page():
    return render_template('dashboard.html')


@app.route('/reports')
@login_required
def reports_page():
    return render_template('dashboard.html', page='reports')


@app.route('/report/<int:report_id>')
@login_required
def report_detail_page(report_id):
    return render_template('report.html', report_id=report_id)


@app.route('/chat')
@login_required
def chat_page():
    report_id = request.args.get('report_id')
    return render_template('chat.html', report_id=report_id)


@app.route('/admin')
def admin_page():
    session['admin'] = True
    return render_template('admin.html')


# ==================== API ROUTES ====================

@app.route('/api/login', methods=['POST'])
def api_login():
    data = request.get_json()
    email = data.get('email', '')
    password = data.get('password', '')

    patient = authenticate_patient(email, password)
    if patient:
        session['patient_id'] = patient['id']
        session['patient_name'] = patient['name']
        return jsonify({
            "success": True,
            "patient": {
                "id": patient['id'],
                "name": patient['name'],
                "email": patient['email']
            }
        })
    return jsonify({"success": False, "error": "Invalid credentials"}), 401


@app.route('/api/logout')
def api_logout():
    session.clear()
    return redirect(url_for('login_page'))


@app.route('/api/me')
@login_required
def api_me():
    patient_id = session.get('patient_id')
    if patient_id:
        patient = get_patient_by_id(patient_id)
        if patient:
            patient.pop('password_hash', None)
            return jsonify({"success": True, "patient": patient})
    return jsonify({"success": True, "admin": True, "name": "Admin"})


@app.route('/api/dashboard')
@login_required
def api_dashboard():
    patient_id = session.get('patient_id')
    stats = get_dashboard_stats(patient_id)
    context = get_patient_context_summary(patient_id) if patient_id else {}
    return jsonify({
        "success": True,
        "stats": stats,
        "context": context
    })


@app.route('/api/reports')
@login_required
def api_reports():
    patient_id = session.get('patient_id')
    if patient_id:
        reports = get_reports_for_patient(patient_id)
    else:
        reports = get_all_reports()
    return jsonify({"success": True, "reports": reports})


@app.route('/api/report/<int:report_id>')
@login_required
def api_report_detail(report_id):
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404

    # Parse JSON fields
    for field in ['parsed_data', 'chart_data', 'diet_plan', 'insights']:
        if report.get(field) and isinstance(report[field], str):
            try:
                report[field] = json.loads(report[field])
            except:
                pass

    patient = get_patient_by_id(report['patient_id'])
    if patient:
        patient.pop('password_hash', None)

    return jsonify({
        "success": True,
        "report": report,
        "patient": patient
    })


@app.route('/api/upload', methods=['POST'])
def api_upload():
    if 'file' not in request.files:
        return jsonify({"error": "No file uploaded"}), 400

    file = request.files['file']
    patient_id = request.form.get('patient_id')
    report_type = request.form.get('report_type', 'Blood Test')

    if not patient_id:
        return jsonify({"error": "Patient ID is required"}), 400

    if file.filename == '':
        return jsonify({"error": "No file selected"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "Only PDF files are allowed"}), 400

    # Save file
    original_filename = secure_filename(file.filename)
    unique_filename = f"{uuid.uuid4().hex}_{original_filename}"
    filepath = os.path.join(UPLOAD_FOLDER, unique_filename)
    file.save(filepath)

    # Add report to database
    report_id = add_report(int(patient_id), unique_filename, original_filename, report_type)

    # Parse PDF
    parsed_data = process_uploaded_pdf(filepath)
    update_report(report_id, parsed_data=parsed_data)

    # Embed into vector DB
    try:
        chunks_embedded = embed_report(report_id, patient_id, parsed_data)
    except Exception as e:
        print(f"Embedding error (non-fatal): {e}")
        chunks_embedded = 0

    return jsonify({
        "success": True,
        "report_id": report_id,
        "filename": original_filename,
        "tests_found": len(parsed_data.get("test_results", [])),
        "chunks_embedded": chunks_embedded
    })


@app.route('/api/analyze/<int:report_id>', methods=['POST'])
@login_required
def api_analyze(report_id):
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404

    # Parse stored data
    parsed_data = report.get('parsed_data', '{}')
    if isinstance(parsed_data, str):
        try:
            parsed_data = json.loads(parsed_data)
        except:
            parsed_data = {}

    test_results = parsed_data.get("test_results", [])

    # Build RAG context (gracefully handle embedding failures)
    patient_id = report['patient_id']
    try:
        rag_context = build_rag_context(parsed_data, patient_id=patient_id)
    except Exception as e:
        print(f"RAG context error (non-fatal): {e}")
        rag_context = ""

    # Generate AI explanation
    ai_explanation = generate_explanation(parsed_data, rag_context)

    # Generate tools output
    chart_data = generate_chart_data(test_results)
    diet_plan = generate_diet_plan(test_results)
    insights = generate_insights(test_results)

    # Save to database
    update_report(
        report_id,
        ai_explanation=ai_explanation,
        chart_data=chart_data,
        diet_plan=diet_plan,
        insights=insights,
        status='analyzed'
    )

    # Save to memory
    save_message(patient_id, report_id, "system",
                 f"Report analyzed: {report.get('original_filename', 'Unknown')}")
    save_message(patient_id, report_id, "assistant", ai_explanation)

    return jsonify({
        "success": True,
        "ai_explanation": ai_explanation,
        "chart_data": chart_data,
        "diet_plan": diet_plan,
        "insights": insights
    })


@app.route('/api/chat', methods=['POST'])
@login_required
def api_chat():
    data = request.get_json()
    message = data.get('message', '')
    report_id = data.get('report_id')
    patient_id = session.get('patient_id')

    if not message:
        return jsonify({"error": "Message is required"}), 400

    # Get conversation history
    try:
        history = get_conversation_history(patient_id, report_id)
    except Exception as e:
        print(f"History load error: {e}")
        history = []

    # Get report context if available (gracefully handle RAG/embedding failures)
    report_context = ""
    if report_id:
        report = get_report_by_id(report_id)
        if report:
            parsed_data = report.get('parsed_data', '{}')
            if isinstance(parsed_data, str):
                try:
                    parsed_data = json.loads(parsed_data)
                except:
                    parsed_data = {}
            # Try RAG context, fall back to plain report data
            try:
                report_context = build_rag_context(parsed_data, patient_id=patient_id, query=message)
            except Exception as e:
                print(f"RAG context error in chat (non-fatal): {e}")
                # Build simple fallback context from parsed data
                if parsed_data.get("test_results"):
                    lines = ["Patient Lab Results:"]
                    for t in parsed_data["test_results"]:
                        lines.append(f"- {t['name']}: {t['value']} {t['unit']} [{t['status']}]")
                    report_context = "\n".join(lines)

            # Also include AI explanation if available
            if report.get('ai_explanation') and not report_context:
                report_context = report['ai_explanation'][:2000]

    # Generate response
    try:
        response = chat_followup(message, history, report_context)
    except Exception as e:
        print(f"Chat generation error: {e}")
        response = "I'm sorry, I encountered an error processing your question. Please make sure Ollama is running with the llama3.1:8b model and try again."

    # Save to memory
    try:
        save_message(patient_id, report_id, "user", message)
        save_message(patient_id, report_id, "assistant", response)
    except Exception as e:
        print(f"Memory save error: {e}")

    return jsonify({
        "success": True,
        "response": response
    })


@app.route('/api/chat/history')
@login_required
def api_chat_history():
    patient_id = session.get('patient_id')
    report_id = request.args.get('report_id')
    history = get_conversation_history(patient_id, report_id)
    return jsonify({"success": True, "history": history})


@app.route('/api/download/<int:report_id>')
@login_required
def api_download(report_id):
    report = get_report_by_id(report_id)
    if not report:
        return jsonify({"error": "Report not found"}), 404

    patient = get_patient_by_id(report['patient_id'])
    patient_info = patient if patient else {}
    patient_info.pop('password_hash', None)

    # Parse all data
    parsed_data = report.get('parsed_data', '{}')
    if isinstance(parsed_data, str):
        try:
            parsed_data = json.loads(parsed_data)
        except:
            parsed_data = {}

    diet_plan = report.get('diet_plan', '{}')
    if isinstance(diet_plan, str):
        try:
            diet_plan = json.loads(diet_plan)
        except:
            diet_plan = {}

    insights = report.get('insights', '{}')
    if isinstance(insights, str):
        try:
            insights = json.loads(insights)
        except:
            insights = {}

    # Generate PDF
    pdf_buffer = generate_patient_report_pdf(
        patient_info=patient_info,
        report_data=parsed_data,
        ai_explanation=report.get('ai_explanation', ''),
        diet_plan=diet_plan,
        insights=insights
    )

    filename = f"MedExplain_Report_{report_id}_{datetime.now().strftime('%Y%m%d')}.pdf"
    return send_file(
        pdf_buffer,
        mimetype='application/pdf',
        as_attachment=True,
        download_name=filename
    )


@app.route('/api/patients')
def api_patients():
    patients = get_all_patients()
    return jsonify({"success": True, "patients": patients})


if __name__ == '__main__':
    print("\n" + "="*60)
    print("  🏥 MedExplain AI - Healthcare LLM Assistant")
    print("  Domain Adaptive Enterprise LLM with RAG")
    print("="*60)
    print(f"\n  🌐 Server: http://localhost:{PORT}")
    print(f"  🤖 LLM Model: {LLM_MODEL}")
    print(f"  📊 Embedding: {EMBEDDING_MODEL}")
    print(f"\n  Demo Login:")
    print(f"    Email: richard@demo.com")
    print(f"    Password: demo123")
    print("\n" + "="*60 + "\n")
    app.run(debug=DEBUG, port=PORT, host='0.0.0.0')
