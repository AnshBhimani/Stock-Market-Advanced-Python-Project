import smtplib
from string import Template

email_address = "python.project.smtp@gmail.com"
password = "kbxwsbiftmwwlade"


def read_template(filename):
    with open(filename, 'r', encoding='utf-8') as template_file:
        template_file_content = template_file.read()
    return Template(template_file_content)

message_template = read_template('message.txt')

def send_email(email, name, subject, message):
    s = smtplib.SMTP('smtp.gmail.com', 587)
    s.starttls()
    s.login(email_address, password)
    s.sendmail(email_address, email, message)
    s.quit()   


send_email("vishesh.rce21@sot.pdpu.ac.in","Vishesh","Test","Hello World")
