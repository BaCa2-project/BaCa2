def normalize_string_to_python(string: str) -> str | bool | int | None | list:
    """
    Converts a string to None, False or True if the value matches python or javascript literals
    for those keywords. If the string is a number, it is converted to an int. If the string starts
    and ends with square brackets, it is converted to a list by splitting it at the commas and
    normalizing the values.

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
    elif string.isdigit():
        return int(string)
    elif string.startswith('[') and string.endswith(']'):
        return decode_list(string)
    else:
        return string


def add_kwargs_to_url(url: str, kwargs: dict) -> str:
    """
    Adds the given kwargs to the given url as query_result parameters.

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
        kwargs = '&'.join([f'{key}={value}' for key, value in kwargs.items()])
        if '?' in url:
            return url + '&' + kwargs
        return url + '?' + kwargs


def replace_special_symbols(string: str, replacement: str = '_') -> str:
    """
    Replaces all special symbols in a string with a given replacement.

    :param string: String to replace special symbols in.
    :type string: str
    :param replacement: Replacement for special symbols.
    :type replacement: str

    :return: String with special symbols replaced.
    :rtype: str
    """
    for i in range(len(string)):
        if not string[i].isalnum():
            string = string[:i] + f'{replacement}' + string[i + 1:]
    return string


def encode_dict_to_url(name: str, dictionary: dict) -> str:
    """
    Encodes a dictionary to a string that can be used in a url. Supports dictionaries containing
    strings, integers, booleans, None and non-nested lists of those types.

    :param name: The name of the dictionary, the encoded dict can be retrieved from url
    query parameters using this name.
    :type name: str
    :param dictionary: The dictionary to encode.
    :type dictionary: dict
    :return: The encoded dictionary.
    :rtype: str

    See also:
        - :func:`decode_url_to_dict`
        - :func:`encode_value`
    """
    items = '|'.join([f'{key}={encode_value(value)}' for key, value in dictionary.items()])
    return f'{name}={items}'


def encode_value(value: str | int | bool | None | list) -> str:
    """
    Encodes a value to a string that can be used in a url. If the value is a list, it is encoded as
    a string in the format '[item1,item2,...]'. Does not support nested lists.

    :param value: The value to encode.
    :type value: str | int | bool | None | list
    :return: The encoded value.
    :rtype: str
    """
    if not isinstance(value, list):
        return f'{value}'

    return f'[{",".join([encode_value(item) for item in value])}]'


def decode_list(string: str) -> list:
    """
    :param string: list encoded as string using :func:`encode_value`.
    :type string: str
    :return: The decoded list of integers, booleans, strings or None.
    :rtype: list
    """
    return [normalize_string_to_python(item) for item in string[1:-1].split(',')]


def decode_url_to_dict(encoded_dict: str) -> dict:
    """
    Decodes a string encoded using :func:`encode_dict_to_url` to a dictionary normalizing values
    to python.

    :param encoded_dict: The encoded dictionary.
    :type encoded_dict: str
    :return: The decoded dictionary.
    :rtype: dict

    See also:
        - :func:`encode_dict_to_url`
    """
    items = encoded_dict.split('|')
    return {item.split('=')[0]: normalize_string_to_python(item.split('=')[1]) for item in items}
