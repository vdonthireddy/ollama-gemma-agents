import importlib
import pkgutil
from pathlib import Path

TOOLS = []
TOOL_REGISTRY = {}

# Automatically discover and load all tool modules in this folder
package_dir = str(Path(__file__).parent)
for _, module_name, _ in pkgutil.iter_modules([package_dir]):
    module = importlib.import_module(f"tools.{module_name}")
    
    # Register the tool if it defines a SCHEMA and a handler
    if hasattr(module, "SCHEMA") and hasattr(module, "handler"):
        TOOLS.append(module.SCHEMA)
        tool_name = module.SCHEMA["function"]["name"]
        TOOL_REGISTRY[tool_name] = module.handler
