from pathlib import Path
from .validators import isAny, isNone, isInt, isIntBetween, isFloat, isFloatBetween, isStr, is_, isIn, isShorter, \
    isDict, isPath, isSize, isList, memory_converting, valid_memory_size
from yaml import safe_load, dump
from re import match
from BaCa2.settings import SUPPORTED_EXTENSIONS, BASE_DIR
from BaCa2.exceptions import NoTestFound, NoSetFound, TestExistError
from os import remove, replace, walk, mkdir, rename, listdir
from shutil import rmtree


def merge_settings(default: dict, to_add: dict) -> dict:
    """
    It takes two dictionaries, and returns a new dictionary that has the keys of the first dictionary, and the values of the
    second dictionary if they exist, otherwise the values of the first dictionary. It overwrites default dict with valuses from to_add

    :param default: The default settings
    :type default: dict
    :param to_add: The settings you want to add to the default settings
    :type to_add: dict
    :return: A dictionary with the keys of the default dictionary and the values of the to_add dictionary.
    """
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



# It's a class that manages a package's settings
class PackageManager:
    def __init__(self, path: Path, settings_init: Path or dict, default_settings: dict):
        """
        If the settings_init is a dict, assign it to settings. If not, load the settings_init yaml file and assign it to
        settings. Then merge the settings with the default settings

        :param path: Path to the settings file
        :type path: Path
        :param settings_init: This is the path to the settings file
        :type settings_init: Path or dict
        :param default_settings: a dict with default settings
        :type default_settings: dict
        """
        self._path = path
        # if type of settings_init is a dict assign settings_init to processed settings
        settings = {}
        if type(settings_init) == dict:
            if bool(settings_init):
                settings = settings_init
        # if not, make dict from settings_init yaml
        else:
            # unpacking settings file to dict
            with open(settings_init, mode="rt", encoding="utf-8") as file:
                settings = safe_load(file)
        # merge external settings with default
        self._settings = merge_settings(default_settings, settings)

    def __getitem__(self, arg: str):
        """
        If the key is in the dictionary, return the value. If not, raise a KeyError

        :param arg: The name of the key to get the value of
        :type arg: str
        :return: The value of the key in the dictionary.
        """
        try:
            return self._settings[arg]
        except KeyError:
            raise KeyError(f'No key named {arg} has found in self_settings')

    def __setitem__(self, arg: str, val):
        """
        `__setitem__` is a special method that allows us to use the `[]` operator to set a value in a dictionary

        :param arg: str
        :type arg: str
        :param val: the value to be set
        """
        self._settings[arg] = val
        # effect changes to yaml settings
        self.save_to_config(self._settings)

    def check_validation(self, validators):
        """
        It checks if the value of the setting is valid by checking if it matches any of the validators for that setting

        :param validators: A dictionary of validators. The keys are the names of the settings, and the values are lists of
        validators. Each validator is a tuple of the form (function, *args, **kwargs). The function is called with the
        setting value as the first argument, followed by the *
        :return: The check variable is being returned.
        """
        for i, j in self._settings.items():
            check = False
            for k in validators[i]:
                check |= k[0](j, *k[1:])
        return check

    def save_to_config(self, settings):
        """
        It opens a file called config.yml in the directory specified by the path attribute of the object, and writes the
        settings dictionary to it.

        :param settings: The settings to save
        """
        with open(self._path / 'config.yml', mode="wt", encoding="utf-8") as file:
            dump(settings, file)

    def read_from_config(self):
        """
        It reads the config.yml file from the path and returns the contents
        :return: The dict from config.yml file is being returned.
        """
        with open(self._path / 'config.yml', mode="rt", encoding="utf-8") as file:
            return safe_load(file)

    def add_empty_file(self, filename):
        """
        It creates an empty file if it doesn't already exist

        :param filename: The name of the file to be created
        """
        if not isPath(self._path / filename):
            with open(self._path / filename, 'w') as f:
                pass



