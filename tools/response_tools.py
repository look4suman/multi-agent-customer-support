def generate_response(order_id=None, refund_status=None, **kwargs):
    return f"Your refund for order {order_id} is currently {refund_status}."
