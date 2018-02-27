from tabulate import tabulate
from clint.textui import colored, indent, puts
from custom_data import clear_screen
import pyperclip

jaquar_dict = {}
result = []
with open("jaquar_data.txt") as f:
    for line in f:
        line = line.strip()
        key, val = line.split(":")
        jaquar_dict[key] = val
    # dict[key] = val


def float_check(a):
    try:
        x = float(a)
        # if x < 0: raise ValueError('value must be positive')
    except ValueError as e:
        # print("ValueError: '{}'".format(e))
        print(colored.red("The margin was not changed."))
        # print("Please try entering it again...")
        return "False" # not boolean False, because number 0 also return False
    else:
        return x


def process_value(k, v, result_p, margin_p):
    v = v.strip("[")
    v = v.strip("]")
    v = v.split(",")
    margin_multiplier = 1 + (float(margin_p) / 100)
    margin_5_after_gst = float(v[1]) * margin_multiplier * (1+(float(v[0])/100))
    amount_before_gst = float(v[1])* margin_multiplier
    mrp = round(float(v[2]),2)
    an_item = (k,
               v[0],
               v[1],
               mrp,
               margin_p,
               round(margin_5_after_gst,0),
               round(amount_before_gst,0))
    result_p.append(an_item)
    pyperclip.copy(str(an_item[5]))


def get_new_margin():
    new_margin = input("Enter margin percentage: ").strip()
    try:
        if float_check(new_margin) != "False":
            print("The new profit margin is {}%".format(new_margin))
    except Exception as e:
        print(e)
        print("Default margin 5% will be used")
        new_margin = 5
    return new_margin


def search_jaquar_function(get_user_query, jaquar_margin_p,  **kwargs):

    if "clear_report" in kwargs:
        result[:] = []
        return
    if "quotation" in kwargs:
        pass
    else:
        result[:] = []
    found = ""
    for k,v in jaquar_dict.items():
        k = k + " "
        if ("-" + get_user_query + " ").lower() in k.lower():

            process_value(k, v, result, jaquar_margin_p)
            found = "exact_match"
    if found != "exact_match":
        print("Exact match was not found.")
        for k, v in jaquar_dict.items():
            if get_user_query.lower() in k.lower():

                process_value(k, v, result, jaquar_margin_p)
                # print("\n")
                # print(tabulate([result], headers=headers_list))
                found = "not_exact"

    if found != "not_exact" and found != "exact_match":
        print("No match was found.")
        print("Invalid Code. Please try again.")
        return
        # elif found == "not_exact":
        # print(tabulate([mult_result], headers=headers_list))
    else:
        clear_screen()
        headers_list = ["Item Code", "GST %", "SP", "MRP", "Margin", "SP + GST + Margin", "Amount Before GST"]
        print(tabulate(result,
                       headers=headers_list,
                       floatfmt="0.0f",
                       numalign="right"))
        return result