# It's a class that represents a package
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

    def __init__(self, path: Path):
        """
        It takes a path to a folder, and then it creates a list of all the subfolders in that folder, and then it creates a
        TSet object for each of those subfolders

        :param path: Path - the path to the package
        :type path: Path
        """
        config_path = path / 'config.yml'
        sets_path = path / 'tests'
        super().__init__(path, config_path, Package.DEFAULT_SETTINGS)
        self._sets = []
        for i in [x[0].replace(str(sets_path) + '\\', '') for x in walk(sets_path)][1:]:
            self._sets.append(TSet(sets_path / i))

    def rm_tree(self, set_name):
        """
        It removes a directory tree

        :param set_name: The name of the test set
        """
        if isPath(self._path / 'tests' / set_name):
            rmtree(self._path / 'tests' / set_name)

    def copy(self, new_path, new_commit) -> 'Package':
        pass

    def delete(self):
        pass

    def _add_new_set(self, set_name):
        """
        > This function adds a new test set to the test suite

        :param set_name: The name of the new test set
        :return: A new TSet object.
        """
        settings = {'name': set_name} | self._settings
        set_path = self._path / 'tests' / set_name
        if not isPath(set_path):
            mkdir(set_path)
            with open(set_path / 'config.yml', 'w') as file:
                dump({'name': set_name}, file)
        new_set = TSet(set_path)
        self._sets.append(new_set)
        return new_set

    def sets(self, set_name: str, add_new: bool = False):
        """
        It returns the set with the name `set_name` if it exists, otherwise it raises an error

        :param set_name: The name of the set you want to get
        :type set_name: str
        :param add_new: If True, it will create a new set directory if it doesn't exist, defaults to False
        :type add_new: bool (optional)
        :return: The set with the name set_name
        """
        for i in self._sets:
            if i['name'] == set_name:
                return i
        if add_new:
            self._add_new_set(set_name)
        else:
            raise NoSetFound(f'Any set directory named {set_name} has found')

    def delete_set(self, set_name: str):
        """
        It deletes a set from the sets list and removes the directory of the set

        :param set_name: The name of the set you want to delete
        :type set_name: str
        :return: the list of sets.
        """
        for i in self._sets:
            if i['name'] == set_name:
                self._sets.remove(i)
                self.rm_tree(set_name)
                return
        raise NoSetFound(f'Any set directory named {set_name} has found to delete')

    def check_package(self, subtree: bool = True):
        """
        It checks the package.

        :param subtree: bool = True, defaults to True
        :type subtree: bool (optional)
        :return: The result of the check_validation() method and the result of the check_set() method.
        """
        result = True
        if subtree:
            for i in self._sets:
                result &= i.check_set()
        return self.check_validation(Package.SETTINGS_VALIDATION) & result


