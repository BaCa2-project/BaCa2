from pathlib import Path

from .misc import random_id


class FileHandler:
    def __init__(self, path: Path, extension: str, file_data):
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError('The path does not exist or is not a directory')
        self.file_data = file_data
        self.extension = extension
        self.file_id = random_id()
        self.path = path / f'{self.file_id}.{extension}'

    def save(self):
        with open(self.path, 'wb+') as file:
            for chunk in self.file_data.chunks():
                file.write(chunk)

    def delete(self):
        self.path.unlink()
