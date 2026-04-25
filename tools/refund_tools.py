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
