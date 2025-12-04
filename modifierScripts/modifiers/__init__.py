import pkgutil
import importlib

__all__ = []
_modules = None

def load_modifiers():
    global _modules
    if _modules is not None:
        return _modules  # already loaded
    print(f"[DEBUG] Loading modifiers...")

    _modules = []
    package_name = __name__  # e.g. "modifierScripts.modifiers"

    for loader, module_name, is_pkg in pkgutil.iter_modules(__path__):
        full_name = f"{package_name}.{module_name}"
        print(f"Loading modifier module: {full_name}")
        module = importlib.import_module(full_name)
        _modules.append(module)
        __all__.append(module_name)

    return _modules
