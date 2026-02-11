import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
import pandas as pd
import os
from datetime import datetime
from app.config.settings import SMTP_SERVER, SMTP_PORT, SMTP_USER, SMTP_PASSWORD

class EmailService:
    def __init__(self):
        self.server = SMTP_SERVER
        self.port = SMTP_PORT
        self.user = SMTP_USER
        self.password = SMTP_PASSWORD
    def _generate_summary_stats(self, df: pd.DataFrame) -> dict:
        """Genera estadísticas resumen del dataframe de incidencias."""
        total = len(df)
        
        # Top 5 Fields
        if 'Nombre del campo evaluado' in df.columns:
            top_fields = df['Nombre del campo evaluado'].value_counts().head(5).to_dict()
        else:
            top_fields = {}
            
        # Top 5 Items
        top_items = {}
        if 'ItemCode' in df.columns:
            # Crear copia para no modificar el original dataframe
            df_copy = df.copy()
            if 'ItemName' in df_copy.columns:
                df_copy['ItemDisplay'] = df_copy['ItemCode'].astype(str) + ' - ' + df_copy['ItemName'].astype(str).fillna('')
                top_items = df_copy['ItemDisplay'].value_counts().head(5).to_dict()
            else:
                top_items = df_copy['ItemCode'].value_counts().head(5).to_dict()
            
        return {
            "total": total,
            "top_fields": top_fields,
            "top_items": top_items
        }

    def _generate_html_body(self, stats: dict) -> str:
        """Genera el cuerpo HTML del correo con estilos CSS."""
        
        def make_table(title, data_dict):
            if not data_dict:
                return ""
            rows = ""
            for k, v in data_dict.items():
                rows += f"<tr><td>{k}</td><td style='text-align:center; font-weight:bold;'>{v}</td></tr>"
            
            return f"""
            <div class="card">
                <h3 style="margin-top:0; border-bottom:1px solid #eee; padding-bottom:5px;">{title}</h3>
                <table>
                    <tr><th>Concepto</th><th>Cantidad</th></tr>
                    {rows}
                </table>
            </div>
            """
            
        # CSS Styling
        css = """
        <style>
            body { font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif; color: #333; line-height: 1.6; background-color: #f4f4f4; margin: 0; padding: 0; }
            .container { max-width: 800px; margin: 20px auto; background-color: #ffffff; border-radius: 8px; box-shadow: 0 0 10px rgba(0,0,0,0.1); overflow: hidden; }
            .header { background-color: #0056b3; color: white; padding: 20px; text-align: center; }
            .header h1 { margin: 0; font-size: 24px; }
            .content { padding: 30px; }
            .card { background: #f9f9f9; padding: 15px; margin-bottom: 20px; border-radius: 5px; border: 1px solid #e0e0e0; }
            table { width: 100%; border-collapse: collapse; font-size: 14px; }
            th, td { padding: 10px; border-bottom: 1px solid #ddd; text-align: left; }
            th { background-color: #efefef; color: #555; }
            .kpi-container { display: flex; gap: 20px; margin-bottom: 20px; }
            .kpi-box { background: #e8f4ff; border: 1px solid #b6e0fe; padding: 15px; border-radius: 5px; flex: 1; text-align: center; }
            .kpi-value { font-size: 28px; font-weight: bold; color: #0056b3; display: block; }
            .kpi-label { font-size: 14px; color: #666; }
            .footer { background-color: #eee; padding: 15px; font-size: 12px; color: #777; text-align: center; border-top: 1px solid #ddd; }
            .alert-box { background-color: #fff3cd; border: 1px solid #ffeeba; color: #856404; padding: 15px; border-radius: 5px; margin-bottom: 20px; border-left: 5px solid #ffc107; }
            .alert-box strong { font-size: 1.1em; }
        </style>
        """
        
        fields_table = make_table("Top Campos con Errores", stats['top_fields'])
        items_table = make_table("Top Artículos Problemáticos", stats['top_items'])
        
        return f"""
        <html>
        <head>{css}</head>
        <body>
            <div class="container">
                <div class="header">
                    <h1>Reporte de Calidad de Datos</h1>
                </div>
                <div class="content">
                    <p>Estimado equipo,</p>
                    <p>Se ha completado el análisis automatizado de calidad de datos. A continuación se presenta el resumen de las incidencias detectadas que requieren atención.</p>
                    
                    <div class="alert-box">
                        <p style="margin: 0;"><strong>⚠️ Acción requerida:</strong> Se adjunta el archivo Excel con el detalle completo. Por favor revisar y corregir los datos en el sistema origen.</p>
                    </div>

                    <div class="kpi-container">
                        <div class="kpi-box">
                            <span class="kpi-value">{stats['total']}</span>
                            <span class="kpi-label">Total Incidencias</span>
                        </div>
                        <div class="kpi-box">
                            <span class="kpi-value">{datetime.now().strftime('%d/%m/%Y')}</span>
                            <span class="kpi-label">Fecha Reporte</span>
                        </div>
                    </div>
                    
                    {fields_table}
                    {items_table}
                    
                </div>
                <div class="footer">
                    <p>Este reporte fue generado automáticamente por el Sistema de Gobierno de Datos.<br>
                    Para soporte contactar al departamento de TI/Datos.</p>
                </div>
            </div>
        </body>
        </html>
        """

    def send_quality_report(self, recipients: list, failed_data: pd.DataFrame, subject_prefix: str = "[Data Governance]"):
        """
        Envía un correo con las filas que fallaron las reglas de calidad adjuntas en un Excel.
        """
        if not recipients or not recipients[0]:
            print("[Email] No hay destinatarios configurados. Omitiendo envío.")
            return
        if failed_data.empty:
            print("[Email] No hay datos erróneos para enviar.")
            return

        # Generar estadísticas y cuerpo HTML
        try:
            stats = self._generate_summary_stats(failed_data)
            body = self._generate_html_body(stats)
        except Exception as e:
            print(f"[Email Warning] Error generando estadísticas/HTML avanzado: {e}. Usando fallback.")
            body = f"<html><body><h2>Reporte de Incidencias</h2><p>Se encontraron {len(failed_data)} errores.</p></body></html>"

        subject = f"{subject_prefix} Reporte de Calidad - {datetime.today().strftime('%d-%m-%Y')}"
        
        # Crear archivo temporal
        temp_filename = f"incidencias_{datetime.now().strftime('%d%m%Y_%H%M%S')}.xlsx"
        failed_data.to_excel(temp_filename, index=False)
        
        try:
            msg = MIMEMultipart()
            msg['From'] = self.user
            msg['To'] = ", ".join(recipients)
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'html'))
            # Adjuntar archivo
            with open(temp_filename, "rb") as attachment:
                part = MIMEBase("application", "octet-stream")
                part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header(
                "Content-Disposition",
                f"attachment; filename= {temp_filename}",
            )
            msg.attach(part)
            # Enviar correo
            print(f"--- Iniciando envío de correo a: {recipients} ---")
            with smtplib.SMTP(self.server, self.port) as server:
                server.starttls()
                server.login(self.user, self.password)
                server.send_message(msg)
            print("[Exito] Correo de incidencias enviado correctamente.")
        except Exception as e:
            print(f"[Error] Falló el envío de correo: {e}")
        finally:
            # Limpiar archivo temporal
            if os.path.exists(temp_filename):
                try:
                    os.remove(temp_filename)
                except:
                    pass
