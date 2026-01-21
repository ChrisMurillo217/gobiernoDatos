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
        subject = f"{subject_prefix} Reporte de Incidencias - {datetime.today().strftime('%d-%m-%Y')}"
        body = f"""
        <html>
        <body>
            <h2>Reporte de Incidencias de Datos</h2>
            <p>Se han detectado <b>{len(failed_data)}</b> incidencias de datos que no cumplen con las reglas de negocio establecidas.</p>
            <p>Adjunto encontrarás el archivo con el detalle de las incidencias.</p>
            <br>
            <p>Este es un mensaje automático del sistema de Gobierno de Datos.</p>
        </body>
        </html>
        """
        # Crear archivo temporal
        temp_filename = f"incidencias_{datetime.now().strftime('%d%m%Y')}.xlsx"
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
                os.remove(temp_filename)
