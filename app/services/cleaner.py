import pandas as pd
import os
from app.config.settings import DATA_CLEANING_OUTPUT
from app.services.business_rules import CLEANING_RULES

def run_cleaning(df_raw: pd.DataFrame):
    """
    Ejecuta el pipeline de limpieza y transformación de datos.
    Aplica secuencialmente todas las reglas definidas en CLEANING_RULES.
    """
    print(f"\n--- Iniciando Proceso de Limpieza (DataCleaner) ---")
    
    # Trabajar sobre una copia para no mutar el original en memoria si se usa luego
    df_clean = df_raw.copy()
    
    # Aplicar transformaciones
    for step_func in CLEANING_RULES:
        try:
            # Cada funcion recibe df y retorna df transformado
            df_clean = step_func(df_clean)
        except Exception as e:
            print(f"[Error Limpieza] Falló en {step_func.__name__}: {e}")
            
    # Guardar resultado
    output_path = os.path.join(DATA_CLEANING_OUTPUT, 'cleaned_data.csv')
    df_clean.to_csv(output_path, index=False)
    print(f"[Generado] {output_path}")
    
    return df_clean
