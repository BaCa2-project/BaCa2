from random import choice


def random_string(length: int, array):
    return ''.join(choice(array) for _ in range(length))
