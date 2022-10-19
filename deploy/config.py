import confuse

c = confuse.Configuration('MyApp', __name__)

def set_config(path: str) -> None:
    c.set_file(path)

def get_metadata() -> dict:
    return c["meta"].get()

def get_storage() -> dict:
    return c["storage"].get()

def get_simulation() -> dict:
    return c["simulation"].get()

def get_spot() -> dict:
    return c["spot"].get()