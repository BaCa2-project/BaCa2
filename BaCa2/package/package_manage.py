from pathlib import Path
from .validators import isAny, isNone, isInt, isIntBetween, isFloat, isFloatBetween, isStr, is_, isIn, isShorter, isDict, isPath, isSize, isList, memory_converting, valid_memory_size
import yaml
from BaCa2.settings import SUPPORTED_EXTENSIONS, BASE_DIR
from BaCa2.exceptions import NoTestFound, NoSetFound
from os import remove, replace, walk, mkdir
from shutil import rmtree


class PackageManager:
    def __init__(self, path: Path, settings_init: Path or dict, default_settings: dict):
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
        self._settings = default_settings | settings


    def __getattr__(self, arg: str):
        try:
            return self._settings[arg]
        except KeyError:
            raise KeyError(f'No key named {arg} has found in self_settings')
    def __setattr__(self, arg: str, val):
        self._settings[arg] = val
        #effect changes to yaml settings
        config_dict = {}
        with open(self._path / 'config.yml', mode="wb", encoding="utf-8") as file:
            yaml.dump(self._settings, file)

    @staticmethod
    def check_validation(arg, validators):
        for i, j in arg.items():
            check = False
            for k in validators[i]:
                check |= k[0](j, *k[1:])
        return check

class Package(PackageManager):
    MAX_SUBMIT_MEMORY = '10G'
    MAX_SUBMIT_TIME = 600
    SETTINGS_VALIDATION = {
        'title': [[isStr]],
        'points': [[isInt], [isFloat]],
        'memory_limit': [[isSize, MAX_SUBMIT_MEMORY]],
        'time_limit': [[isIntBetween, 0, MAX_SUBMIT_TIME], [isFloat, 0, MAX_SUBMIT_TIME]],
        'allowedExtensions': [[isIn, *SUPPORTED_EXTENSIONS], [isList, [isIn, *SUPPORTED_EXTENSIONS]]],
        'hinter': [[isNone], [isPath]],
        'checker': [[isNone], [isPath]],
        'test_generator': [[isNone], [isPath]]
    }
    DEFAULT_SETTINGS = {
        'title': 'p',
        'points': 0,
        'memory_limit': '512M',
        'time_limit': 10,
        'allowedExtensions': 'cpp',
        'hinter': None,
        'checker': None,
        'test_generator': None
    }
    def __init__(self, path: Path):
        config_path = path / 'config.yml'
        super().__init__(path, config_path, Package.DEFAULT_SETTINGS)
        self._sets = []
        for i in [x[0].replace(str(BASE_DIR  / 'package') + '\\', '') for x in walk(BASE_DIR  / "package")][1:]:
            self._sets.append(TSet(path / i))

    def sets(self, set_name: str, add_new: bool=False):
        for i in self._sets:
            if i['name'] == set_name:
                return i
        if add_new:
            settings = {'name': set_name} | self._settings
            set_path = self._path / set_name
            if not isPath(set_path):
                mkdir(set_path)
            return TSet(set_path)
        raise NoSetFound(f'Any set directory named {set_name} has found')

    def delete_set(self, set_name: str):
        for i in self._tests:
            if i['name'] == set_name:
                self._sets.remove(i)
                if isPath(self._path / set_name):
                    rmtree(self._path / set_name)
                return
        raise NoSetFound(f'Any set directory named {set_name} has found to delete')

    def check_package(self, subtree: bool=True):
        result = True
        if subtree:
            for i in self._sets:
                result &= i.check_set()

        return PackageManager.check_validation(self._settings, Package.SETTINGS_VALIDATION) & result

class TSet(PackageManager):
    SETTINGS_VALIDATION = {
        'name': [[isStr]],
        'weight': [[isInt], [isFloat]],
        'memory_limit': [[isNone], [isSize, Package.MAX_SUBMIT_MEMORY]],
        'time_limit': [[isNone], [isIntBetween, 0, Package.MAX_SUBMIT_TIME], [isFloat, 0, Package.MAX_SUBMIT_TIME]],
        'checker': [[isNone], [isPath]],
        'test_generator': [[isNone], [isPath]],
        'tests': [[isNone], [isAny]],
        'makefile': [[isNone], [isPath]]
    }
    DEFAULT_SETTINGS = {
        'name': 'set0',
        'weight': 10,
        'memory_limit': '512M',
        'time_limit': '10s',
        'checker': None,
        'test_generator': None,
        'tests': {},
        'makefile': None
    }
    def __init__(self, path: Path):
        config_path = path / 'config.yml'
        super().__init__(path, config_path, TSet.DEFAULT_SETTINGS)
        self._tests = []
        for i, j in self._settings['tests'].items():
            test_path = i.replace("test", "") + '.in'
            self._tests.append(TestF(path / test_path, j, TSet.DEFAULT_SETTINGS))


    def tests(self, test_name: str, add_new: bool=False):
        for i in self._tests:
            if i['name'] == test_name:
                return i
        if add_new:
            settings = {'name': test_name} | self._settings
            test_path = test_name.replace("test", "") + '.in'
            new_test = TestF(self._path / test_path, settings, TSet.DEFAULT_SETTINGS)
            return new_test
        raise NoTestFound(f'Any test named {test_name} has found')

    def delete_set(self, test_name: str):
        for i in self._tests:
            if i['name'] == test_name:
                self._tests.remove(i)
                in_to_delete = 'test' + test_name + '.in'
                out_to_delete = 'test' + test_name + '.out'
                if isPath(self._path / in_to_delete):
                    remove(in_to_delete)
                if isPath(self._path / out_to_delete):
                    remove(out_to_delete)
                return
        raise NoTestFound(f'Any test named {test_name} has found to delete')

    def move_test(self, test_name: str, to_set: 'TSet'):
        for i in self._tests:
            if i['name'] == test_name:
                to_set._tests.append(i)
                self._tests.remove(i)
                if isPath('', to_set._path):
                    process_name = 'test' + test_name + '.in'
                    if isPath(process_name, self._path):
                        replace(self._path / process_name, to_set._path / process_name)
                    process_name.replace('.in', '.out')
                    if isPath('test' + test_name, self._path):
                        replace(self._path / process_name, to_set._path / process_name)
        raise NoTestFound(f'Any test named {test_name} has found to move to to_set')

    def check_set(self, subtree=True):
        result = True
        if subtree:
            for i in self._tasks:
                result &= i.check_test()

        return PackageManager.check_validation(self._settings, TSet.SETTINGS_VALIDATION) & result

class TestF(PackageManager):
    SETTINGS_VALIDATION = {
        'name': [[isStr]],
        'memory_limit': [[isNone],[isSize, Package.MAX_SUBMIT_MEMORY]],
        'time_limit': [[isNone],[isIntBetween, 0, Package.MAX_SUBMIT_TIME], [isFloatBetween, 0, Package.MAX_SUBMIT_TIME]],
    }
    def __init__(self, path: Path, additional_settings: dict, default_settings: dict):
        super().__init__(path, additional_settings, default_settings)

    def __setattr__(self, key, value):
        pass
    def __getattr__(self, key):
        pass
    def check_test(self):
        return PackageManager.check_validation(self._settings, TestF.SETTINGS_VALIDATION)
