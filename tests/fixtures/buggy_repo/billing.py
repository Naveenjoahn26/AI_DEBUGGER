"""
Billing module — contains an intentional type bug in calculate_total.

Bug: price and quantity should be multiplied, but they are added instead.
Additionally, quantity is expected to be int but no type coercion is applied,
so passing a string quantity causes: TypeError: unsupported operand type(s) for +: 'int' and 'str'
"""


def calculate_total(price, quantity):
    return price + quantity  # Bug: should be price * quantity, and quantity is not cast to int


def apply_discount(total, discount_percent):
    if discount_percent < 0 or discount_percent > 100:
        raise ValueError("Discount must be between 0 and 100")
    return total * (1 - discount_percent / 100)


def generate_invoice(customer_name, items):
    lines = []
    for item in items:
        line_total = calculate_total(item["price"], item["quantity"])
        lines.append(f"{customer_name}: {item['name']} x{item['quantity']} = {line_total}")
    return "\n".join(lines)
