from pathlib import Path

from .misc import random_id


class FileHandler:
    """
    A class used to handle file operations such as saving and deleting.

    :param path: The directory path where the file will be saved
    :type path: Path
    :param extension: The extension of the file
    :type extension: str
    :param file_data: The data that will be written to the file
    :type file_data: Any
    :raises FileNotFoundError: If the path does not exist or is not a directory
    """

    def __init__(self, path: Path, extension: str, file_data):
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError('The path does not exist or is not a directory')
        self.file_data = file_data
        self.extension = extension
        self.file_id = random_id()
        self.path = path / f'{self.file_id}.{extension}'

    def save(self):
        """
        Saves the file data to the file path.
        """
        with open(self.path, 'wb+') as file:
            for chunk in self.file_data.chunks():
                file.write(chunk)

    def delete(self):
        """
        Deletes the file from the file path.
        """
        self.path.unlink()


class DocFileHandler:
    """
    A class used to handle document file operations such as saving and deleting.

    :param path: The file path of the document
    :type path: Path
    :param extension: The extension of the document file
    :type extension: str
    :param file_id: The unique identifier of the file, if not provided a random id will be generated
    :type file_id: str, optional
    :raises FileNotFoundError: If the path does not exist or is not a file
    """

    class FileNotStaticError(Exception):
        """
        An exception raised when the file is not saved in a static directory.
        """
        pass

    def __init__(self, path: Path, extension: str, file_id: str = None):
        if not (path.exists() and path.is_file()):
            raise FileNotFoundError('The path does not exist or is not a file')
        self.path = path
        self.extension = extension
        if file_id:
            self.file_id = file_id
        else:
            self.file_id = random_id()

    @classmethod
    def check_if_path_in_docs(cls, path: Path) -> bool:
        """
        Checks if the document file is saved in a static directory.

        :param path: The path to the file
        :type path: Path
        :return: True if the file is saved in a static directory, False otherwise
        :rtype: bool
        """
        from django.conf import settings

        if settings.TASK_DESCRIPTIONS_DIR in path.parents:
            return True
        return False

    @classmethod
    def delete_doc(cls, path: Path) -> None:
        """
        Deletes the document file from a static directory.

        :param path: The path to the file
        :type path: Path
        :raises FileNotStaticError: If the file is not saved in a static directory
        """
        if not cls.check_if_path_in_docs(path):
            raise cls.FileNotStaticError('The file is not saved in a static directory')

        if path.exists():
            path.unlink()

    def save_as_static(self) -> Path:
        """
        Saves the document file to a static directory.

        :return: The path to the saved file
        :rtype: Path
        """
        from django.conf import settings

        static_path = settings.TASK_DESCRIPTIONS_DIR / f'{self.file_id}.{self.extension}'
        while static_path.exists():
            self.file_id = random_id()
            static_path = settings.TASK_DESCRIPTIONS_DIR / f'{self.file_id}.{self.extension}'

        with open(self.path, 'rb') as file:
            with open(static_path, 'wb+') as static_file:
                static_file.write(file.read())
        return static_path
