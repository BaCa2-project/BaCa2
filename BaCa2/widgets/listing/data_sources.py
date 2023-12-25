from __future__ import annotations

from abc import ABC, abstractmethod

from main.models import Course
from util.models import model_cls
from util.models_registry import ModelsRegistry


class TableDataSource(ABC):
    @abstractmethod
    def get_url(self) -> str:
        raise NotImplementedError('This method has to be implemented by inheriting classes.')

    @abstractmethod
    def generate_table_widget_name(self) -> str:
        raise NotImplementedError('This method has to be implemented by inheriting classes.')


class ModelDataSource(TableDataSource):
    def __init__(self, model: model_cls) -> None:
        self.model = model

    def get_url(self) -> str:
        return f'/{self.model._meta.app_label}/models/{self.model._meta.model_name}'

    def generate_table_widget_name(self) -> str:
        return f'{self.model._meta.model_name}_table_widget'


class CourseModelDataSource(ModelDataSource):
    def __init__(self, model: model_cls, course: str | int | Course) -> None:
        if not isinstance(course, str):
            course = ModelsRegistry.get_course(course).short_name
        self.course = course
        super().__init__(model)

    def get_url(self) -> str:
        return f'course/{self.course}/models/{self.model._meta.model_name}'
