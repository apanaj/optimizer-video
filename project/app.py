from flask import Flask, jsonify

from exc import AppException
from extensions import celery_app
from views import mod


def create_app(config, app_name):
    app = Flask(app_name)
    app.config.from_object(config)
    app.register_blueprint(mod)
    configure_celery(app)

    @app.errorhandler(AppException)
    def exception_handler(error):
        return jsonify(error=error.message), error.status

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