# It's a class that represents a set of tests
class TSet(PackageManager):
    SETTINGS_VALIDATION = {
        'name': [[isStr]],
        'weight': [[isInt], [isFloat]],
        'points': [[isInt], [isFloat]],
        'memory_limit': [[isNone], [isSize, Package.MAX_SUBMIT_MEMORY]],
        'time_limit': [[isNone], [isIntBetween, 0, Package.MAX_SUBMIT_TIME],
                       [isFloatBetween, 0, Package.MAX_SUBMIT_TIME]],
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
        """
        It reads the config file and creates a list of tests

        :param path: Path - path to the test set
        :type path: Path
        """
        config_path = path / 'config.yml'
        super().__init__(path, config_path, TSet.DEFAULT_SETTINGS)
        self._tests = []
        self._test_settings = {
            'name': '0',
            'memory_limit': self._settings['memory_limit'],
            'time_limit': self._settings['time_limit'],
            'points': 0
        }
        if self._settings['tests'] is not None:
            for i in self._settings['tests'].values():
                self._tests.append(TestF(path, i, self._test_settings))
        self._add_test_from_dir()

    def move_test_file(self, to_set, filename):
        """
        It moves a file from one directory to another

        :param to_set: the set you want to move the file to
        :param filename: the name of the file to move
        """
        if isPath(to_set._path):
            if isPath(self._path / filename):
                replace(self._path / filename, to_set._path / filename)

    def _add_test_from_dir(self):
        """
        It takes a directory, finds all the files in it, and then adds all the tests that have both an input and output file
        """
        test_files_ext = listdir(self._path)
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
                self._tests.append(TestF(self._path, name_dict, self._test_settings))

    def tests(self, test_name: str, add_new: bool = False):
        """
        It returns a test object with the given name, if it exists, or creates a new one if it doesn't

        :param test_name: The name of the test
        :type test_name: str
        :param add_new: if True, then if the test is not found, it will be created, defaults to False
        :type add_new: bool (optional)
        :return: A TestF object
        """
        for i in self._tests:
            if i['name'] == test_name:
                return i
        if add_new:
            new_test = TestF(self._path, {'name': test_name}, self._test_settings)
            self._tests.append(new_test)
            self.add_empty_file(test_name + '.in')
            self.add_empty_file(test_name + '.out')
            return new_test
        raise NoTestFound(f'Any test named {test_name} has found')

    def remove_file(self, filename):
        """
        It removes a file from the current directory

        :param filename: The name of the file to remove
        """
        if isPath(self._path / filename):
            remove(self._path / filename)

    def _delete_chosen_test(self, test: 'TestF'):
        """
        It removes the test from the list of tests, deletes the files associated with the test,
        and removes the test from the config file

        :param test: the test to be deleted
        :type test: 'TestF'
        """
        self._tests.remove(test)
        self.remove_file(test['name'] + '.in')
        self.remove_file(test['name'] + '.out')

        # removes settings for this test (from _settings and from config file)
        new_settings = deepcopy(self._settings)
        for k, v in self._settings['tests'].items():
            if v['name'] == test['name']:
                new_settings['tests'].pop(k)
        self._settings = new_settings
        self.save_to_config(self._settings)

    def delete_test(self, test_name: str):
        """
        It deletes a test from the list of tests, and deletes associated files.

        :param test_name: The name of the test to delete
        :type test_name: str
        :raise NoTestsFound: If there is no test with name equal to the test_name argument.
        """
        for test in self._tests:
            if test['name'] == test_name:
                self._delete_chosen_test(test)
                return

        raise NoTestFound(f'No test named {test_name} has found to delete')

    def _move_chosen_test(self, test: 'TestF', to_set: 'TSet'):
        """
        > Move a test from one test set to another

        :param test: 'TestF' - the test to be moved
        :type test: 'TestF'
        :param to_set: the set to which the test will be moved
        :type to_set: 'TSet'
        """
        name_list_ta = [j['name'] for j in to_set._tests]
        if test['name'] not in name_list_ta:
            to_set._tests.append(test)
            self._tests.remove(test)
        else:
            raise TestExistError(f'Test named {test["name"]} exist in to_set files')

        self.move_test_file(to_set, test['name'] + '.in')
        self.move_test_file(to_set, test['name'] + '.out')

    def _move_config(self, to_set: 'TSet', test_name: str):
        """
        It takes a test name and a set object, and moves the test from the current set to the set object

        :param to_set: The set to move the test to
        :type to_set: 'TSet'
        :param test_name: The name of the test you want to move
        :type test_name: str
        """
        new_settings = deepcopy(self._settings)
        for i, j in self._settings['tests'].items():
            if j['name'] == test_name:
                to_set._settings['tests'][i] = j
                new_settings['tests'].pop(i)

        self._settings = new_settings
        self.remove_file('config.yml')
        self.save_to_config(self._settings)
        to_set.remove_file('config.yml')
        to_set.save_to_config(to_set._settings)

    # moves test to to_set (and all settings pinned to this test in self._settings)
    def move_test(self, test_name: str, to_set: 'TSet'):
        """
        It moves a test from one set to another

        :param test_name: The name of the test to move
        :type test_name: str
        :param to_set: The set to which the test will be moved
        :type to_set: 'TSet'
        """
        search = False
        for i in self._tests:
            if i['name'] == test_name:
                self._move_chosen_test(i,  to_set)
                self._move_config(to_set, test_name)
                search |= True
                return
            search |= False

        if not search:
            raise NoTestFound(f'Any test named {test_name} has found to move to to_set')

    # check set validation
    def check_set(self, subtree=True):
        """
        It checks the set.

        :param subtree: If True, check the subtree of tests, defaults to True (optional)
        :return: The result of the check_validation() method and the result of the check_set() method.
        """
        result = True
        if subtree:
            for i in self._tests:
                result &= i.check_test()

        return self.check_validation(TSet.SETTINGS_VALIDATION) & result


# class for represent test in set
class TestF(PackageManager):
    SETTINGS_VALIDATION = {
        'name': [[isStr]],
        'memory_limit': [[isNone], [isSize, Package.MAX_SUBMIT_MEMORY]],
        'time_limit': [[isNone], [isIntBetween, 0, Package.MAX_SUBMIT_TIME],
                       [isFloatBetween, 0, Package.MAX_SUBMIT_TIME]],
        'points': [[isInt], [isFloat]]
    }

    def __init__(self, path: Path, additional_settings: dict or Path, default_settings: dict):
        """
        This function initializes the class by calling the superclass's __init__ function, which is the __init__ function of
        the Config class

        :param path: The path to the file that contains the settings
        :type path: Path
        :param additional_settings: This is a dictionary of settings that you want to override the default settings with
        :type additional_settings: dict or Path
        :param default_settings: This is a dictionary of default settings that will be used if the settings file doesn't
        contain a value for a setting
        :type default_settings: dict
        """
        super().__init__(path, additional_settings, default_settings)

    def _rename_files(self, old_name, new_name):
        """
        It renames a file

        :param old_name: The name of the file you want to rename
        :param new_name: The new name of the file
        """
        rename(self._path / old_name, self._path / new_name)

    def __setitem__(self, arg: str, val):
        """
        It renames the files and changes the name in the yaml file

        :param arg: the key of the dictionary
        :type arg: str
        :param val: the new value
        """
        # effect changes to yaml settings
        settings = self.read_from_config()
        if arg == 'name':
            self._rename_files(self._settings['name'] + '.in', val + '.in')
            self._rename_files(self._settings['name'] + '.out', val + '.out')

            for i, j in settings['tests'].items():
                if j['name'] == self._settings['name']:
                    new_key = 'test' + val
                    j[arg] = val
                    settings['tests'][new_key] = j
                    del settings['tests'][i]
                    break

        self.save_to_config(settings)
        self._settings[arg] = val


    def check_test(self):
        """
        It checks if the test is valid
        :return: The return value is the result of the check_validation method.
        """
        return self.check_validation(TestF.SETTINGS_VALIDATION)
