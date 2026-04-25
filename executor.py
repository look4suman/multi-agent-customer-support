import re

# ----------------------------
# 1. TOOL IMPLEMENTATIONS
# ----------------------------


def get_order_details(order_id):
    return {
        "order_id": order_id,
        "status": "delivered",
        "refund_requested": True
    }


def check_refund_status(order_id):
    return {
        "order_id": order_id,
        "refund_status": "processing"
    }


def generate_response(order_id=None, refund_status=None, **kwargs):
    return f"Your refund for order {order_id} is currently {refund_status}."


# ----------------------------
# 2. TOOL REGISTRY (STRICT)
# ----------------------------

TOOLS = {
    "get_order_details": get_order_details,
    "check_refund_status": check_refund_status,
    "generate_response": generate_response
}


# ----------------------------
# 3. ACTION MAPPING (SAFE LAYER)
# ----------------------------

ACTION_MAP = {
    "get_order_details": "get_order_details",
    "check_refund_status": "check_refund_status",
    "respond_to_user_with_refund_status": "generate_response",
    "generate_response": "generate_response"
}


# ----------------------------
# 4. INPUT RESOLUTION ({{step.x.y}})
# ----------------------------

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


# ----------------------------
# 5. EXECUTOR ENGINE
# ----------------------------

def execute_plan(plan):
    context = {}

    for step in plan["steps"]:
        raw_action = step["action"]

        print(f"\nExecuting step {step['id']}: {raw_action}")

        # ---- Safe mapping ----
        action = ACTION_MAP.get(raw_action)
        if not action:
            raise Exception(f"Unsupported action: {raw_action}")

        tool = TOOLS[action]

        # ---- Resolve inputs ----
        raw_inputs = step.get("input", {})
        inputs = resolve_inputs(raw_inputs, context)

        print(f"Resolved inputs: {inputs}")

        # ---- Execute ----
        result = tool(**inputs) if inputs else tool(**context)

        print(f"Result: {result}")

        # ---- Update shared context ----
        if isinstance(result, dict):
            context.update(result)
        else:
            context["final_response"] = result

    return context
