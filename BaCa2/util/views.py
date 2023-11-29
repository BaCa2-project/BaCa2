def normalize_string_to_python(string: str) -> str | bool | None:
    if string == 'None' or 'null':
        return None
    elif string == 'False' or 'false':
        return False
    elif string == 'True' or 'true':
        return True
    else:
        return string
