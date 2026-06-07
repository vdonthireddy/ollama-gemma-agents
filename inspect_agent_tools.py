#!/usr/bin/env python3
import importlib.util
import sys
import json
import argparse
from pathlib import Path

def inspect_agent_tools(agent_path: str):
    path = Path(agent_path).resolve()
    if not path.exists():
        print(f"Error: File '{agent_path}' not found.", file=sys.stderr)
        sys.exit(1)
        
    module_name = path.stem
    spec = importlib.util.spec_from_file_location(module_name, path)
    if spec is None or spec.loader is None:
        print(f"Error: Could not load module spec for '{agent_path}'.", file=sys.stderr)
        sys.exit(1)
        
    module = importlib.util.module_from_spec(spec)
    
    # Add the target file's parent directory to sys.path to allow internal imports
    sys.path.insert(0, str(path.parent))
    
    try:
        spec.loader.exec_module(module)
    except Exception as e:
        print(f"Error: Failed to execute module '{agent_path}': {e}", file=sys.stderr)
        sys.exit(1)
        
    tools = getattr(module, "TOOLS", None)
    if tools is None:
        print(f"No global 'TOOLS' variable found in '{path.name}'.", file=sys.stderr)
        return
        
    print(json.dumps(tools, indent=2))

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="Inspect an agent module and list all LLM tools it defines."
    )
    parser.add_argument(
        "agent_path", 
        type=str, 
        help="Path to the agent python file (e.g., search_agent.py)"
    )
    
    args = parser.parse_args()
    inspect_agent_tools(args.agent_path)
