from tools.registry import load_tools
import re

TOOLS = load_tools()

ACTION_MAP = {
    "get_order_details": "get_order_details",
    "check_refund_status": "check_refund_status",
    "respond_to_user_with_refund_status": "generate_response",
    "generate_response": "generate_response"
}


def resolve_inputs(inputs, context):
    resolved = {}

    for key, value in inputs.items():
        if isinstance(value, str):
            matches = re.findall(r"\{\{step\.\d+\.(.*?)\}\}", value)
            if matches:
                resolved[key] = context.get(matches[0])
            else:
                resolved[key] = value
        else:
            resolved[key] = value

    return resolved


def execute_plan(plan):
    context = {}

    for step in plan["steps"]:
        raw_action = step["action"]

        print(f"\nExecuting: {raw_action}")

        action = ACTION_MAP.get(raw_action)
        if not action:
            raise Exception(f"Unsupported action: {raw_action}")

        tool = TOOLS[action]

        inputs = resolve_inputs(step.get("input", {}), context)

        result = tool(**inputs) if inputs else tool(**context)

        if isinstance(result, dict):
            context.update(result)
        else:
            context["final_response"] = result

    return context
