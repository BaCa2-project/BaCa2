import csv
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

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

    class FileContentError(Exception):
        """
        An exception raised when the file content is invalid.
        """
        pass

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


class CsvFileHandler(FileHandler):
    def __init__(self, path: Path, file_data, fieldnames: Optional[List[str]] = None):
        super().__init__(path, 'csv', file_data)
        self.fieldnames = fieldnames
        self.data = None

    def read_csv(self,
                 force_fieldnames: Optional[List[str]] = None,
                 restkey: Optional[str] = 'restkey',
                 ignore_first_line: bool = False) -> Tuple[Sequence[str], List[dict]]:
        """
        Reads the csv file and returns the data as a list of dictionaries.

        :param force_fieldnames: The field names of the csv file, if not provided the first row of
            the csv file will be used as the field names.
        :type force_fieldnames: Optional[List[str]]
        :param restkey: The key used to collect all the non-matching fields. Default is 'restkey'.
        :type restkey: Optional[str]
        :param ignore_first_line: If True, the first line of the csv file will be ignored.
        :type ignore_first_line: bool

        :return: A tuple containing the field names and the data as list of dictionaries.
        :rtype: Tuple[List[str], List[dict]]
        """
        with open(self.path, newline='', encoding='utf-8') as csvfile:
            dialect = csv.Sniffer().sniff(csvfile.read(1024))
            csvfile.seek(0)

            if force_fieldnames and ignore_first_line:
                csvfile.readline()

            reader = csv.DictReader(csvfile,
                                    restkey=restkey,
                                    fieldnames=force_fieldnames,
                                    dialect=dialect)
            fieldnames = reader.fieldnames
            data = [row for row in reader]

        self.data = data
        self.fieldnames = fieldnames
        return fieldnames, data

    def validate(self) -> None:
        """
        Validates the csv file.


        """
        if not self.data:
            raise self.FileContentError('The csv file has not been read yet')
        for row in self.data:
            for field_name in self.fieldnames:
                if field_name not in row:
                    raise self.FileContentError(
                        f'The field {field_name} is missing in the csv file (row: {row})')

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
