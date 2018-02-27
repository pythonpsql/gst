from list_completer import TabCompleter

from clint.textui import colored, indent, puts

def product_qty_validate2(product_name_qty_p):
    product_name = product_name_qty_p

    while True:
        product_qty = input(colored.blue("Enter qty:")).strip()
        if float_check(product_qty) == "False":
            continue
        else:
            break
    # format_print = "Please try again. The format is: product qty"
    # product_name_qty_p = product_name_qty_p.split(" ")
    # if len(product_name_qty_p) <= 1:
    #     print(format_print)
    #     return None, ""
    # product_qty = product_name_qty_p[-1]
    # if float_check(product_qty) == "False":
    #     print(format_print)
    #     return None, ""
    # product_name = " ".join(product_name_qty_p[:-1]).strip()
    # if product_name == "":
    #     print(format_print)
    #     return None, ""
    return product_name, product_qty


def product_qty_validate(product_name_qty_p):
    format_print = "Please try again. The format is: product qty"
    product_name_qty_p = product_name_qty_p.split(" ")
    if len(product_name_qty_p) <= 1:
        print(format_print)
        return None, ""
    product_qty = product_name_qty_p[-1]
    if float_check(product_qty) == "False":
        print(format_print)
        return None, ""
    product_name = " ".join(product_name_qty_p[:-1]).strip()
    if product_name == "":
        print(format_print)
        return None, ""
    return product_name, product_qty


def float_check(a):
    try:
        x = float(a)
        # if x < 0: raise ValueError('value must be positive')
    except ValueError as e:
        print("ValueError: '{}'".format(e))
        # print("Please try entering it again...")
        return "False" # not boolean False, because number 0 also return False
    else:
        return x


def rate_discount_validate(product_name_p):
    while True:
        try:
            from sys import exit, exc_info
            print("The format is: rate discount")
            TabCompleter([])
            rate_discount_p = (input(colored.blue("Enter the rate and discount: ")).format(product_name_p)).strip()
            if rate_discount_p == "help":
                print("Enter rate and discount:\n e.g. 10 20  where 10 is the rate and 20% is the discount")
                print("Or just enter the rate\n e.g. 10    where discount will be assumed as 0%")
                print("enter 0 if you do not wish to enter the rate and discount")
                continue
            if rate_discount_p.count(" ") == 1:
                rate = rate_discount_p.split(" ")[0]
                if float_check(rate) == "False": continue
                discount = rate_discount_p.split(" ")[1]
                if float_check(discount) == "False": continue
                return rate_discount_p.split(" ")[0], rate_discount_p.split(" ")[1]
            elif rate_discount_p.count(" ") == 0:
                if float_check(rate_discount_p) == "False":
                    continue
                return rate_discount_p, 0
            else:
                print("Please try again. The format is rate discount")
        except KeyboardInterrupt:
            exit("\n<terminated by user>")
        except:
            exc_value = exc_info()[1]
            exc_class = exc_value.__class__.__name__
            print("{} exception: '{}'".format(exc_class, exc_value))
            exit("<fatal error encountered>")

    #   product_qty_validate("sale_sai")
