from celery import Celery
from config import DefaultConfig

celery_app = Celery('tasks',
                    backend=DefaultConfig.CELERY_RESULT_BACKEND,
                    broker=DefaultConfig.CELERY_BROKER_URL)
