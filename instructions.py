from os import system

from tabulate import tabulate




def invoice_layout_instructions():
    # system('clear && printf "\e[3J"')
    instruction_tuple = (("vi", "View previous invoices"),
                         ("vl", "View ledger account"),
                         ("b", "Back"))
    print(tabulate(instruction_tuple,
                   headers=['command', 'meaning'],
                   numalign="right"))
    print("\nInstructions:\n1. Type party name to make new invoice")
    print("2. Press Tab key to auto-complete while typing party name")
    print("3. Enter b to go back")
    print("\n")


def ledger_instructions():
    # system('clear && printf "\e[3J"')
    instruction_tuple = (("b", "Back"),)
    print(tabulate(instruction_tuple,
                   headers=['command', 'meaning'],
                   numalign="right"))
    print("\n\n")


def sale_detail_layout_instructions():
    # system('clear && printf "\e[3J"')
    instruction_tuple = (("b", "Back"),
                         ("address", "Enter address details"),
                         # ("vip", "View Invoice Previous"),
                         ("vic", "View Invoice"),
                         # ("vin", "View Invoice Next"),
                         ("del", "Delete Invoice"),
                         ("p", "Print Invoice"),
                         # ("save","Save Invoice to Ledger"),
                         ("etd", "Enter Transport Details"),
                         ("date", "Change Invoice Date"),
                         ("gst <gst number>", "Enter gst number", "gst 27AFVPJ9"),
                         ("number <new invoice no>", "Change invoice no", "number 14 -> change current invoice number to 14"),
                         ("de <Number>", "Delete Invoice Item Number", "de 3 -> delete Invoice item number 3"),
                         ("q <Number> <new qty>", "Change Qty of Invoice Item Number", "q 3 10 -> change qty of invoice item 3 to 10"),
                         ("r <Number> <new rate>", "Change Rate of Invoice Item Number", "r 3 10 -> change rate of invoice item 3 to 10"),
                         ("u <Number> <new unit>", "Change Unit of Invoice Item Number", "u 3 10 -> change unit of invoice item 3 to 10"),
                         ("d <Number> <new discount>", "Change Discount of Invoice Item Number", "d 3 10 -> change discount of invoice item 3 to 10"),
                         ("h <Number> <hsn number>", "Change HSN of Invoice Item Number", "h 3 7307 -> change HSN of invoice item 3 to 7307"),
                         ("igst <Number> <igst rate>", "Change igst rate of Invoice Item Number",   "igst 3 9 -> change igst of invoice item 3 to 9"),
                         ("t <Number> <cgst rate>", "Change cgst rate of Invoice Item Number",   "t 3 9 -> change cgst of invoice item 3 to 9"),
                         )
    print(tabulate(instruction_tuple,
                   headers=['command', 'meaning', 'example'],
                   tablefmt="psql",
                   numalign="right"))
    # print("\nInstructions:\n1. Type product name \n e.g. itemx 10")
    # print("2. Press Tab key to auto-complete while typing product name")
    # print("3. Enter b to go back")




