from email.header import Header
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from django.core.mail import send_mail
from django.conf import settings
from celery_tasks.main import celery_app


@celery_app.task(name='send_find_password_email')
def send_find_password_email(to_email, verify_url):
    # subject = "打标平台找回密码验证"
    # html_message = '<p>尊敬的用户您好！</p>' \
    #                '<p>感谢您使用打标签平台。</p>' \
    #                '<p>您的邮箱为：%s 。请点击此链接找回密码：</p>' \
    #                '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    # send_mail(subject, "", settings.EMAIL_FROM, [to_email], html_message=html_message)

    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用打标签平台。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接找回密码：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, "点击此处重置密码")
    mail_info = {
        "from": "wzc18220844786@163.com",
        "to": to_email,
        "hostname": "smtp.163.com",
        "username": "wzc18220844786@163.com",
        "password": "123456789abc",
        "mail_subject": "打标平台邮件",
        "mail_text": html_message,
        "mail_encoding": "utf-8"
    }
    smtp = SMTP_SSL(mail_info["hostname"])
    smtp.set_debuglevel(1)
    smtp.ehlo(mail_info["hostname"])
    smtp.login(mail_info["username"], mail_info["password"])
    msg = MIMEText(mail_info["mail_text"], "html", mail_info["mail_encoding"])
    msg["Subject"] = Header(mail_info["mail_subject"], mail_info["mail_encoding"])
    msg["from"] = mail_info["from"]
    msg["to"] = mail_info["to"]
    smtp.sendmail(mail_info["from"], mail_info["to"], msg.as_string())
    smtp.quit()
