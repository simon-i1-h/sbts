from rest_framework.views import exception_handler
from rest_framework.exceptions import server_error


def uncaught_exception_handler(exc, context):
    response = exception_handler(exc, context)

    if response is None:
        return server_error(context['request'])
    return response
