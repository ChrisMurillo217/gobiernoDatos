import os
from dotenv import load_dotenv

load_dotenv()

# HANA Configuration
DB_HOST = os.getenv("HANA_HOST")
DB_PORT = int(os.getenv("HANA_PORT", 30015))
DB_USER = os.getenv("HANA_USER")
DB_PASSWORD = os.getenv("HANA_PASSWORD")

# Excel Configuration
EXCEL_FILE_PATH = os.path.join("inputs", "Diccionario Articulos.xlsx")
EXCEL_SHEET_NAME = "Diccionario Gobierno Datos"

# Ollama Configuration
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "gemma3:27b")
OLLAMA_ENABLE = os.getenv("OLLAMA_ENABLE", "false").lower() == "true"

# SMTP Configuration (Email)
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.office365.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", 587))
SMTP_USER = os.getenv("SMTP_USER", "")
SMTP_PASSWORD = os.getenv("SMTP_PASSWORD", "")
EMAIL_RECIPIENTS = os.getenv("EMAIL_RECIPIENTS", "").split(",")

# Profiling Configuration
DATA_PROFILING_OUTPUT = os.path.join("outputs", "perfilado")
if not os.path.exists(DATA_PROFILING_OUTPUT):
    os.makedirs(DATA_PROFILING_OUTPUT, exist_ok=True)

# Quality Configuration
DATA_QUALITY_OUTPUT = os.path.join("outputs", "calidad")
if not os.path.exists(DATA_QUALITY_OUTPUT):
    os.makedirs(DATA_QUALITY_OUTPUT, exist_ok=True)

# Cleaning Configuration
DATA_CLEANING_OUTPUT = os.path.join("outputs", "limpieza")
if not os.path.exists(DATA_CLEANING_OUTPUT):
    os.makedirs(DATA_CLEANING_OUTPUT, exist_ok=True)