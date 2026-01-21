import pandas as pd
from app.infrastructure.excel import load_excel_data, get_profiling_rules
from app.infrastructure.database import fetch_data_in_chunks
import sys

# Función auxiliar para identificar errores (refactorizada fuera de main para claridad)
def identify_error_row(col_name, current_value, expected_value, item_code, item_name, ugp_entry=None):
    """Identifica el error específico en el valor"""
    error_details = []
    
    # Convertir a string para análisis
    current_str = str(current_value) if pd.notna(current_value) else "VACÍO"
    
    # Análisis específico por tipo de campo
    if col_name == 'ItemCode':
        if not str(current_value).startswith('PT'):
            error_details.append("❌ No empieza con 'PT'")
        if len(str(current_value)) <= 10:
            error_details.append(f"❌ Longitud insuficiente ({len(str(current_value))} caracteres, requiere >10)")
        if not str(current_value).isupper():
            error_details.append("❌ No está en mayúsculas")
        if not str(current_value).isalnum():
            error_details.append("❌ Contiene caracteres no alfanuméricos")
    
    elif col_name == 'ItemName':
        if not str(current_value).isupper():
            error_details.append("❌ No está en mayúsculas")
        if any(char in str(current_value) for char in 'ÁÉÍÓÚáéíóú'):
            error_details.append("❌ Contiene tildes")
    
    elif col_name in ['LeadTime', 'ToleranDay', 'IWeight1']:
        try:
            val = float(current_value) if pd.notna(current_value) else None
            if val is None:
                error_details.append("❌ Valor nulo o vacío")
            elif col_name == 'LeadTime' and (val < 1 or val > 20):
                error_details.append(f"❌ Fuera de rango (1-20): {val}")
            elif col_name == 'ToleranDay' and (val < 0 or val > 24):
                error_details.append(f"❌ Fuera de rango (0-24): {val}")
            elif col_name == 'IWeight1' and (val < 0 or val > 1000):
                error_details.append(f"❌ Fuera de rango (0-1000 inclusive): {val}")
        except:
            error_details.append("❌ No es un valor numérico válido")
    
    elif col_name == 'PriceUnit':
        try:
            val = float(current_value) if pd.notna(current_value) else None
            ugp = float(ugp_entry) if pd.notna(ugp_entry) else 0
            if val is None:
                error_details.append("❌ Valor nulo o vacío")
            elif ugp == 1 and val != 8:
                error_details.append(f"❌ Para UgpEntry=1 debe ser 8, actual: {val}")
            elif ugp == 3 and val != 2:
                error_details.append(f"❌ Para UgpEntry=3 debe ser 2, actual: {val}")
            elif ugp == 11 and val != 13:
                error_details.append(f"❌ Para UgpEntry=11 debe ser 13, actual: {val}")
        except:
            error_details.append("❌ Error validando PriceUnit")
    
    
    elif col_name == 'DfltWH':
        if '_PROD' not in str(current_value):
            error_details.append("❌ No contiene '_PROD'")
    
    elif col_name == 'UgpEntry':
        try:
            val = int(current_value) if pd.notna(current_value) else None
            item_name_str = str(item_name)
            item_code_str = str(item_code)
            
            # Verificar casos específicos
            if item_code_str in ['PTFUND0212', 'PTFUND0216']:
                if val != 11:
                    error_details.append(f"❌ Debe ser 11 para {item_code_str}, actual: {val}")
            elif 'LAMINA' in item_name_str or 'MANGA' in item_name_str:
                if val != 3:
                    error_details.append(f"❌ Debe ser 3 para LAMINA/MANGA, actual: {val}")
            elif any(word in item_name_str for word in ['ENVASE', 'TAPA', 'BALDE', 'PREFORMA', 'FUNDA']):
                if val != 1:
                    error_details.append(f"❌ Debe ser 1 para ENVASE/TAPA/BALDE/PREFORMA/FUNDA, actual: {val}")
        except:
            error_details.append("❌ No es un valor numérico válido")

    
    elif col_name in ['InvntItem', 'SellItem', 'PrchseItem']:
        if current_value != 'Y':
            error_details.append(f"❌ Valor incorrecto: '{current_value}' (debe ser 'Y')")
    
    elif col_name == 'ItemClass':
        if current_value != 2:
            error_details.append(f"❌ Valor incorrecto: {current_value} (debe ser 2)")
    
    elif col_name == 'PlaningSys':
        if current_value != 'M':
            error_details.append(f"❌ Valor incorrecto: '{current_value}' (debe ser 'M')")
    
    elif col_name == 'MngMethod':
        if current_value != 'A':
            error_details.append(f"❌ Valor incorrecto: '{current_value}' (debe ser 'A')")
    
    elif col_name in ['U_EMPA_ESPESOR', 'U_EMPA_ANCHO', 'U_EMPA_DESIDAD']:
        # Simplificación: Usar contains genérico en el nombre si aplica, o lógica previa
        pass # Mantener paso a genérico si no implementamos detalle aquí para brevedad, pero estaba implementado detallado
            # Reimplementando lógica detallada para estos campos
        if pd.isna(current_value) or current_value == '':
            # Nota: Esto puede ser falso positivo si el campo NO es requerido para este ItemCode.
            # Pero identify_error solo se llama si la regla FALLÓ.
            # Si la regla de negocio dice que NO es requerido, entonces NO falló, y no llegamos aquí.
            # Si llegamos aquí es porque falló la regla (que presumiblemente chequea requerimiento).
            error_details.append("❌ Campo vacío o valor inválido")
        else:
            try:
                val = float(current_value)
                if 'ESPESOR' in col_name and (val < 25 or val > 125):
                    error_details.append(f"❌ Fuera de rango (25-125): {val}")
                elif 'ANCHO' in col_name:
                    if 'PTLAMI' in str(item_code) and (val < 8.4 or val > 120):
                        error_details.append(f"❌ Fuera de rango PTLAMI (8.4-120): {val}")
                    elif 'PTMANG' in str(item_code) and (val < 5 or val > 58):
                        error_details.append(f"❌ Fuera de rango PTMANG (5-58): {val}")
            except:
                error_details.append("❌ No es un valor numérico válido")
    
    # Si no se identificó error específico, usar genérico
    if not error_details:
        if pd.isna(current_value) or current_value == '':
            error_details.append("❌ Campo vacío o nulo")
        else:
            error_details.append(f"❌ Valor '{current_str}' no cumple la regla")
    
    return " | ".join(error_details)


