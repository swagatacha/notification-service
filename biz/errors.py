class NotFoundError(Exception):
    def __init__(self, message, errors=None):
        super().__init__(message)
        self.message = message
        self.e = errors
