__version__ = '0.1.0-dev'


def accessorize(request, **kwargs):
    """Update the request.accessories dict.

    If request.accessories doesn't exist, create it.

    *request* is assumed to be a Django HTTPRequest object.
    """
    if not hasattr(request, 'accessories'):
        request.accessories = {}

    request.accessories.update(kwargs)