def process_batch(df_chunk, batch_index):
    """Procesa un lote de datos: Perfilamiento -> Calidad -> Limpieza -> Reporte"""
    from app.services.profiler import run_profile
    from app.services.quality_inspector import run_quality_check
    from app.services.business_rules import RULE_DESCRIPTIONS
    from app.services.cleaner import run_cleaning
    from app.services.value_meanings import get_value_meaning
    from app.services.field_mappings import get_field_common_name
    
    print(f"[Core] Procesando Lote #{batch_index} ({len(df_chunk)} registros)...")
    
    # 1. Perfilamiento
    quality_results_df, _, _ = run_profile(df_chunk)
    
    # 2. Calidad Avanzada
    final_quality_results = None
    if quality_results_df is not None:
        final_quality_results = run_quality_check(df_chunk, quality_results_df)

    # 3. Limpieza (Sugerencias)
    df_cleaned = run_cleaning(df_chunk)
    
    # 4. Generación de Reporte de Incidencias
    batch_report_rows = []
    
    if quality_results_df is not None:
        # Combinar resultados
        combined_results = quality_results_df.copy()
        if final_quality_results is not None:
            for col in final_quality_results.columns:
                if col not in combined_results.columns and col not in ['ItemCode', 'TimeStamp']:
                    combined_results[col] = final_quality_results[col]
        
        # Identificar fallos
        rule_cols = [c for c in combined_results.columns if c not in ['ItemCode', 'TimeStamp']]
        failed_mask = ~combined_results[rule_cols].all(axis=1) # Filas que fallan alguna regla
        
        if failed_mask.any():
            # Iterar solo sobre filas fallidas
            idxs = failed_mask.index[failed_mask] # Obtener índices originales del chunk
            
            # Subconjuntos para iterar rápido
            chunk_failures = combined_results.loc[failed_mask, rule_cols]
            chunk_raw = df_chunk.loc[failed_mask]
            chunk_clean = df_cleaned.loc[failed_mask]
            
            for idx in idxs:
                row_raw = chunk_raw.loc[idx]
                row_clean = chunk_clean.loc[idx]
                row_res = chunk_failures.loc[idx]
                
                failed_rules = row_res.index[~row_res] # Reglas False
                
                for col in failed_rules:
                    current_val = row_raw.get(col, "N/A")
                    suggested_val = row_clean.get(col, "Revisar")
                    
                    error_msg = identify_error_row(
                        col, 
                        current_val, 
                        suggested_val,
                        row_raw.get('ItemCode'),
                        row_raw.get('ItemName'),
                        row_raw.get('UgpEntry')
                    )
                    
                    batch_report_rows.append({
                        "ItemCode": row_raw.get('ItemCode'),
                        "ItemName": row_raw.get('ItemName'),
                        "Nombre del campo evaluado": get_field_common_name(col),
                        "Valor actual": get_value_meaning(col, current_val),
                        "Valor sugerido": get_value_meaning(col, suggested_val),
                        "Detalle del error": error_msg,
                        "Regla no cumplida": RULE_DESCRIPTIONS.get(col, "Regla no cumplida")
                    })
    
    return batch_report_rows


