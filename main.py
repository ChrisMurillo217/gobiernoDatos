import pandas as pd
from excel_loader import load_excel_data, get_profiling_rules
from db_connector import fetch_data_from_view
import sys

def main():
    print("--- Inicio del Proceso ---")
    
    # 1. Cargar reglas de perfilamiento
    try:
        print("\n--- Cargando Reglas de Negocio ---")
        df_rules = get_profiling_rules()
        print(f"Reglas cargadas: {len(df_rules)} definiciones.")
    except Exception as e:
        print(f"\n[Error] Falló la carga de reglas del Excel: {e}")
        sys.exit(1)

    # 2. Conectar a HANA y cargar dato
    # IMPORTANTE: Reemplaza 'TU_ESQUEMA.TU_VISTA' con el nombre real de la vista en HANA
    HANA_VIEW_NAME = "EMPAQPLAST_PROD.SB1_VIEW_PRODUCTO_TERMINADO_GD" 
    
    print(f"\n--- Conectando a HANA para leer vista: {HANA_VIEW_NAME} ---")
    
    try:
        data_hana = fetch_data_from_view(HANA_VIEW_NAME)
        df_hana = pd.DataFrame(data_hana)
        print(f"[HANA] Datos cargados: {len(df_hana)} filas.")
        print(df_hana.head())
        
        print("\n[Exito] Conexión y carga de datos completada correctamente.")
        
    except Exception as e:
        print(f"\n[Error] Falló la conexión o consulta a HANA: {e}")
        print("Verifica que el servidor esté accesible y las credenciales en .env sean correctas.")

    # 3. Verificar integración con Ollama
    from ollama_service import OllamaService
    print("\n--- Verificando servicio Ollama ---")
    ollama_svc = OllamaService()
    if ollama_svc.check_connection():
        print("[Exito] Conexión con Ollama establecida.")
    else:
        print("[Aviso] No se pudo conectar con Ollama. Asegúrate de que estė corriendo.")

    # 4. Chat interactivo
    if 'ollama_svc' in locals() and ollama_svc.check_connection():
        print("\n¿Deseas chatear con tus datos usando Ollama?")
        answer = input("(s/n): ").lower().strip()
        if answer.startswith('s'):
            from chat_controller import start_chat
            # Pasamos los dataframes cargados (pueden ser None si falló la carga, manejar eso)
            # Como main define variables locales dentro de bloques try, asegurémonos de tener acceso
            # Para este script simple, asumiremos que si llegamos aquí y df_rules/df_hana existen, los pasamos.
            
            # Recuperar variables del scope local si existen, sino None
            rules = locals().get('df_rules', None)
            hana_data = locals().get('df_hana', None)
            
            if rules is None and hana_data is None:
                print("[Advertencia] No hay datos cargados para chatear.")
            else:
                start_chat(rules, hana_data, ollama_svc)

    print("\n--- Fin del Proceso de Verificación ---")

if __name__ == "__main__":
    main()
