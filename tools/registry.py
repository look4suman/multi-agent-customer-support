from tools import refund_tools, response_tools


def load_tools():
    return {
        "get_order_details": refund_tools.get_order_details,
        "check_refund_status": refund_tools.check_refund_status,
        "generate_response": response_tools.generate_response
    }
