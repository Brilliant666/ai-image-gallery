class GenError(Exception):
    """A public, sanitized generation failure."""

    def __init__(self, kind, message, status=400):
        super().__init__(message)
        self.kind, self.message, self.status = kind, message, status
