from rest_framework.views import exception_handler as drf_exception_handler


def custom_exception_handler(exc, context):
    response = drf_exception_handler(exc, context)
    if response is None:
        return None

    data = response.data
    if isinstance(data, list):
        response.data = {"detail": data[0] if data else str(exc), "errors": {}}
    elif isinstance(data, dict):
        detail = data.pop("detail", None)
        if detail is None:
            detail = "Validation failed."
        response.data = {"detail": str(detail), "errors": data}
    else:
        response.data = {"detail": str(data), "errors": {}}

    return response