def main():
    print("--- Inicio del Proceso Optimizados (Chunking) ---")
    
    # 1. Cargar reglas (aunque no se usan explícitamente en el pipeline core, se cargan por consistencia)
    try:
        df_rules = get_profiling_rules()
        print(f"Reglas cargadas: {len(df_rules)} definiciones.")
    except Exception as e:
        print(f"[Aviso] No se pudieron cargar reglas del Excel: {e}")

    # 2. Procesamiento por Lotes (Chunking)
    HANA_VIEW_NAME = "EMPAQPLAST_PROD.SB1_VIEW_PRODUCTO_TERMINADO_GD"
    CHUNK_SIZE = 50000 
    
    all_incidences = []
    total_processed = 0
    batch_count = 0
    
    try:
        # Iterador sobre chunks
        data_iterator = fetch_data_in_chunks(HANA_VIEW_NAME, chunk_size=CHUNK_SIZE)
        
        for df_chunk in data_iterator:
            batch_count += 1
            total_processed += len(df_chunk)
            
            # Procesar chunk
            incidences = process_batch(df_chunk, batch_count)
            all_incidences.extend(incidences)
            
        print(f"\n--- Procesamiento Completado ---")
        print(f"Total registros procesados: {total_processed}")
        print(f"Total incidencias detectadas: {len(all_incidences)}")
        
        # 3. Enviar Reporte Unificado
        if all_incidences:
            from app.services.email_service import EmailService
            from app.config.settings import EMAIL_RECIPIENTS
            
            print("Generando DataFrame de reporte...")
            detailed_report_df = pd.DataFrame(all_incidences)
            
            print(f"Enviando reporte por correo a {EMAIL_RECIPIENTS}...")
            email_svc = EmailService()
            email_svc.send_quality_report(EMAIL_RECIPIENTS, detailed_report_df)
            print("[Exito] Reporte enviado.")
        else:
            print("[Info] Calidad perfecta. No se enviaron reportes.")

    except Exception as e:
        print(f"\n[Error Crítico] Falló el proceso principal: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

    # 4. Ollama (Solo disponible si se habilita y no es un proceso por lotes puro)
    # Nota: El chat con Ollama requiere un DataFrame en memoria. 
    # Si habilitamos chunking es porque no cabe en memoria.
    # Por tanto, deshabilitamos el chat interactivo en modo batch o cargamos solo una muestra.
    # Para escalabilidad real, el chat debería consultar la DB, no un DF en memoria.
    # Dejamos pendiente para futura mejora.
    pass

if __name__ == "__main__":
    main()
