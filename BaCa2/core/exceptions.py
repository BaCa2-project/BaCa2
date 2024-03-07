class ModelValidationError(Exception):
    pass


class DataError(Exception):
    pass


class NewDBError(Exception):
    pass


class RoutingError(Exception):
    pass

class InvalidTokenError(Exception):
    """Exception raised for invalid tokens."""
    def __init__(self, message='Invalid or expired token'):
        self.message = message
        super().__init__(self.message)
