SCHEMA = {
    "type": "function",
    "function": {
        "name": "calculate",
        "description": "Perform basic mathematical calculations (addition, subtraction, multiplication, division).",
        "parameters": {
            "type": "object",
            "properties": {
                "expression": {
                    "type": "string",
                    "description": "The mathematical expression to evaluate (e.g., '12 * 45' or '100 / (5 + 5)'). Only arithmetic operations are supported."
                }
            },
            "required": ["expression"]
        }
    }
}

def handler(expression: str) -> dict:
    try:
        # Safe check to restrict character set to basic numbers and arithmetic operators
        allowed_chars = set("0123456789+-*/(). ")
        if not all(char in allowed_chars for char in expression):
            return {"error": "Invalid characters in expression. Only basic arithmetic is allowed."}
        
        # Evaluate safely without builtins
        result = eval(expression, {"__builtins__": None}, {})
        return {"expression": expression, "result": result}
    except Exception as e:
        return {"error": f"Evaluation error: {str(e)}"}
