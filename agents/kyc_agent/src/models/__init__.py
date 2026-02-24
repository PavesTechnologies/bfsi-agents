import importlib
import pathlib

package_dir = pathlib.Path(__file__).resolve().parent

for file in package_dir.glob("*.py"):
    if file.name == "__init__.py":
        continue

    module_name = file.stem

    print(f"Loading model module: {module_name}")  # debug

    importlib.import_module(f"{__package__}.{module_name}")
