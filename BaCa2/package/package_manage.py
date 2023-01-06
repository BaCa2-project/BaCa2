from pathlib import Path
from .validators import isAny, isNone, isInt, isIntBetween, isFloat, isFloatBetween, isStr, is_, isIn, isShorter, isDict, isPath, isSize, isList, memory_converting, valid_memory_size
from yaml import safe_load, dump
from re import match
from BaCa2.settings import SUPPORTED_EXTENSIONS, BASE_DIR
from BaCa2.exceptions import NoTestFound, NoSetFound, TestExistError
from os import remove, replace, walk, mkdir, rename, listdir
from shutil import rmtree
from copy import deepcopy

#merge default settings with additional from given in to_add
def merge_settings(default: dict, to_add: dict) -> dict:
    new = {}
    for i in default.keys():
        if to_add is not None:
            if i in to_add.keys() and to_add[i] is not None:
                new[i] = to_add[i]
            else:
                new[i] = default[i]
        else:
            new[i] = default[i]
    return new

#abstract class for basic functionality in class Package, TSet, TestF
class PackageManager:
    def __init__(self, path: Path, settings_init: Path or dict, default_settings: dict):
        self._path = path
        #if type of settings_init is a dict assign settings_init to processed settings
        settings = {}
        if type(settings_init) == dict:
            if bool(settings_init):
                settings = settings_init
        #if not, make dict from settings_init yaml
        else:
            #unpacking settings file to dict
            with open(settings_init, mode="rt", encoding="utf-8") as file:
                settings = safe_load(file)

        #merge external settings with default
        self._settings = merge_settings(default_settings, settings)

    #get item from self._settings dict
    def __getitem__(self, arg: str):
        try:
            return self._settings[arg]
        except KeyError:
            raise KeyError(f'No key named {arg} has found in self_settings')

    #set item to self._settings dict and make changes in the config file
    def __setitem__(self, arg: str, val):
        self._settings[arg] = val
        #effect changes to yaml settings
        config_dict = {}
        with open(self._path / 'config.yml', mode="wt", encoding="utf-8") as file:
            dump(self._settings, file)

    #validate self._settings with class-specific validators
    def check_validation(self, validators):
        for i, j in self._settings.items():
            check = False
            for k in validators[i]:
                check |= k[0](j, *k[1:])
        return check

