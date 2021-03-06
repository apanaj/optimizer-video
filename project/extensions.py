from celery import Celery
from flask_pymongo import MongoClient
import gridfs

from config import DefaultConfig

db = MongoClient(
    host=DefaultConfig.MONGO_HOST,
    port=DefaultConfig.MONGO_PORT
).video_optimizer
fs = gridfs.GridFS(db)

celery_app = Celery('tasks',
                    backend=DefaultConfig.CELERY_RESULT_BACKEND,
                    broker=DefaultConfig.CELERY_BROKER_URL)
