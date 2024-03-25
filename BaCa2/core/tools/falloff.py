from abc import ABC, abstractmethod
from datetime import datetime

from core.choices import FallOffPolicy


class FallOff(ABC):
    """
    Abstract base class for different types of fall-off policies.

    :param start: The start time of the policy
    :type start: datetime
    :param deadline: The deadline time of the policy
    :type deadline: datetime
    :param end: The end time of the policy, defaults to None
    :type end: datetime, optional
    """

    def __init__(self,
                 start: datetime,
                 deadline: datetime,
                 end: datetime = None):
        self.start = start
        self.deadline = deadline
        if end is None:
            end = deadline
        self.end = end

    def is_in_deadline(self, when: datetime) -> bool:
        """
        Checks if a given time is within the start and deadline of the policy.

        :param when: The time to check
        :type when: datetime
        :return: True if the time is within the start and deadline, False otherwise
        :rtype: bool
        """
        return self.start <= when <= self.deadline

    def is_in_end(self, when: datetime) -> bool:
        """
        Checks if a given time is within the start and end of the policy.

        :param when: The time to check
        :type when: datetime
        :return: True if the time is within the deadline and end, False otherwise
        :rtype: bool
        """
        return self.start <= when <= self.end

    @classmethod
    def __class_getitem__(cls, item: FallOffPolicy):
        """
        Returns the appropriate FallOff subclass based on the given policy.

        :param item: The policy to check
        :type item: FallOffPolicy
        :return: The appropriate FallOff subclass
        :rtype: type
        :raises ValueError: If the policy is not recognized
        """
        if item == FallOffPolicy.NONE:
            return NoFallOff
        if item == FallOffPolicy.LINEAR:
            return LinearFallOff
        if item == FallOffPolicy.SQUARE:
            return SquareFallOff
        raise ValueError(f'Unknown fall-off policy: {item}')

    @abstractmethod
    def get_factor(self, when: datetime) -> float:
        """
        Abstract method to get the factor at a given time.

        :param when: The time to get the factor for
        :type when: datetime
        :return: The factor at the given time
        :rtype: float
        """
        pass


class NoFallOff(FallOff):
    """
    Class representing a fall-off policy with no fall-off.

    This class is used to define a fall-off policy with no fall-off. The `get_factor` method always
    returns 1.0 if the given time is within the deadline, and 0.0 otherwise.
    """

    def get_factor(self, when: datetime) -> float:
        """
        Gets the factor at a given time for a NoFallOff policy.

        :param when: The time to get the factor for
        :type when: datetime
        :return: The factor at the given time, 1.0 if within the deadline, 0.0 otherwise
        :rtype: float
        """
        if self.is_in_deadline(when):
            return 1.0
        return 0.0


class LinearFallOff(FallOff):
    """
    Class representing a fall-off policy with linear fall-off.
    """

    def get_factor(self, when: datetime) -> float:
        """
        Gets the factor at a given time for a LinearFallOff policy.

        :param when: The time to get the factor for
        :type when: datetime
        :return: The factor at the given time, 1.0 if within the end, 0.0 otherwise
        :rtype: float
        """
        if self.is_in_end(when):
            return 1.0
        if self.is_in_deadline(when):
            return 1.0 - (when - self.end).total_seconds() / (
                self.deadline - self.end).total_seconds()
        return 0.0


class SquareFallOff(FallOff):
    """
    Class representing a fall-off policy with square fall-off.
    """

    def evaluate_quadratic_formula(self, when: datetime) -> float:
        """
        Evaluates the quadratic formula at a given time.

        This method is used to calculate the factor for the SquareFallOff policy.
        The quadratic formula used is: a * when^2 + b * when + c, where:

        - a = -1 / ((self.deadline.timestamp() - self.end.timestamp()) ** 2)
        - b = -2 * a * self.end.timestamp()
        - c = a * self.end.timestamp() ** 2 + 1

        :param when: The time to evaluate the quadratic formula at
        :type when: datetime
        :return: The evaluated value of the quadratic formula at the given time
        :rtype: float
        """
        a = -1 / ((self.deadline.timestamp() - self.end.timestamp()) ** 2)
        b = -2 * a * self.end.timestamp()
        c = a * self.end.timestamp() ** 2 + 1

        return a * when.timestamp() ** 2 + b * when.timestamp() + c

    def get_factor(self, when: datetime) -> float:
        """
        Gets the factor at a given time for a SquareFallOff policy.

        :param when: The time to get the factor for
        :type when: datetime
        :return:
        :rtype: float
        """
        if self.is_in_end(when):
            return 1.0
        if self.is_in_deadline(when):
            return self.evaluate_quadratic_formula(when)
        return 0.0
