import shutil
from abc import ABC, abstractmethod
from pathlib import Path


class PathCreator:
    class _Path(ABC):
        def __init__(self, path: Path, overwrite: bool = False):
            self.path = path
            self.overwrite = overwrite

        def __str__(self):
            return str(self.path)

        @abstractmethod
        def type_check(self) -> bool:
            pass

        @abstractmethod
        def create(self):
            pass

    class Dir(_Path):
        def type_check(self) -> bool:
            return self.path.is_dir()

        def create(self):
            if not self.path.exists():
                self.path.mkdir(parents=True)
            elif not self.type_check():
                raise FileExistsError(f'Path {self.path} exists but is not a directory')
            elif self.overwrite:
                shutil.rmtree(self.path)
                self.path.mkdir(parents=True)

    class File(_Path):
        def type_check(self) -> bool:
            return self.path.is_file()

        def create(self):
            if not self.path.exists():
                self.path.touch()
            elif not self.type_check():
                raise FileExistsError(f'Path {self.path} exists but is not a file')
            elif self.overwrite:
                self.path.unlink()
                self.path.touch()

    class AssertExist(_Path):
        def __init__(self, path_: 'PathCreator._Path'):
            self._path = path_

        def type_check(self) -> bool:
            return self._path.type_check()

        def create(self):
            if not self._path.path.exists():
                raise FileNotFoundError(f'Path {self._path} does not exist')
            if not self.type_check():
                raise FileNotFoundError(f'Path {self._path} exists but is not '
                                        f'a {self._path.__class__.__name__}')

    def __init__(self):
        self._auto_create_dirs = []

    def add_dir(self, path: Path, overwrite: bool = False):
        self._auto_create_dirs.append(self.Dir(path, overwrite))

    def add_file(self, path: Path, overwrite: bool = False):
        self._auto_create_dirs.append(self.File(path, overwrite))

    def assert_exists(self, path_with_type: 'PathCreator._Path', instant: bool = False):
        exist_tester = self.AssertExist(path_with_type)
        if instant:
            exist_tester.create()
        else:
            self._auto_create_dirs.insert(0, exist_tester)

    def assert_exists_dir(self, path: Path, instant: bool = False):
        self.assert_exists(self.Dir(path), instant)

    def assert_exists_file(self, path: Path, instant: bool = False):
        self.assert_exists(self.File(path), instant)

    def create(self):
        for p in self._auto_create_dirs:
            p.create()
