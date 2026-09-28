ValueError
TypeError
KeyError
IndexError
AttributeError
NameError
FileNotFoundError
ModuleNotFoundError
ZeroDivisionError
Exception
TimeoutError
ConnectionError
PermissionError
RuntimeError
ImportError
OSError

class InvalidDocumentError(Exception):
    pass

try:
    process_document("xyz")

except InvalidDocumentError as e:
    print(f"Error: {e}")