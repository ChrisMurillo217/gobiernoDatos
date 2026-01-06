from hdbcli import dbapi
import config

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
