import pandas as pd
import os
from datetime import datetime
from app.config.settings import DATA_QUALITY_OUTPUT
from app.services.business_rules import QUALITY_RULES, PROFILING_DEPENDENCY_MAP

def run_quality_check(df_raw: pd.DataFrame, df_profiling_results: pd.DataFrame):
    """
    Ejecuta el chequeo de calidad avanzado.
    Combina reglas simples (heredadas del perfilamiento) y reglas complejas (definidas en quality_rules).
    """
    print(f"\n--- Iniciando Chequeo de Calidad ---")
    
    # 0. Preprocesamiento (igual que en script usuario)
    # Limpieza de columnas _Nombre...
    # Regla: Borrar columnas con _Nombre o _Significado, PERO asegurar que TaxCodeAR se quede
    # y TaxCodeAR_NombreImpuesto se borre.
    cols_to_drop = [c for c in df_raw.columns if '_Nombre' in c or '_Significado' in c]

    df_clean = df_raw.drop(columns=cols_to_drop, errors='ignore').copy()
    
    # 1. Resultados de Calidad
    quality_results = pd.DataFrame(index=df_clean.index)
    quality_results['ItemCode'] = df_clean['ItemCode']
    
    # A. Reglas Complejas (Calculadas aqui)
    for rule_name, rule_func in QUALITY_RULES.items():
        if rule_name in df_clean.columns or rule_name == "U_Codigo_Secundario": # Check column existence
            try:
                # Retorna Serie Booleana (True=Valid)
                quality_results[rule_name] = rule_func(df_clean)
            except Exception as e:
                print(f"[Advertencia Calidad] Falló regla {rule_name}: {e}")
                quality_results[rule_name] = False

    # B. Reglas Heredadas de Profiling (Dependencias)
    # Si pasó el profiling -> Es valido en calidad (Logica user: takeValid/takeNovalid es filtro)
    # Basicamente el usuario dice: "Si falló en profiling, falla en calidad".
    # OJO: User code a veces usa "takeNovalid" para reglas. 
    # Example: ugpEntry -> calls takeNovalid.
    # takeNovalid returns index where ValidData is FALSE.
    # quality variable collects "x not in j()". j() returns INVALID indexes.
    # So if x IS in InvalidIndexes -> It is Invalid.
    # So: QualityResult = ProfilingResult.
    
    for rule_name, profil_col in PROFILING_DEPENDENCY_MAP.items():
        if profil_col in df_profiling_results.columns:
            # Heredamos directamente el resultado booleano
            # Si era True en profiling, es True aqui.
            quality_results[rule_name] = df_profiling_results[profil_col]
        else:
            # Si no existe en profiling, asumimos False o warning
            # print(f"Warning: {rule_name} missing in profiling results")
            pass

    # 2. Generar 'validValues.csv' (Conteo estadistico)
    # Estructura: Atributo, Valid_values, NoValid_values
    stats_rows = []
    cols_check = [c for c in quality_results.columns if c != 'ItemCode']
    
    for col in cols_check:
        valid_count = quality_results[col].sum()
        invalid_count = len(quality_results) - valid_count
        
        stats_rows.append({
            'Atributo': col,
            'Valid_values': valid_count,
            'NoValid_values': invalid_count,
            'TimeStamp': datetime.today().date()
        })
        
    df_valid_values = pd.DataFrame(stats_rows)
    valid_path = os.path.join(DATA_QUALITY_OUTPUT, 'validValues.csv')
    df_valid_values.to_csv(valid_path, index=False)
    print(f"[Generado] {valid_path}")
    
    # 3. Generar 'dataQuality.csv' (Detalle - Sobrescribe o version nueva?)
    # El usuario lo llama 'informe' y lo guarda como 'dataQuality.csv'. 
    # (El profiling generaba el mismo nombre, cuidado con sobrescritura si Output path es igual)
    # Pero aqui es el reporte "final" de calidad.
    quality_results['TimeStamp'] = datetime.today().date()
    # Usaremos prefijo para distinguir si estan en la misma carpeta
    report_path = os.path.join(DATA_QUALITY_OUTPUT, 'finalDataQuality.csv') 
    quality_results.to_csv(report_path, index=False)
    print(f"[Generado] {report_path}")
    
    return quality_results
