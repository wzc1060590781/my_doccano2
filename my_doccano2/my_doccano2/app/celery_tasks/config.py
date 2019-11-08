RABBIT_MQ = {
    'HOST': '127.0.0.1',
    'PORT': 5672,
    'USER': 'guest',
    'PASSWORD': 'guest'
}

CELERY_IMPORTS = ("celery_tasks.email.tasks", )

BROKER_URL = 'amqp://%s:%s@%s:%s/myvhost' % (RABBIT_MQ['USER'], RABBIT_MQ['PASSWORD'], RABBIT_MQ['HOST'], RABBIT_MQ['PORT'])

CELERYD_LOG_FORMAT = '[%(asctime)s] [%(levelname)s] %(message)s'

CELERY_ROUTES = {
        'email.tasks.add': {'queue': 'sunday'},
}