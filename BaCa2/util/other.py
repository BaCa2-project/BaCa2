def normalize_string_to_python(string: str) -> str | bool | None:
    """
    Converts a string to None, False or True if the value matches python or javascript literals
    for those keywords. Otherwise, the string is returned unchanged.

    :param string: The string to convert
    :type string: str
    :return: The converted string
    :rtype: str | bool | None
    """
    if string == 'None' or string == 'null':
        return None
    elif string == 'False' or string == 'false':
        return False
    elif string == 'True' or string == 'true':
        return True
    else:
        return string


def add_kwargs_to_url(url: str, kwargs: dict) -> str:
    """
    Adds the given kwargs to the given url as query parameters.

    :param url: The url to add the kwargs to
    :type url: str
    :param kwargs: The kwargs to add
    :type kwargs: dict
    :return: The url with the kwargs added
    :rtype: str
    """
    if len(kwargs) == 0:
        return url
    else:
        return url + '?' + '&'.join([f'{key}={value}' for key, value in kwargs.items()])
