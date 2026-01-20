import pandas as pd
import os
from datetime import datetime
from app.config.settings import DATA_PROFILING_OUTPUT
from app.services.business_rules import PROFILING_RULES

def run_profile(df: pd.DataFrame):
    """
    Ejecuta el perfilamiento completo sobre el DataFrame dado.
    Genera y guarda 3 CSVs: dataQuality, dataProfiling, dataValues.
    """
    print(f"\n--- Iniciando Perfilamiento de Datos ({len(df)} filas) ---")
    
    # 0. Preprocesamiento (Limpieza de columnas _Nombre...)
    # Simula la logica del script original de borrar columnas auxiliares de join
    cols_to_drop = [c for c in df.columns if '_Nombre' in c or '_Significado' in c]
    df_clean = df.drop(columns=cols_to_drop, errors='ignore').copy()
    
    # 1. Ejecutar Reglas (Broadcasting)
    # Creamos un DataFrame booleano donde cada columna es el resultado de una regla
    quality_results = pd.DataFrame(index=df_clean.index)
    quality_results['ItemCode'] = df_clean['ItemCode'] # Key obligatoria
    
    for rule_name, rule_func in PROFILING_RULES.items():
        if rule_name in df_clean.columns or rule_name in ["U_beas_prccode"]: # Check existencia base o logica compuesta
            # Se wrap con try-except para que una regla mala no mate todo el proceso
            try:
                # La funcion debe devolver una Serie booleana alineada con df
                result_series = rule_func(df_clean)
                quality_results[rule_name] = result_series
            except Exception as e:
                print(f"[Advertencia] Falló regla {rule_name}: {e}")
                # Asumimos False (no valido) en caso de error tecnico, o NaN
                quality_results[rule_name] = False

    # 2. Generar 'dataQuality.csv' (Detalle fila por fila)
    quality_results['TimeStamp'] = datetime.today().date()
    quality_path = os.path.join(DATA_PROFILING_OUTPUT, 'dataQuality.csv')
    quality_results.to_csv(quality_path, index=False)
    print(f"[Generado] {quality_path}")

    # 3. Generar 'dataProfiling.csv' (Estadísticas Agregadas)
    # Contamos True como Valid
    # Excluimos ItemCode y TimeStamp del conteo
    cols_rules = [c for c in quality_results.columns if c not in ['ItemCode', 'TimeStamp']]
    
    summary_data = []
    total_rows = len(df_clean)
    
    for col in cols_rules:
        valid_count = quality_results[col].sum() # Suma de Trues
        # Check original nulls for this column in source data
        # Nota: algunas reglas son compuestas, asi que mapeamos lo mejor posible
        # Si la columna existe en el DF original, contamos nulos reales
        null_count = df_clean[col].isna().sum() if col in df_clean.columns else 0
        
        summary_data.append({
            'Atributo': col,
            'Valid_values': valid_count,
            'NoValid_values': total_rows - valid_count,
            'NullValues': null_count,
            'NoNullValues': total_rows - null_count,
            'TimeStamp': datetime.today().date()
        })
        
    df_profiling = pd.DataFrame(summary_data)
    profiling_path = os.path.join(DATA_PROFILING_OUTPUT, 'dataProfiling.csv')
    df_profiling.to_csv(profiling_path, index=False)
    print(f"[Generado] {profiling_path}")

    # 4. Generar 'dataValues.csv' (Distribución de valores)
    # Itera sobre todas las columnas del DF limpio (no solo las reglas)
    values_list = []
    col_exclude = ['ItemCode', 'TimeStamp']
    
    for col in df_clean.columns:
        if col in col_exclude: 
            continue
            
        # Value counts
        v_counts = df_clean[col].value_counts(dropna=False)
        temp_df = pd.DataFrame({
            'atributo': col,
            'valor': v_counts.index,
            'conteo': v_counts.values
        })
        values_list.append(temp_df)
        
    if values_list:
        df_values = pd.concat(values_list, ignore_index=True)
        values_path = os.path.join(DATA_PROFILING_OUTPUT, 'dataValues.csv')
        df_values.to_csv(values_path, index=False)
        print(f"[Generado] {values_path}")
    
    return quality_results, df_profiling, df_values
