import csv
from pathlib import Path
from typing import List, Optional, Sequence, Tuple

from django.core.files import File

from .misc import random_id


class BaseFileHandler:
    """
    A class used to handle file operations such as saving and deleting.

    :param path: The directory path where the file will be saved
    :type path: Path
    :param extension: The extension of the file
    :type extension: str
    :raises FileNotFoundError: If the path does not exist or is not a directory
    """

    class FileContextMng:
        """
        A context manager for the file object. It is used to open and close the file as django
        db object.
        """

        def __init__(self, path: Path, mode: str = 'rb'):
            if path is None:
                self.file_obj = None
            else:
                self.file_obj = open(path, mode)
            self.path = path

        def __enter__(self):
            if self.file_obj is None:
                return None
            return File(self.file_obj, name=self.path.name)

        def __exit__(self, exc_type, exc_val, exc_tb):
            if self.file_obj is not None:
                self.file_obj.close()

    class FileContentError(Exception):
        """
        An exception raised when the file content is invalid.
        """
        pass

    def __init__(self, path: Path, extension: str, delete_on_exit: bool = False):
        """
        Initializes the basic file handler.

        :param path: Path to the file or directory
        :type path: Path
        :param extension: The extension of the file
        :type extension: str
        :param delete_on_exit: If True, the file will be deleted when the object is deleted
            (default is False)
        :type delete_on_exit: bool
        """
        self.path = path
        self.extension = extension
        self.saved = False
        self.deleted = False
        self.delete_on_exit = delete_on_exit

    def __del__(self):
        """
        Deletes the file if the delete_on_exit is True and the file has not been deleted yet.
        """
        if self.delete_on_exit and not self.deleted:
            self.delete()

    def delete(self):
        """
        Deletes the file from the file path.
        """
        if not self.saved:
            raise self.FileContentError('The file has not been saved yet')
        if self.deleted:
            raise self.FileContentError('The file has already been deleted')
        self.path.unlink()
        self.deleted = True

    @property
    def file(self) -> FileContextMng:
        """
        :return: A context manager for the file object.
        :rtype: FileContextMng
        """
        return self.FileContextMng(self.path)


class MediaFileHandler(BaseFileHandler):
    """
    Base file handler with auto path validation.
    """

    def __init__(self,
                 path: Path,
                 extension: str,
                 delete_on_exit: bool = False,
                 nullable: bool = False):
        """
        Initializes the media file handler.

        :param path: Path to the file or directory
        :type path: Path
        :param extension: The extension of the file
        :type extension: str
        :param delete_on_exit: If True, the file will be deleted when the object is deleted
            (default is False)
        :type delete_on_exit: bool
        :param nullable: If True, the file path can be None
        :type nullable: bool
        """
        if path is None or not path.exists() or not path.is_file():
            if nullable:
                path = None
            else:
                raise FileNotFoundError('The path does not exist or is not a directory')
        super().__init__(path, extension, delete_on_exit)
        self.saved = True


class UploadedFileHandler(BaseFileHandler):
    """
    A class used to handle uploaded files. It is used to save the file data to the file path,
    and optionally convert it to django db file object.
    """

    def __init__(self, path: Path, extension: str, file_data, delete_on_exit: bool = True) -> None:
        """
        Initializes the file handler, used to save the file data to the file path.

        :param path: Path to the file or directory
        :type path: Path
        :param extension: The extension of the file
        :type extension: str
        :param file_data: The file data to be saved
        :type file_data: django.core.files.uploadedfile.InMemoryUploadedFile
        :param delete_on_exit: If True, the file will be deleted when the object is deleted.
            Default is True.
        :type delete_on_exit: bool
        """
        if not path.exists() or not path.is_dir():
            raise FileNotFoundError('The path does not exist or is not a directory')
        self.file_data = file_data
        super().__init__(path, extension, delete_on_exit)
        self.file_id = random_id()
        self.path = path / f'{self.file_id}.{extension}'

    def save(self):
        """
        Saves the file data to the file path.
        """

        with open(self.path, 'wb+') as file:
            for chunk in self.file_data.chunks():
                file.write(chunk)
        self.saved = True


class CsvFileHandler(UploadedFileHandler):
    def __init__(self, path: Path, file_data, fieldnames: Optional[List[str]] = None):
        super().__init__(path, 'csv', file_data)
        self.fieldnames = fieldnames
        self.data = None

    def read_csv(self,
                 force_fieldnames: Optional[List[str]] = None,
                 restkey: Optional[str] = 'restkey',
                 ignore_first_line: bool = False) -> Tuple[Sequence[str] | None, List[str]]:
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
