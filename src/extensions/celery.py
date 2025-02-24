from flask import Flask
from celery import Celery, Task


# celery = Celery(
#     __name__,
#     broker="redis://redis:6379/0",
#     backend="redis://redis:6379/0"
# )


def init_celery(app: Flask) -> Celery:
    """
    Configures Celery to use Flask's app context.
    
    :param app: The Flask application instance.
    :return: Configured Celery instance.
    """
    class FlaskTask(Task):
        def __call__(self, *args: object, **kwargs: object) -> object:
            with app.app_context():
                return self.run(*args, **kwargs)
    celery = Celery(
        app.name,
        broker="redis://redis:6379/0",
        backend="redis://redis:6379/0",
        task_cls=FlaskTask
    )            
    # celery = Celery(app.name, task_cls=FlaskTask)
    celery.conf.update(app.config)
    celery.set_default()
    app.extensions["celery"] = celery
    return celery
