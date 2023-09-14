from dataclasses import dataclass, asdict
from hashlib import sha256


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
        data['tests'] = [TestResult.parse(item) for item in data['tests']]
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
        data['results'] = [SetResult.parse(item) for item in data['results']]
        return cls(**data)


def create_broker_submit_id(course_name: str, submit_id: int):
    return f'{course_name}___{submit_id}'


def make_hash(password: str, broker_submit_id: str):
    hash_obj = sha256()
    hash_obj.update(password)
    hash_obj.update(broker_submit_id)
    return hash_obj.hexdigest()
