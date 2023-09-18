from dataclasses import dataclass, asdict
from hashlib import sha256
import re

# TODO: get rid of this file


@dataclass
class BacaToBroker:
    pass_hash: str
    submit_id: str
    package_path: str
    commit_id: str
    submit_path: str

    def serialize(self):
        return asdict(self)

    @classmethod
    def parse(cls, data: dict):
        return cls(**data)


@dataclass
class TestResult:
    name: str
    status: str
    time_real: float
    time_cpu: float
    runtime_memory: int

    def serialize(self):
        return asdict(self)

    @classmethod
    def parse(cls, data: dict):
        return cls(**data)


@dataclass
class SetResult:
    name: str
    tests: dict[str, TestResult]

    def serialize(self):
        return asdict(self)

    @classmethod
    def parse(cls, data_: dict):
        data = data_.copy()
        data['tests'] = {key: TestResult.parse(val) for key, val in data['tests'].items()}
        return cls(**data)


@dataclass
class BrokerToBaca:
    pass_hash: str
    submit_id: str
    results: dict[str, SetResult]

    def serialize(self):
        return asdict(self)

    @classmethod
    def parse(cls, data_: dict):
        data = data_.copy()
        data['results'] = {key: SetResult.parse(val) for key, val in data['results'].items()}
        return cls(**data)


def create_broker_submit_id(course_name: str, submit_id: int) -> str:
    return f'{course_name}___{submit_id}'


def split_broker_submit_id(broker_submit_id: str) -> (str, int):
    r = re.compile(r'(\w+?)___([0-9]+)')
    m = re.fullmatch(r, broker_submit_id)
    course_name = m.group(1)
    submit_id = int(m.group(2))
    return course_name, submit_id


def make_hash(password: str, broker_submit_id: str) -> str:
    hash_obj = sha256()
    hash_obj.update((password + '___').encode('utf-8'))
    hash_obj.update(broker_submit_id.encode('utf-8'))
    return hash_obj.hexdigest()
