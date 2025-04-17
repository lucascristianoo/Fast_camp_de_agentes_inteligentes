import smtplib
from email.mime.text import MIMEText

def send_email(to, content):
    from_email = "seu_email@gmail.com"
    password = "sua_senha_de_app"

    msg = MIMEText(content)
    msg["Subject"] = "Resultados dos Candidatos"
    msg["From"] = from_email
    msg["To"] = to

    with smtplib.SMTP_SSL("smtp.gmail.com", 465) as server:
        server.login(from_email, password)
        server.sendmail(from_email, to, msg.as_string())