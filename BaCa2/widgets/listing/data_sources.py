from __future__ import annotations

from abc import ABC, abstractmethod

from main.models import Course
from util.models import model_cls
from util.models_registry import ModelsRegistry


class TableDataSource(ABC):
    """
    Base abstract class for all objects used to generate the data source url for table widgets
    (table widgets use ajax requests to load their data).

    See also:
        - :class:`TableWidget`
        - :class:`ModelDataSource`
        - :class:`CourseModelDataSource`
    """

    @abstractmethod
    def get_url(self) -> str:
        """
        Returns the url pointing to the data source for the table widget.

        :return: The data source url.
        :rtype: str
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @abstractmethod
    def generate_table_widget_name(self) -> str:
        """
        Generates the name for the table widget (used as the id of the table element).

        :return: The name of the table widget.
        :rtype: str
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @abstractmethod
    def generate_table_widget_title(self) -> str:
        """
        Generates the title for the table widget (can be displayed in the util header above the
        table).

        :return: The title of the table widget.
        :rtype: str
        """
        raise NotImplementedError('This method has to be implemented by inheriting classes.')


class ModelDataSource(TableDataSource):
    """
    Data source for table widgets which display information of 'default' database models.

    See also:
        - :class:`TableWidget`
        - :class:`TableDataSource`
        - :class:`CourseModelDataSource`
    """

    def __init__(self, model: model_cls) -> None:
        """
        :param model: The model class which instances should be used as data source for the table
            widget.
        :type model: Type[Model]
        """
        self.model = model

    def get_url(self) -> str:
        """
        Returns the url pointing to the model view of the model class used to generate the data
        for the table widget.

        :return: The data source url.
        :rtype: str
        """
        return f'/{self.model._meta.app_label}/models/{self.model._meta.model_name}'

    def generate_table_widget_name(self) -> str:
        """
        Generates the name for the table widget based on the model name (used as the id of the
        table element).

        :return: The name of the table widget.
        :rtype: str
        """
        return f'{self.model._meta.model_name}_table_widget'

    def generate_table_widget_title(self) -> str:
        """
        Generates the title for the table widget based on the model name (can be displayed in the
        util header above the table).

        :return: The title of the table widget.
        :rtype: str
        """
        model_plural = self.model._meta.verbose_name_plural
        return model_plural[0].upper() + model_plural[1:]


class CourseModelDataSource(ModelDataSource):
    """
    Data source for table widgets which display information of course database models.

    See also:
        - :class:`TableWidget`
        - :class:`TableDataSource`
        - :class:`ModelDataSource`
    """

    def __init__(self, model: model_cls, course: str | int | Course) -> None:
        """
        :param model: The model class which instances should be used as data source for the table
            widget.
        :type model: Type[Model]
        :param course: The course to which the model instances belong. Can be specified as the
            course short name, the course id or the course object.
        :type course: str | int | Course
        """
        if not isinstance(course, str):
            course = ModelsRegistry.get_course(course).short_name
        self.course = course
        super().__init__(model)

    def get_url(self) -> str:
        """
        Returns the url pointing to the course model view of the model class used to generate the
        data for the table widget.

        :return: The data source url.
        :rtype: str
        """
        return f'course/{self.course}/models/{self.model._meta.model_name}'
