class DakkuError(Exception):
    pass

class BadFileSize(DakkuError):
    pass

class UnknownFileFormat(DakkuError):
    pass
