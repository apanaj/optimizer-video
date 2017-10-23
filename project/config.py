import os


class DefaultConfig(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'SECRET_KEY')
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'pyamqp://')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost')
    URL_CACHE = False
    MAX_CONTENT_LENGTH = 80 * 1024 * 1024  # MB
    WEB_HOOKS = []


class DevelopmentConfig(DefaultConfig):
    DEBUG = True
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEDIA_FOLDER = os.path.join(BASE_DIR, 'media/')


class DeploymentConfig(DefaultConfig):
    DEBUG = False
    MEDIA_FOLDER = os.environ.get('MEDIA_FOLDER')
