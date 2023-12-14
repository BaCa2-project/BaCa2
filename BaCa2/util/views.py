def normalize_string_to_python(string: str) -> str | bool | None:
    if string == 'None' or string == 'null':
        return None
    elif string == 'False' or string == 'false':
        return False
    elif string == 'True' or string == 'true':
        return True
    else:
        return string
