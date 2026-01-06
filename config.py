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