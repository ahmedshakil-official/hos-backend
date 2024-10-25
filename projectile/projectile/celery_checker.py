def check(request):
    """
        :param request: HttpRequest object
        :return: dict
        """

    # Checker logic goes here
    error_key = "ERROR"
    try:
        from projectile import celery
        inspector = celery.app.control.inspect()
        status = inspector.stats()
        if not status:
            status = {error_key: 'No running Celery workers were found.'}
    except IOError as e:
        from errno import errorcode
        msg = "Error connecting to the backend: " + str(e)
        if len(e.args) > 0 and errorcode.get(e.args[0]) == 'ECONNREFUSED':
            msg += ' Check that the RabbitMQ server is running.'
        status = {error_key: msg}
    except ImportError as e:
        status = {error_key: str(e)}
    return status
