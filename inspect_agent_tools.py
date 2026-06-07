#!/usr/bin/env python3
import sys
import json
import importlib.util

if len(sys.argv) < 2:
    print("Usage: python3 inspect_agent_tools.py <agent_path>")
    sys.exit(1)

# Dynamically load the agent python module
spec = importlib.util.spec_from_file_location("agent_module", sys.argv[1])
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)

# Output the defined TOOLS in JSON format
if hasattr(module, "TOOLS"):
    print(json.dumps(module.TOOLS, indent=2))
else:
    print(f"No 'TOOLS' variable defined in {sys.argv[1]}")
