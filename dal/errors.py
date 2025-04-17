class IdempotencyError(Exception):
    def __init__(self, data=None, message=None):
        super(IdempotencyError, self).__init__(message)
        self.message = message
        self.data = data


