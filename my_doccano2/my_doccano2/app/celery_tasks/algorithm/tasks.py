import os
from email.header import Header
from email.mime.text import MIMEText
from smtplib import SMTP_SSL

from django.core.mail import send_mail
from django.conf import settings

from celery_tasks.main import celery_app


@celery_app.task(name='train_model')
def train_model(algorithm_file,config_path,model_path):
    print(config_path)
    os.system(algorithm_file+" "+config_path+" "+model_path)
    # with open("/common_static/configs")
    # nermi = trainingModel(doc_list)
    # # nermi.trainingModel(doc_list)
    # # import NamedEntityRecognitionModelInterface
    # print("训练完成")