from decimal import Decimal, ROUND_HALF_UP
# rate_p = 5.676
# discount_p = 10.5

def get_rate_after_discount(rate_p, discount_p):
    discount_amount = (Decimal(rate_p) * Decimal(discount_p) / Decimal(100))
    discount_amount = Decimal(discount_amount).quantize(Decimal("1.00"))
    net_rate = Decimal(rate_p) - discount_amount
    net_rate = Decimal(net_rate).quantize(Decimal("1.00"), ROUND_HALF_UP)
    return net_rate


def get_amount_after_discount(net_rate_p, qty_p):
    amount_after_discount = (Decimal(net_rate_p) * Decimal(qty_p))
    amount_after_discount = Decimal(amount_after_discount).quantize(Decimal("1.00"))
    return amount_after_discount


def get_cgst(amount_after_discount_p, cgst_p):
    if cgst_p is not None:
        cgst_amount = (Decimal(amount_after_discount_p) * Decimal(cgst_p) / Decimal(100))
        cgst_amount = Decimal(cgst_amount).quantize(Decimal("1.00"), ROUND_HALF_UP)
    else:
        cgst_amount = 0
    return cgst_amount
# print(get_amount_after_discount(5.067, 10.560))