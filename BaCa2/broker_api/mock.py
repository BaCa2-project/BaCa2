from pathlib import Path
from random import choice, randint, uniform
from typing import Iterable, Tuple

from django.conf import settings

from core.choices import EMPTY_FINAL_STATUSES, HALF_EMPTY_FINAL_STATUSES, ResultStatus
from course.models import Result, Submit, Test
from main.models import Course
from util.models_registry import ModelsRegistry


class BrokerMock:
    MOCK_SRC = settings.BASE_DIR / 'broker_api' / 'mock_src'
    COMPILE_LOGS = MOCK_SRC / 'compile_logs'
    CHECKER_LOGS = MOCK_SRC / 'checker_logs'

    def __init__(self,
                 course: int | Course,
                 submit: int | Submit,
                 generate_results: bool = True,
                 add_logs: bool = True,
                 add_answers: bool = True,
                 available_statuses: Iterable[ResultStatus] = None,
                 range_time_real: Tuple[float, float] = (0, 5),
                 time_cpu_mod_range: Tuple[float, float] = (0.5, 0.9),
                 runtime_memory_range: Tuple[int, int] = (2000, 1e8),
                 **kwargs
                 ):
        self.course = ModelsRegistry.get_course(course)
        self.submit = course.get_submit(submit)
        self.generate_results = generate_results
        self.add_logs = add_logs
        self.add_answers = add_answers
        if not available_statuses:
            available_statuses = [ResultStatus.ANS, ResultStatus.MEM,
                                  ResultStatus.TLE, ResultStatus.OK]
        self.available_statuses = available_statuses
        self.range_time_real = range_time_real
        self.time_cpu_mod_range = time_cpu_mod_range
        self.runtime_memory_range = runtime_memory_range

    @classmethod
    def get_random_log(cls, from_dir: Path) -> str:
        logs = list(from_dir.iterdir())
        log_file = choice(logs)
        with open(log_file, 'r', encoding='utf-8') as file:
            return file.read()

    @property
    def rand_time_real(self):
        return uniform(*self.range_time_real)

    @property
    def rand_time_cpu(self):
        return self.rand_time_real * uniform(*self.time_cpu_mod_range)

    @property
    def rand_runtime_memory(self):
        return randint(*self.runtime_memory_range)

    def generate_fake_test_result(self,
                                  test: Test,
                                  status: ResultStatus,
                                  ) -> Result:
        if status in HALF_EMPTY_FINAL_STATUSES:
            return Result.objects.create_result(
                submit=self.submit,
                test=test,
                status=status,
                time_real=-1,
                time_cpu=-1,
                runtime_memory=-1,
                compile_log=self.get_random_log(self.COMPILE_LOGS) if self.add_logs else None,
            )
        elif status == ResultStatus.ANS:
            return Result.objects.create_result(
                submit=self.submit,
                test=test,
                status=status,
                time_real=self.rand_time_real,
                time_cpu=self.rand_time_cpu,
                runtime_memory=self.rand_runtime_memory,
                answer='wrong answer\nwrong answer\nwrong answer\n' if self.add_answers else None,
            )
        elif status in (ResultStatus.MEM, ResultStatus.TLE):
            return Result.objects.create_result(
                submit=self.submit,
                test=test,
                status=status,
                time_real=self.rand_time_real,
                time_cpu=self.rand_time_cpu,
                runtime_memory=self.rand_runtime_memory,
                compile_log=self.get_random_log(self.COMPILE_LOGS) if self.add_logs else None,
                answer='rand answer\nrand answer\nrand answer\n' if self.add_answers else ''
            )
        elif status == ResultStatus.OK:
            return Result.objects.create_result(
                submit=self.submit,
                test=test,
                status=status,
                time_real=self.rand_time_real,
                time_cpu=self.rand_time_cpu,
                runtime_memory=self.rand_runtime_memory,
                answer='ok answer\nok answer\nok answer\n' if self.add_answers else '',
                checker_log=self.get_random_log(self.CHECKER_LOGS) if self.add_logs else None,
            )
        else:
            raise ValueError(f'Cant generate result from status: {status}')

    def generate_fake_results(self):
        unused_results = [r for r in self.available_statuses]
        for task_set in self.submit.task.sets:
            for test in task_set.tests:
                if unused_results:
                    result = self.generate_fake_test_result(
                        test,
                        choice(unused_results)
                    )
                    unused_results.remove(ResultStatus[result.status])
                else:
                    self.generate_fake_test_result(
                        test,
                        choice(self.available_statuses)
                    )

    def run(self) -> None:
        submit_prestatus = choice(self.available_statuses)
        if submit_prestatus in EMPTY_FINAL_STATUSES:
            self.submit.end_with_error(submit_prestatus, 'mock error')
            return
        new_available_statuses = []
        for status in self.available_statuses:
            if status not in EMPTY_FINAL_STATUSES:
                new_available_statuses.append(status)
        self.available_statuses = new_available_statuses
        if not self.available_statuses:
            self.submit.end_with_error(ResultStatus.INT,
                                       'no results available - cant generate results')
        if self.generate_results:
            self.generate_fake_results()
