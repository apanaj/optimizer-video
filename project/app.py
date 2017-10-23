from flask import Flask, jsonify

from exception import LargeFileException, FileSizeException
from extensions import celery_app
from views import mod


def create_app(config, app_name):
    app = Flask(app_name)
    app.config.from_object(config)
    app.register_blueprint(mod)
    configure_celery(app)

    @app.errorhandler(FileSizeException)
    def file_size_exception(error):
        return jsonify(error='File not found or file length is zero'), 400

    @app.errorhandler(LargeFileException)
    def large_file_exception(error):
        return jsonify(error='File is too large'), 413

    return app


def configure_celery(app):
    celery_app.conf.update(app.config)
    TaskBase = celery_app.Task

    class ContextTask(TaskBase):
        abstract = True

        def __call__(self, *args, **kwargs):
            with app.app_context():
                return TaskBase.__call__(self, *args, **kwargs)

    celery_app.Task = ContextTask
    return celery_app