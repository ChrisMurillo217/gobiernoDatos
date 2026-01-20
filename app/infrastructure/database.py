from hdbcli import dbapi
from app.config import settings as config
# rama view-test
import pandas as pd

def get_hana_connection():
    """
    Establece y retorna una conexión a la base de datos SAP HANA
    usando las credenciales de config.py.
    """
    try:
        conn = dbapi.connect(
            address=config.DB_HOST,
            port=config.DB_PORT,
            user=config.DB_USER,
            password=config.DB_PASSWORD
        )
        return conn
    except Exception as e:
        print(f"Error al conectar a HANA: {e}")
        raise

def fetch_data_from_view(view_name):
    """
    Ejecuta un SELECT * sobre la vista especificada y retorna los resultados
    como una lista de diccionarios.
    """
    conn = get_hana_connection()
    cursor = conn.cursor()
    try:
        query = f"SELECT * FROM {view_name}"
        cursor.execute(query)
        
        # Obtener nombres de columnas
        if cursor.description:
            columns = [desc[0] for desc in cursor.description]
            data = cursor.fetchall()
            # Convertir a lista de diccionarios
            result = [dict(zip(columns, row)) for row in data]
        else:
            result = []
            
        print(f"Datos obtenidos de la vista '{view_name}': {len(result)} filas.")
        return result
    except Exception as e:
        print(f"Error al consultar la vista {view_name}: {e}")
        raise
    finally:
        cursor.close()
        conn.close()

def fetch_data_in_chunks(view_name, chunk_size=50000):
    """
    Recupera datos de la vista usando pandas en chunks para eficiencia de memoria.
    Retorna un iterador de DataFrames.
    """
    conn = get_hana_connection()
    try:
        query = f"SELECT * FROM {view_name}"
        print(f"[DB] Iniciando lectura por chunks de '{view_name}' (Tam: {chunk_size})...")
        
        # read_sql retorna un generador si chunksize está definido
        chunks = pd.read_sql(query, conn, chunksize=chunk_size)
        
        for chunk in chunks:
            yield chunk
            
    except Exception as e:
        print(f"[DB Error] Fallo leyendo chunks: {e}")
        raise
    finally:
        conn.close()
        print("[DB] Conexión cerrada.")
