from django.core.mail import send_mail
from django.conf import settings
from celery_tasks.main import celery_app


@celery_app.task(name='send_find_password_email')
def send_find_password_email(to_email, verify_url):
    subject = "打标平台找回密码验证"
    html_message = '<p>尊敬的用户您好！</p>' \
                   '<p>感谢您使用打标签平台。</p>' \
                   '<p>您的邮箱为：%s 。请点击此链接找回密码：</p>' \
                   '<p><a href="%s">%s<a></p>' % (to_email, verify_url, verify_url)
    send_mail(subject, "", settings.EMAIL_FROM, [to_email], html_message=html_message)