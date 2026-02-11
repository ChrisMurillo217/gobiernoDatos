import sys
import os
import pandas as pd
from unittest.mock import MagicMock
import smtplib

# Add app to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.services.email_service import EmailService

def test_email_generation():
    # Mock data
    data = {
        "ItemCode": ["PT001", "PT002", "PT001", "PT003", "PT002"],
        "ItemName": ["Product 1", "Product 2", "Product 1", "Product 3", "Product 2"],
        "Nombre del campo evaluado": ["Price", "Weight", "Price", "Description", "Stock"],
        "Valor actual": [0, -1, 0, "", -5],
        "Valor sugerido": [10, 10, 10, "Desc", 0],
        "Detalle del error": ["Zero price", "Negative weight", "Zero price", "Empty", "Negative stock"],
        "Regla no cumplida": ["Price > 0", "Weight > 0", "Price > 0", "NotEmpty", "Stock >= 0"]
    }
    df = pd.DataFrame(data)
    
    # Mock SMTP to avoid sending real emails
    original_smtp = smtplib.SMTP
    smtplib.SMTP = MagicMock()
    
    service = EmailService()
    
    # We want to capture the HTML body. 
    # Since send_quality_report creates the message inside, we'll need to inspect the mock or 
    # slightly modify the service to be testable. 
    # For now, let's just run it and see if it crashes, and maybe we can inspect the mock calls.
    
    recipients = ["test@example.com"]
    service.send_quality_report(recipients, df)
    
    # Verify SMTP was called
    print("SMTP connect called:", smtplib.SMTP.called)
    
    # Capture the message sent
    smtp_instance = smtplib.SMTP.return_value.__enter__.return_value
    if smtp_instance.send_message.called:
        msg = smtp_instance.send_message.call_args[0][0]
        # Iterate over parts to find HTML
        for part in msg.walk():
            if part.get_content_type() == 'text/html':
                html_content = part.get_payload(decode=True).decode('utf-8')
                with open("tests/preview_report.html", "w", encoding="utf-8") as f:
                    f.write(html_content)
                print("HTML report saved to tests/preview_report.html")
                break
    else:
        print("send_message was NOT called!")

if __name__ == "__main__":
    test_email_generation()
