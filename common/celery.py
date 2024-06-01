from celery import shared_task


def default_celery_task(queue='default', **shared_task_kwargs):
    """
    Обычная celery задача
    """
    name_prefix = 'default'

    def decorator(func):
        shared_task_kwargs['name'] = f'{name_prefix}.{shared_task_kwargs.get("name", func.__name__.lower())}'

        @shared_task(queue=queue, **shared_task_kwargs)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def periodic_celery_task(queue='default', **shared_task_kwargs):
    """
    периодические задачи Celery
    """
    name_prefix = 'periodic'

    def decorator(func):
        shared_task_kwargs['name'] = f'{name_prefix}.{shared_task_kwargs.get("name", func.__name__.lower())}'

        @shared_task(queue=queue, **shared_task_kwargs)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator


def long_celery_task(queue='long_tasks', **shared_task_kwargs):
    """
    Декоратор для задач Celery, который ставит их в очередь 'long_tasks'.
    """
    name_prefix = 'long_task'

    def decorator(func):
        shared_task_kwargs['name'] = f'{name_prefix}.{shared_task_kwargs.get("name", func.__name__.lower())}'

        @shared_task(queue=queue, **shared_task_kwargs)
        def wrapper(*args, **kwargs):
            return func(*args, **kwargs)

        return wrapper

    return decorator
