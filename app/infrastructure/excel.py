import pandas as pd
from app.config.settings import EXCEL_FILE_PATH, EXCEL_SHEET_NAME
import os

def load_excel_data():
    """
    Carga los datos del archivo Excel especificado en config.py.
    Retorna un DataFrame de pandas.
    """
    if not os.path.exists(EXCEL_FILE_PATH):
        raise FileNotFoundError(f"El archivo Excel no se encuentra en: {EXCEL_FILE_PATH}")
    
    print(f"Cargando datos desde: {EXCEL_FILE_PATH}")
    df = pd.read_excel(EXCEL_FILE_PATH, sheet_name=EXCEL_SHEET_NAME)
    print(f"Datos cargados exitosamente: {len(df)} filas.")
    return df

def get_profiling_rules():
    """
    Carga y retorna un DataFrame con las reglas de perfilamiento.
    Filtra solo las columnas necesarias.
    """
    df = load_excel_data()
    df['Nombre comun campo'] = df['Nombre comun campo'].astype(str).str.strip()
    df['reglas de perfilamiento'] = df['reglas de perfilamiento'].astype(str).str.strip()
    # Ajusta los nombres de columnas según lo visto en la inspección
    # Se requiere: 'Nombre comun campo' (identificador) y 'reglas de perfilamiento' (regla)
    required_cols = ['Nombre comun campo', 'reglas de perfilamiento']
    
    # Verificar que las columnas existan
    missing = [c for c in required_cols if c not in df.columns]
    if missing:
        print(f"Advertencia: Faltan columnas en el Excel para reglas: {missing}")
        return pd.DataFrame() # Retorna vacio si no hay estructura correcta
        
    return df[required_cols].dropna(subset=['reglas de perfilamiento'])
