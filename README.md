# Gobierno de Datos - Calidad y Perfilamiento

Este proyecto implementa un sistema de gobierno de datos enfocado en el perfilamiento, validación de reglas de calidad y limpieza de datos para productos terminados (Vista HANA: `EMPAQPLAST_PROD.SB1_VIEW_PRODUCTO_TERMINADO_GD`).

## Características

- **Perfilamiento de Datos**: Análisis estadístico básico de los datos.
- **Reglas de Calidad**: Validación de reglas de negocio específicas (ver `app/services/business_rules.py`).
- **Limpieza de Datos**: Sugerencias automáticas de corrección.
- **Reporte**: Generación de reportes de incidencias y envío por correo electrónico.
- **Chunking**: Procesamiento eficiente de grandes volúmenes de datos mediante lotes.

## Requisitos Previos

- Python 3.10+
- Cliente HANA (hdbcli)
- Acceso al servidor SMTP (para envío de correos)
- (Opcional) Ollama corriendo localmente para funcionalidades de IA

## Instalación

1.  Clonar el repositorio.
2.  Crear un entorno virtual (recomendado).
3.  Instalar las dependencias listadas en `requirements.txt`:

    ```bash
    pip install -r requirements.txt
    ```

    ó

    ```bash
    py -m pip install -r requirements.txt
    ```

    > [!IMPORTANT]
    > Es crítico instalar todas las dependencias del archivo `requirements.txt` para el correcto funcionamiento del sistema.

## Configuración

Crear un archivo `.env` en la raíz del proyecto con las siguientes variables (basado en `app/config/settings.py`):

```env
# HANA Configuration
HANA_HOST=tu_host_hana
HANA_PORT=30015
HANA_USER=tu_usuario
HANA_PASSWORD=tu_password

# SMTP Configuration (Correo)
SMTP_SERVER=smtp.office365.com
SMTP_PORT=587
SMTP_USER=tu_email@dominio.com
SMTP_PASSWORD=tu_password_email
EMAIL_RECIPIENTS=destinatario1@dominio.com,destinatario2@dominio.com

# Ollama Configuration (Opcional)
OLLAMA_ENABLE=false
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=gemma3:27b
```

## Uso

Para ejecutar el pipeline principal de procesamiento, calidad y reporte:

```bash
python main.py
```

ó

```bash
py -m main.py
```

El sistema procesará los datos en lotes y enviará un reporte por correo si se encuentran incidencias.
