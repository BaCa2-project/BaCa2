from django.utils.translation import gettext_lazy as _

from course.models import Result
from widgets.base import Widget


class BriefResultSummary(Widget):

    def __init__(self,
                 set_name: str,
                 test_name: str,
                 result: Result,
                 show_compile_log: bool = True,
                 show_checker_log: bool = False, ):
        name = f'{set_name}_{test_name}'
        super().__init__(name=name)
        self.set_name = set_name
        self.test_name = test_name

        self.result = result
        self.show_compile_log = show_compile_log
        self.show_checker_log = show_checker_log

    def get_result_data(self) -> dict:
        from .code_block import CodeBlock
        result_data = self.result.get_data(add_compile_log=self.show_compile_log,
                                           add_checker_log=self.show_checker_log)
        if result_data['compile_log']:
            compile_log_widget = CodeBlock(
                name=f'{self.set_name}_{self.test_name}_compile_log_widget',
                code=result_data['compile_log'],
                language='log',
                title=_('Compile log'),
                show_line_numbers=False
            )
            result_data['compile_log_widget'] = compile_log_widget.get_context()
        if result_data['checker_log']:
            checker_log_widget = CodeBlock(
                name=f'{self.set_name}_{self.test_name}_checker_log_widget',
                code=result_data['checker_log'],
                language='log',
                title=_('Checker log'),
                show_line_numbers=False
            )
            result_data['checker_log_widget'] = checker_log_widget.get_context()
        return result_data

    def get_context(self) -> dict:
        return super().get_context() | {
            'set_name': self.set_name,
            'test_name': self.test_name,
            'result': self.get_result_data(),
            'time_prompt': _('Time used'),
            'memory_prompt': _('Memory used'),
        }