#main class for package
class Package(PackageManager):
    MAX_SUBMIT_MEMORY = '10G'
    MAX_SUBMIT_TIME = 600
    SETTINGS_VALIDATION = {
        'title': [[isStr]],
        'points': [[isInt], [isFloat]],
        'memory_limit': [[isSize, MAX_SUBMIT_MEMORY]],
        'time_limit': [[isIntBetween, 0, MAX_SUBMIT_TIME], [isFloatBetween, 0, MAX_SUBMIT_TIME]],
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
    #config_path not include config file
    def __init__(self, path: Path):
        config_path = path / 'config.yml'
        sets_path = path / 'tests'
        super().__init__(path, config_path, Package.DEFAULT_SETTINGS)
        self._sets = []
        #appends sets represented in the path as folders
        for i in [x[0].replace(str(sets_path) + '\\', '') for x in walk(sets_path)][1:]:
            self._sets.append(TSet(sets_path/ i))

    #add new set to _sets, if add_new == True, make a new set (make dir and make config file for this set)
    def sets(self, set_name: str, add_new: bool=False):
        for i in self._sets:
            if i['name'] == set_name:
                return i
        if add_new:
            settings = {'name': set_name} | self._settings
            set_path = self._path / 'tests' / set_name
            if not isPath(set_path):
                mkdir(set_path)
                with open(set_path / 'config.yml', 'w') as f:
                    f.write(f'name: {set_name}')
            new_set = TSet(set_path)
            self._sets.append(new_set)
            return new_set
        else:
            raise NoSetFound(f'Any set directory named {set_name} has found')

    #delete set from _sets and remove dir from path
    def delete_set(self, set_name: str):
        for i in self._sets:
            if i['name'] == set_name:
                self._sets.remove(i)
                if (self._path / 'tests' / set_name).exists():
                    rmtree(self._path / 'tests' / set_name)
                return
        raise NoSetFound(f'Any set directory named {set_name} has found to delete')

    #check _settings validation
    def check_package(self, subtree: bool=True):
        result = True
        if subtree:
            for i in self._sets:
                result &= i.check_set()
        return self.check_validation(Package.SETTINGS_VALIDATION) & result

#class for representing set in package
class TSet(PackageManager):
    SETTINGS_VALIDATION = {
        'name': [[isStr]],
        'weight': [[isInt], [isFloat]],
        'points': [[isInt], [isFloat]],
        'memory_limit': [[isNone], [isSize, Package.MAX_SUBMIT_MEMORY]],
        'time_limit': [[isNone], [isIntBetween, 0, Package.MAX_SUBMIT_TIME], [isFloatBetween, 0, Package.MAX_SUBMIT_TIME]],
        'checker': [[isNone], [isPath]],
        'test_generator': [[isNone], [isPath]],
        'tests': [[isNone], [isAny]],
        'makefile': [[isNone], [isPath]]
    }
    DEFAULT_SETTINGS = {
        'name': 'set0',
        'weight': 10,
        'points': 0,
        'memory_limit': '512M',
        'time_limit': 10,
        'checker': None,
        'test_generator': None,
        'tests': {},
        'makefile': None
    }

    def __init__(self, path: Path):
        config_path = path / 'config.yml'
        super().__init__(path, config_path, TSet.DEFAULT_SETTINGS)
        self._tests = []
        #default settings for test
        self._test_settings = {
            'name': '0',
            'memory_limit': self._settings['memory_limit'],
            'time_limit': self._settings['time_limit'],
            'points': 0
        }
        #appends tests which are described in config file
        if self._settings['tests'] is not None:
            for i in self._settings['tests'].values():
                self._tests.append(TestF(path, i, self._test_settings))
        #appedns tests that consist of an in and out file
        test_files_ext = listdir(path)
        tests = []
        for i in test_files_ext:
            tests.append(match('.*[^.in|out]', i).group(0))
        tests_to_do = []
        for i in tests:
            if tests.count(i) == 2:
                tests_to_do.append(i)
        tests_to_do = set(tests_to_do)
        names = [i["name"] for i in self._tests]
        for i in tests_to_do:
            if i not in names:
                name_dict = {'name': i}
                self._tests.append(TestF(path, name_dict, self._test_settings))

    #returns test for 'name' == test_name, or add new if add_new == True (add .in and .out file named test_name)
    def tests(self, test_name: str, add_new: bool=False):
        for i in self._tests:
            if i['name'] == test_name:
                return i
        if add_new:
            new_test = TestF(self._path, {'name': test_name} , self._test_settings)
            self._tests.append(new_test)
            infile = test_name + '.in'
            #add .in and .out files
            if not isPath(self._path / infile):
                with open(self._path / infile, 'w') as f:
                    pass
            outfile = test_name + '.out'
            if not isPath(self._path / outfile):
                with open(self._path / outfile, 'w') as f:
                    pass
            return new_test
        raise NoTestFound(f'Any test named {test_name} has found')

    #delete test from tests and .in and .out files
    def delete_test(self, test_name: str):
        search = False
        for i in self._tests:
            if i['name'] == test_name:
                self._tests.remove(i)
                in_to_delete = self._path / (test_name + '.in')
                out_to_delete = self._path / (test_name + '.out')
                #removes files if its exists in path
                if isPath(in_to_delete):
                    remove(in_to_delete)
                if isPath(out_to_delete):
                    remove(out_to_delete)
                #removes settings for this test (from _settings and from config file)
                new_settings = deepcopy(self._settings)
                for i, j in self._settings['tests'].items():
                    if j['name'] == test_name:
                        new_settings['tests'].pop(i)
                with open(self._path / 'config.yml', mode="wt", encoding="utf-8") as file:
                    dump(new_settings, file)
                search |= True
                return
            search |= False
        if not search:
            raise NoTestFound(f'Any test named {test_name} has found to delete')

    #moves test to to_set (and all settings pinned to this test in self._settings)
    def move_test(self, test_name: str, to_set: 'TSet'):
        search = False
        for i in self._tests:
            if i['name'] == test_name:
                name_list_ta = [j['name'] for j in to_set._tests]
                if test_name not in name_list_ta:
                    to_set._tests.append(i)
                    self._tests.remove(i)
                else:
                    raise TestExistError(f'Test named {test_name} exist in to_set files')
                if isPath(to_set._path):
                    process_name = test_name + '.in'
                    if (self._path / process_name).exists():
                        replace(self._path / process_name, to_set._path / process_name)
                    process_name = test_name + '.out'
                    if (self._path / process_name).exists():
                        replace(self._path / process_name, to_set._path / process_name)
                #move settings for this test to to_set config file
                new_settings = deepcopy(self._settings)
                for i, j in self._settings['tests'].items():
                    if j['name'] == test_name:
                        to_set._settings['tests'][i] = j
                        new_settings['tests'].pop(i)

                self._settings = new_settings
                remove(self._path / 'config.yml')
                with open(self._path / 'config.yml', mode="wt", encoding="utf-8") as file:
                    dump(new_settings, file)
                remove(to_set._path / 'config.yml')
                with open(to_set._path / 'config.yml', mode="wt", encoding="utf-8") as file:
                    dump(to_set._settings, file)
                search |= True
                return
            search |= False

        if not search:
            raise NoTestFound(f'Any test named {test_name} has found to move to to_set')

    #check set validation
    def check_set(self, subtree=True):
        result = True
        if subtree:
            for i in self._tests:
                result &= i.check_test()

        return self.check_validation(TSet.SETTINGS_VALIDATION) & result

#class for represent test in set
class TestF(PackageManager):
    SETTINGS_VALIDATION = {
        'name': [[isStr]],
        'memory_limit': [[isNone],[isSize, Package.MAX_SUBMIT_MEMORY]],
        'time_limit': [[isNone],[isIntBetween, 0, Package.MAX_SUBMIT_TIME], [isFloatBetween, 0, Package.MAX_SUBMIT_TIME]],
        'points': [[isInt], [isFloat]]
    }
    def __init__(self, path: Path, additional_settings: dict or Path, default_settings: dict):
        super().__init__(path, additional_settings, default_settings)

    #specific setitem, if arg is 'name', then rename .in and .out files
    def __setitem__(self, arg: str, val):
        #effect changes to yaml settings
        config_file = self._path / 'config.yml'

        settings = {}
        with open(config_file, mode="rt", encoding="utf-8") as file:
            settings = safe_load(file)

        if arg == 'name':
            infile = self._settings['name'] + '.in'
            new_infile = val + '.in'
            rename(self._path / infile, self._path / new_infile)
            outfile = infile.replace('.in', '.out')
            new_outfile = new_infile.replace('.in', '.out')
            rename(self._path / outfile, self._path / new_outfile)

            for i, j in settings['tests'].items():
                if j['name'] == self._settings['name']:
                    new_key = 'test' + val
                    j[arg] = val
                    settings['tests'][new_key] = j
                    del settings['tests'][i]
                    break

        with open(config_file, mode="wt", encoding="utf-8") as file:
            dump(settings, file)

        self._settings[arg] = val

    #check test validation
    def check_test(self):
        return self.check_validation(TestF.SETTINGS_VALIDATION)


