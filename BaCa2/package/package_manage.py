from pathlib import Path
from validators import *
import yaml

class PackageManager:
    def __init__(self, path: Path, settings_init: Path, default_settings: dict):
        if isPath("config.yml", path):
            _path = yaml.dump(yaml.load(path / "config.yml"))
        _settings = settings_init
    def __getattr__(self, arg: str):
        pass
    def __setattr__(self, arg: str, val):
        pass


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
