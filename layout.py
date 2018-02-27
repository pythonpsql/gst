from sys import exit
from os import system
from list_completer import TabCompleter
from tabulate import tabulate
import custom_data
from clint.textui import colored, indent, puts

layout_commands = ['nsi', 'npi', 'vsi', 'vpi']
layout_options = ['Sale Invoice',
                  'Purchase Invoice',
                  'Receipt',
                  'Payment',
                  'Sale Ledger',
                  'Purchase Ledger',
                  'Stock',
                  'Work',
                  'Add Work',
                  'Report',
                  'Add GST Number of Vendor',
                  'GST Report Purchase',
                  'GST Report Sale',
                  'Print Cheque',
                  'Create Jaquar Quotation',
                  'Quit']


def get_layout():
    custom_data.clear_screen()
    new_list = [layout_options[x:x + 1] for x in range(0, len(layout_options), 1)]
    print(tabulate(new_list,
                   showindex=range(1, len(layout_options)+1),
                   headers=['No', 'Layout'],
                   tablefmt="psql"
                   ))
    while True:
        s = list(range(1, len(layout_options)+1))
        s = [str(a) for a in s]
        TabCompleter(s)
        selected_layout = input(colored.blue("Enter a No: ")).strip()
        TabCompleter([])
        try:
            return layout_options[int(selected_layout)-1]
        except Exception as e:
            if selected_layout == 'nsi':

            if selected_layout == "b":
                custom_data.clear_screen()
                print("Exiting stack ...")
                exit()
            print(e)
        continue


