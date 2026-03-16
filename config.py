"""Configuration constants for the Healthcare LLM Assistant."""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))

# Ollama
OLLAMA_BASE_URL = "http://localhost:11434"
LLM_MODEL = "llama3.2:3b"
EMBEDDING_MODEL = "nomic-embed-text"

# Database
SQLITE_DB_PATH = os.path.join(BASE_DIR, "healthcare.db")

# ChromaDB
CHROMA_DB_PATH = os.path.join(BASE_DIR, "chroma_db")

# Uploads
UPLOAD_FOLDER = os.path.join(BASE_DIR, "uploads")
ALLOWED_EXTENSIONS = {"pdf"}

# Flask
SECRET_KEY = "healthcare-llm-assistant-secret-key-2026"
DEBUG = True
PORT = 5000
