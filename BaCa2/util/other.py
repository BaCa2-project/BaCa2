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
