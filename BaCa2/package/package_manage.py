from pathlib import Path
from validators import *
import yaml

#returns None is value doesn't found
def key_to_value_search(key, dictionary: dict):
    for i, j in dictionary.items():
        if isDict(j):
            if i == key:
                return j
            return key_to_value_search(key, j)
        else:
            if i == key:
                return j

#merge default settings with external settings which can be incomplete
def merge_settings(default: dict, to_add: dict):
    for i, j in default.items():
        found_value = key_to_value_search(i, to_add)
        if isDict(j):
            default[i] = merge_settings(j, found_value)
        else:
            if found_value is not None:
                default[i] = found_value
    return default
def get_value_from_nested_dict(keys: str, search_dict: dict):
    keys_list = keys.split(': ')
    temp_dict = search_dict
    for i in keys_list:
        value = key_to_value_search(i, temp_dict)
        if isDict(value) == False:
            return value
        temp_dict = value

def set_value_to_key(key, dictionary: dict, val):
    for i, j in dictionary.items():
        if isDict(j):
            if i == key:
                dictionary[i] = val
                return
            return set_value_to_key(key, j, val)
        else:
            if i == key:
                dictionary[i] = val
                return
def set_value_to_nested_dict(keys: str, _dict: dict, val):
    keys_list = keys.split(': ')
    temp_dict = _dict
    for i in keys_list:
        value = key_to_value_search(i, temp_dict)
        if i == keys_list[-1]:
            set_value_to_key(i, temp_dict, val)
            return
        elif isDict(value) == True:
            temp_dict = value

class PackageManager:
    def __init__(self, path: Path, settings_init: Path, default_settings: dict):
        self._path = path
        #if type of settings_init is a dict assign _settings attribute
        settings = {}
        if type(settings_init) == dict:
            settings = settings_init
        #if not, make dict from settings_init yaml
        else:
            #unpacking settings file to dict
            with open(settings_init, mode="wt", encoding="utf-8") as file:
                yaml.dump(settings, file)
        #merge external settings with default
        self._settings = merge_settings(default_settings, settings)


    def __getattr__(self, arg: str):
        searching_value = get_value_from_nested_dict(arg, self._settings)
        if searching_value is not None:
            return searching_value
        raise KeyError

    def __setattr__(self, arg: str, val):
        set_value_to_nested_dict(arg, self._settings, val)
        #effect changes to yaml settings

class Package(PackageManager):
    def __init__(self, path: Path):
        _test_sets = 'x'
        super().__init__(path, config_path, default_settings)

    def sets(self, set_name: str, add_new: bool=False):
        pass
    def delete_set(self, set_name: str):
        pass
    def check_package(self, subtree: bool=True):
        pass

class TSet(PackageManager):
    def __init__(self, path: Path):
        super().__init__(path, config_path, default_settings)

    def tests(self, test_name: str, add_new: bool=False):
        pass
    def delete_set(self, test_name: str):
        pass
    def move_test(self, test_name: str, to_set: str):
        pass

    def check_set(self, subtree=True):
        pass

class TestF(PackageManager):
    def __init__(self, path: Path, **additional_settings):
        super().__init__(path, additional_settings, default_settings)

    def check_test(self):
        pass



data = """
memory: 512MB
kolejka:
    image       : 'kolejka/satori:extended'
    exclusive   : false
    collect     : [ 'log.zip' ]
    limits: 
        memory      : '4G'
        swap        : 0
        network     : false
        pids        : 256
        storage     : '2G'
"""
default = """
    time        : '20s'
    memory      : '4G'
    swap        : 0
    cpus        : 4
    network     : false
    pids        : 256
    storage     : '2G'
    workspace   : '2G'
"""
doc = yaml.safe_load(data)
defaultd = yaml.safe_load(default)
# print(doc)
# print(doc.has_key('image'))

print(doc)
print(defaultd)
print(key_to_value_search('cpus', doc))
dict1 = merge_settings(defaultd, doc)
print(dict1)
print(get_value_from_nested_dict('memory', doc))
set_value_to_key('memory', doc, '8G')
print(doc)
set_value_to_nested_dict('limits: memory', doc, '2M')

print(doc)
