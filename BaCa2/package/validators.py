from pathlib import Path
from re import findall, split
from BaCa2.settings import BASE_DIR


def isAny(val):
    """
    any non-empty value is allowed

    :return: A boolean value.
    """
    return bool(val)


def isNone(val):
    """
    check if val is None

    :return: A boolean value.
    """
    return val is None


def isInt(val):
    """
    check if val can be converted to int

    :return: A boolean value.
    """
    if type(val) == float:
        return False
    try:
        int(val)
        return True
    except ValueError:
        return False


def isIntBetween(val, a: int, b: int):
    """
    check if val is an int value between a and b

    :return: A boolean value.
    """
    if isInt(val):
        if a <= val < b:
            return True
    return False


def isFloat(val):
    """
    check if val can be converted to float

    :return: A boolean value.
    """
    try:
        float(val)
        return True
    except ValueError:
        return False


def isFloatBetween(val, a: int, b: int):
    """
    check if val is a float value between a and b

    :return: A boolean value.
    """
    if isFloat(val):
        if a <= val < b:
            return True
    return False


def isStr(val):
    """
    check if val can be converted to string

    :return: A boolean value.
    """
    if type(val) == str:
        return True
    return False


def is_(val, schema: str):
    """
    check if val is exactly like schema

    :return: A boolean value.
    """
    if isStr(val):
        return val == schema
    return False


def isIn(val, *args):
    """
    check if val is in args

    :return: A boolean value.
    """
    return val in args


def isShorter(val, l: int):
    """
    check if val is string and has len < len(l)

    :return: A boolean value.
    """
    if isStr(val):
        return len(val) < l
    return False


def isDict(val):
    """
    check if val has dict type

    :return: A boolean value.
    """
    return type(val) == dict


def isPath(val):
    """
    check if val is path in package_dir

    :return: A boolean value.
    """
    if val is None:
        return False
    try:
        val = Path(val)
        if val.exists():
            return True
        return False
    except ValueError:
        return False

def resolve_validator(func_list, arg):
    """
    takes the validator function with arguments, and check that if validator function is true for arg (other arguments for func)
    """
    func_name = str(func_list[0])
    func_arguments_ext = ',' + ','.join(func_list[1:])
    return eval(func_name + '("' + str(arg) + '"' + func_arguments_ext + ')')


def hasStructure(val, struct: str):
    """
    check if val has structure provided by struct and fulfills validators functions from struct

    :return: A boolean value.
    """
    validators = findall("<.*?>", struct)
    validators = [i[1:-1].split(',') for i in validators]
    constant_words = findall("[^<>]{0,}<", struct) + findall("[^>]{0,}$", struct)
    constant_words = [i.strip("<") for i in constant_words]
    if len(validators) == 1:
        values_to_check = [val]
    else:
        # words_in_pattern = [i for i in constant_words if i != '|' and i != '']
        # regex_pattern = '|'.join([i for i in constant_words if i != '|' and i != ''])
        values_to_check = split('|'.join([i for i in constant_words if i != '|' and i != '']), val)
    if struct.startswith('<') == False:
        values_to_check = values_to_check[1:]
    valid_idx = 0
    const_w_idx = 0
    values_idx = 0
    temp_alternative = False
    result = True
    while valid_idx < len(validators) and values_idx < len(values_to_check):
        temp_alternative |= resolve_validator(validators[valid_idx], values_to_check[values_idx])
        if constant_words[const_w_idx] == '|':
            if constant_words[const_w_idx + 1] != '|':
                values_idx += 1
        else:
            if constant_words[const_w_idx + 1] != '|':
                values_idx += 1
                result &= temp_alternative
                temp_alternative = False
        valid_idx += 1
        const_w_idx += 1
    return result


def memory_converting(val: str):
    """
     function is converting memory from others units to bytes

     :return: Memory converted to bytes. (In INT type)
    """
    if val[-1] == 'B':
        return int(val[0:-1])
    elif val[-1] == 'K':
        return int(val[0:-1]) * 1024
    elif val[-1] == 'M':
        return int(val[0:-1]) * 1024 * 1024
    elif val[-1] == 'G':
        return int(val[0:-1]) * 1024 * 1024 * 1024


def valid_memory_size(first: str, second: str):
    """
    checks if first is smaller than second considering memory

    :return: A boolean value.
    """
    if memory_converting(first) <= memory_converting(second):
        return True
    return False


def isSize(val: str, max_size: str):
    """
    check if val has structure like <isInt><isIn, 'B', 'K', 'M', 'G'>

    :return: A boolean value.
    """
    val = val.strip()
    return hasStructure(val[:-2], "<isInt>") and hasStructure(val[-1], "<isIn, 'B', 'K', 'M', 'G'>") and valid_memory_size(val, max_size)


def isList(val, *args):
    """
    check if val is a list and every element from list fulfill at least one validator from args

    :return: A boolean value.
    """
    if type(val) == list:
        result = False
        for i in val:
            for j in args:
                result |= hasStructure(i, j)
            if not result:
                return result
    return True