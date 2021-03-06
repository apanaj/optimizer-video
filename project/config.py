import os


class DefaultConfig(object):
    SECRET_KEY = os.environ.get('SECRET_KEY', 'SECRET_KEY')
    MONGO_HOST = os.environ.get('MONGO_HOST')
    MONGO_PORT = int(os.environ.get('MONGO_PORT', 27017))
    CELERY_BROKER_URL = os.environ.get('CELERY_BROKER_URL', 'pyamqp://')
    CELERY_RESULT_BACKEND = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost')
    SERVER_PROTOCOL = 'http'
    SERVER_HOST = os.environ.get('SERVER_HOST', '127.0.0.1:5000')
    ONLY_PULL_FROM_SERVER_HOST = True
    URL_CACHE = False
    MAX_CONTENT_LENGTH = 80 * 1024 * 1024  # MB
    RETRY_CALLBACK_REQUEST_COUNT = 5
    WATERMARK_PADDING = 50
    OUTPUT_VIDEO_HEIGHT = 360


class DeploymentConfig(DefaultConfig):
    DEBUG = False
    MEDIA_FOLDER = os.environ.get('MEDIA_FOLDER')
    SERVER_HOST = os.environ.get('SERVER_HOST', 'apanaj_optimizer-video')
    WEB_HOOKS = [
        # 'http://allowed-web-hook/',
        'http://api.apanajapp.com/v2/xcontent/webhook',
        'http://apanaj_web-server/xcontent/webhook'
    ]


class DevelopmentConfig(DefaultConfig):
    DEBUG = True
    BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    MEDIA_FOLDER = os.path.join(BASE_DIR, 'media/')
    WEB_HOOKS = [
        'http://127.0.0.1:5001',
        'http://127.0.0.1:5001/xcontent/webhook',
        'http://apanaj_web-server:5001/v2/xcontent/webhook',
        'http://apanaj_web-server/xcontent/webhook'
    ]
