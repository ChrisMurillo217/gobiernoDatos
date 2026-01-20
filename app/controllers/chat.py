import pandas as pd
import sys

def build_context(df_rules, df_hana):
    """
    Construye un contexto LITERAL basado en el contenido real del Excel y los datos HANA.
    Ollama solo podrá responder con lo que aquí se le proporciona.
    """
    context = "Eres un asistente de datos. Tus respuestas deben basarse EXCLUSIVAMENTE en la siguiente información:\n\n"

    # --- Reglas de negocio (Excel) ---
    if df_rules is not None and not df_rules.empty:
        # Asegurarse de que solo se incluyan las columnas necesarias
        df_clean = df_rules[['Nombre comun campo', 'reglas de perfilamiento']].copy()
        df_clean = df_clean.dropna(subset=['Nombre comun campo', 'reglas de perfilamiento'])

        context += "=== REGLAS DE NEGOCIO (contenido literal del archivo Excel) ===\n"
        context += "Formato: cada línea es \"<Nombre_comun_campo> → <Regla_de_perfilamiento>\"\n\n"

        for _, row in df_clean.iterrows():
            nombre = str(row['Nombre comun campo']).strip()
            regla = str(row['reglas de perfilamiento']).strip()
            context += f"{nombre} → {regla}\n"
        
        context += f"\nTotal de reglas: {len(df_clean)}\n\n"
    else:
        context += "=== REGLAS DE NEGOCIO ===\nNo se cargaron reglas desde el Excel.\n\n"

    # --- Datos HANA ---
    if df_hana is not None and not df_hana.empty:
        context += "=== DATOS DE HANA (MUESTRA) ===\n"
        context += "A continuación se muestra una muestra de los datos reales (máximo 50 filas) para su análisis:\n\n"
        # Con esta linea no limito el numero de filas
        # context += df_hana.to_string(index=False)
        context += df_hana.head(10).to_string(index=False)
        context += "\n\n(Obs: Se incluyen solo las primeras 50 filas para no exceder el límite de contexto. Usa estos datos para inferir patrones.)\n\n"
    else:
        context += "=== DATOS DE HANA ===\nNo se cargaron datos desde HANA.\n\n"

    # --- Instrucciones estrictas ---
    context += "=== REGLAS PARA TUS RESPUESTAS ===\n"
    context += "1. Solo usa la información arriba. No inventes columnas, reglas ni datos.\n"
    context += "2. Si te preguntan por una regla, búscala EXACTAMENTE en la lista de reglas.\n"
    context += "3. Si no existe, di: 'No se ha definido una regla para esa columna'.\n"
    context += "4. Si te preguntan por el contenido de una celda, responde con el texto literal del Excel.\n"
    context += "5. Sé directo, preciso y profesional.\n"

    return context

def start_chat(df_rules, df_hana, ollama_service):
    """
    Inicia el bucle de chat interactivo.
    """
    print("\n" + "="*50)
    print(" INICIANDO CHAT DE DATOS CON OLLAMA ")
    print("="*50)
    print("Escribe 'salir' para terminar.\n")
    
    system_prompt = build_context(df_rules, df_hana)
    messages = [{'role': 'system', 'content': system_prompt}]
    
    while True:
        try:
            user_input = input("Tú: ").strip()
            if user_input.lower() in ['salir', 'exit', 'quit']:
                print("Finalizando chat...")
                break
                
            if not user_input:
                continue
                
            # Agregar mensaje del usuario
            messages.append({'role': 'user', 'content': user_input})
            
            print("Ollama pensando...", end="\r")
            
            # Obtener respuesta
            response = ollama_service.chat(messages)
            
            if response:
                print(f"Ollama: {response}\n")
                # Agregar respuesta al historial
                messages.append({'role': 'assistant', 'content': response})
            else:
                print("Ollama: [Error] No pude generar una respuesta.\n")
                
        except KeyboardInterrupt:
            print("\nChat interrumpido.")
            break
        except Exception as e:
            print(f"\n[Error] Ocurrió un problema durante el chat: {e}")
