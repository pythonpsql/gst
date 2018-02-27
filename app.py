#! /usr/bin/env python
from tabulate import tabulate
from database import Database, CursorFromConnectionFromPool
from product import Product, get_product_name_list
# from layout import get_layout
from list_completer import TabCompleter
from invoice import Invoice
from os import system
import os
from instructions import invoice_layout_instructions, ledger_instructions
from create_ledger import create_sale_ledger
from create_cheque import cheque_print
import custom_data
import calendar
from readline_input import rlinput
from clint.textui import colored, indent, puts
from search_jaquar import search_jaquar_function
from pick import pick
from word_completer import WordCompleter
from prompt_toolkit import prompt
import csv
import json


def show_ledger(transaction_type_p, id_transactor_p):
    # print("transaction_type_p is {}".format(transaction_type_p))
    if transaction_type_p in ["sale", "receipt"]:
        sq = "select " \
             "to_char(date,'DD.MM.YYYY'), " \
             "Round(amount_sale,2), " \
             "Round(amount_receipt,2), " \
             "Round(ts - tr,2), " \
             "id, " \
             "type, " \
             "id_sale_invoice, " \
             "id_receipt, " \
             "id_customer " \
             "from sale_ledger_view where id_customer = %s"
        headers_list = ['No', 'Date', 'Sale', 'Receipt', 'Balance', "", "", "", "", ""]
        sq2 = "select name, place from customer where id = %s"
        # print(sq2)
    if transaction_type_p in ["purchase", "payment"]:
        sq = "select " \
             "to_char(date,'DD.MM.YYYY'), " \
             "Round(amount_purchase,2), " \
             "Round(amount_payment,2), " \
             "Round(ts - tr, 2), " \
             "id, " \
             "type, " \
             "id_purchase_invoice, " \
             "id_payment, " \
             "id_vendor " \
             "from purchase_ledger_view where id_vendor = %s"
        headers_list = ['No', 'Date', 'Purchase', 'Payment', 'Balance', "", "", "", "", ""]
        sq2 = "select name, place from vendor where id = %s"
    try:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (int(id_transactor_p),))
            ledger_info = cursor.fetchall()
        print(tabulate(ledger_info,
                       headers=headers_list,
                       numalign="right",
                       stralign="right",
                       floatfmt="0.2f",
                       tablefmt="psql",
                       showindex=range(1, len(ledger_info) + 1))

              )
        d = {}
        j = 1
        # print(len(ledger_info))
        for a in range(len(ledger_info)):
            # print("a is {}".format(a))
            a = ledger_info[j - 1]
            # print("{}. {} ({}) Rs. {}".format(a[4], a[1], a[2], a[5]))
            d[j] = {}
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq2, (id_transactor_p,))
                some_name_place = cursor.fetchone()
                some_name = some_name_place[0]
                # print("some_name is {}".format(some_name))
                some_place = some_name_place[1]
            d[j]["id"], d[j]["transactor_name"], d[j]["transactor_place"], d[j]["id_transactor"] \
                = a[6], some_name, some_place, a[8]
            j += 1
        print("Enter p to print")
        print("Enter b to go back")
        eno = (input(colored.blue("Enter the number from above list: "))).strip()
        if eno == "b":
            return "Back"
        if eno == "p":
            create_sale_ledger(ledger_info, some_name, some_place)
            return None
        try:
            eno = int(eno)
        except Exception as e:
            print("Exception: ".format(e))
            print("You have typed an invalid number. Enter 'vi' if you want to try again")
        if eno in d:
            Invoice(transaction_type_p,
                    d[eno]["id_transactor"],
                    d[eno]["transactor_name"],
                    d[eno]["transactor_place"],
                    id_invoice=d[eno]["id"]
                    )
    except Exception as e:
        print("Exception in show_ledger is {}".format(e))
        return None


def create_new_transactor(name_place_p, transaction_type_p):
    if transaction_type_p == "sale" or transaction_type_p == "receipt":
        entity = "customer"
        some_query = "insert into customer (name, place, gst) values (%s, %s, %s) returning id"
    elif transaction_type_p == "purchase" or transaction_type_p == "payment":
        entity = "vendor"
        some_query = "insert into vendor (name, place, gst) values (%s, %s, %s) returning id"
    print("Creating new {} ...".format(entity))
    while True:
        if name_place_p:
            if name_place_p.count("(") == 1 and name_place_p.count(")") == 1:
                pass
            elif name_place_p == "b":
                return "error", "", ""
            else:
                place_only_list = get_transactor_place_only_list(transaction_type_p)
                pl_completer = WordCompleter(place_only_list, ignore_case=True, sentence=True)
                new_place = prompt("Enter place: ", completer=pl_completer)
                # new_place = rlinput(colored.blue("Enter place:"), custom_data.custom_city).strip()
                # print("New name must be entered in the format: name (place)")
                # print("{} has assumed as the default place".format(custom_data.custom_city))
                name_place_p = name_place_p + " (" + new_place + ")"
                # name_place_p = name_place_p + " (" + custom_data.custom_city + ")"
            # TabCompleter(['y','n'])
            new_name_confirm = input(
                colored.blue("Do you want to create a new " + entity + " \'" + name_place_p + "\'? (y/n): ")).strip()
            if new_name_confirm == 'y':
                break
            else:
                name_place_p = prompt("Enter party name:", completer=tr_completer).strip()
                if name_place_p == "b":
                    return "error", "", ""

                # name_place_p = input("Enter party name: ").strip()
                if name_place_p in transactor_name_list:
                    return "old_name", name_place_p, ""
                continue
    name_p, place_p = name_place_p.split('(')
    name_p = name_p.strip()
    place_p = place_p.split(')')[0]
    get_gst_number_of_new = input(colored.blue("Enter gst number: ")).strip()
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(some_query, (name_p, place_p, get_gst_number_of_new))
        id_transactor_p = cursor.fetchone()[0]
        print("id of new {} is {}".format(entity, id_transactor_p))

    get_address_first_line = rlinput(colored.blue("Enter address first line: ")).strip()
    get_address_second_line = rlinput(colored.blue("Enter address second line: ")).strip()
    get_address_third_line = rlinput(colored.blue("Enter address third line: ")).strip()
    get_contact_no_one = rlinput(colored.blue("Enter contact number one: ")).strip()
    get_contact_no_two = rlinput(colored.blue("Enter contact number two: ")).strip()
    get_contact_no_three = rlinput(colored.blue("Enter contact number three: ")).strip()
    get_email_address = rlinput(colored.blue("Enter email address: ")).strip()
    if transaction_type == "sale":
        sq = "update customer set (" \
             "address_first_line, " \
             "address_second_line, " \
             "address_third_line, " \
             "contact_no_one, " \
             "contact_no_two, " \
             "contact_no_three, " \
             "email_address" \
             ") = (%s, %s, %s, %s, %s, %s, %s) where id = %s"
    elif transaction_type == "purchase":
        sq = "update vendor set (" \
             "address_first_line, " \
             "address_second_line, " \
             "address_third_line, " \
             "contact_no_one, " \
             "contact_no_two, " \
             "contact_no_three, " \
             "email_address" \
             ") = (%s, %s, %s, %s, %s, %s, %s) where id = %s"

    try:
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq,
                           (get_address_first_line,
                            get_address_second_line,
                            get_address_third_line,
                            get_contact_no_one,
                            get_contact_no_two,
                            get_contact_no_three,
                            get_email_address,
                            id_transactor_p))
    except Exception as e1:
        print(e1)
        print("There was an error in entering address. Please try again")
    return id_transactor_p, name_p, place_p


def get_transactor_name_list(transaction_type_p):
    if transaction_type_p == "sale" or transaction_type_p == "receipt":
        # some_query = "select concat(lower(name), ' (', lower(place), ')') from customer"
        some_query = "select concat((name), ' (', (place), ')') from customer"
    if transaction_type_p == "purchase" or transaction_type == "payment":
        some_query = "select concat((name), ' (', (place), ')') from vendor"
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(some_query)
        t = cursor.fetchall()
        return [element for tupl in t for element in tupl]


def get_transactor_place_only_list(transaction_type_p):
    if transaction_type_p == "sale" or transaction_type_p == "receipt":
        # some_query = "select concat(lower(name), ' (', lower(place), ')') from customer"
        some_query = "select distinct place from customer"
    if transaction_type_p == "purchase" or transaction_type == "payment":
        some_query = "select distinct place from vendor"
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(some_query)
        t = cursor.fetchall()
        return [element for tupl in t for element in tupl]


def separate_name_place(name_place_p):
    name_only = name_place_p.split("(")[0].strip()
    place_only = (name_place_p.split(name_only)[1]).strip()[1:-1]
    return name_only, place_only


def get_id_transactor(name_p, place_p, transaction_type_p):
    if transaction_type_p == "sale" or transaction_type_p == "receipt":
        some_query = "select id from customer where lower(name) = lower(%s) and lower (place) = lower (%s)"
    elif transaction_type_p == "purchase" or transaction_type_p == "payment":
        some_query = "select id from vendor where lower(name) = lower(%s) and lower (place) = lower (%s)"
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(some_query, (name_p, place_p))
        return cursor.fetchone()[0]


def view_sale_ledger(transactor_name_list_p):
    while True:
        tr_completer = WordCompleter(transactor_name_list_p, ignore_case=True, sentence=True)
        # TabCompleter(tr_completer)
        print("Enter b to go back")
        transactor_name_place_p = prompt("Enter party name: ", completer=tr_completer)
        # transactor_name_place_p = input(colored.blue(transaction_type + "_Enter name of party for ledger: ")).strip()
        if transactor_name_place_p in transactor_name_list_p:
            transactor_name_p, transactor_place_p = separate_name_place(transactor_name_place_p)
            id_transactor_p = get_id_transactor(transactor_name_p, transactor_place_p, transaction_type)
            get_ledger_result = show_ledger(transaction_type, id_transactor_p)
            if get_ledger_result == "Back":
                break
        elif transactor_name_place_p == "b":
            break
        else:
            continue


def view_invoices(transaction_type_p):
    if transaction_type_p == "sale":
        sq = "select id, name, place, id_customer, invoice_no, total_amount_after_gst, to_char(date,'DD.MM.YYYY') from sale_invoice order by invoice_no"
    elif transaction_type_p == "purchase":
        sq = "select id, name, place, id_vendor, invoice_no, total_amount_after_gst, to_char(date,'DD.MM.YYYY') from purchase_invoice order by id"
    elif transaction_type_p == "receipt":
        sq = "select id, name, place, id_customer, invoice_no, amount, to_char(date, 'DD.MM.YYYY') from receipt order by invoice_no"
    elif transaction_type_p == "payment":
        sq = "select id, name, place, id_vendor, invoice_no, amount, to_char(date, 'DD.MM.YYYY')  from payment order by invoice_no"
    with CursorFromConnectionFromPool() as cursor:
        cursor.execute(sq)
        t = cursor.fetchall()
        if len(t) != 0:
            print(colored.blue("The previous invoices are: "))
            d = {}
            if transaction_type_p == "purchase":
                headers_list_view = ['No', 'name', 'date', 'amount', 'invoice no']
                a_list = [(el[0], (el[1] + " (" + el[2] + ")"), el[6], el[5], el[4]) for el in t]
            elif transaction_type_p == "sale":
                headers_list_view = ['No', 'name', 'date', 'amount', 'invoice no']
                a_list = [(el[4], (el[1] + " (" + el[2] + ")"), el[6], el[5]) for el in t]
            elif transaction_type_p == "receipt":
                headers_list_view = ['No', 'Name', 'Date', 'Amount']
                a_list = [((el[0]), (str(el[1]) + " (" + str(el[2]) + ")"), str(el[6]), str(el[5])) for el in t]
            elif transaction_type_p == "payment":
                headers_list_view = ['No', 'Name', 'Date', 'Amount']
                a_list = [(str(el[0]), (str(el[1]) + " (" + str(el[2]) + ")"), str(el[6]), str(el[5])) for el in t]
            a_list.append(("0", "back", "", "", ""))
            print(tabulate(a_list,
                           headers=headers_list_view,
                           numalign="right",
                           # stralign="right",
                           # showindex=range(1, len(a_list)+1)
                           tablefmt="psql"
                           )
                  )
            for a in t:
                if transaction_type_p == "purchase":
                    d[a[0]] = {}
                    d[a[0]]["id"], d[a[0]]["transactor_name"], d[a[0]]["transactor_place"], d[a[0]]["id_transactor"] \
                        = a[0], a[1], a[2], a[3]
                else:
                    d[a[4]] = {}
                    # invoice_no
                    d[a[4]]["id"], d[a[4]]["transactor_name"], d[a[4]]["transactor_place"], d[a[4]]["id_transactor"] \
                        = a[0], a[1], a[2], a[3]
                    # id, name, place, id_customer
                    # print(a)
            TabCompleter([])
            eno = (input(colored.blue("Enter No: "))).strip()
            try:
                eno = int(eno)
            except Exception as e:
                print("Exception: ".format(e))
                print("You have typed an invalid number")
            if eno in d:
                Invoice(transaction_type_p,
                        d[eno]["id_transactor"],
                        d[eno]["transactor_name"],
                        d[eno]["transactor_place"],
                        id_invoice=d[eno]["id"]
                        )
        else:
            print("There are no previous records")


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
                  'GST Report Detailed',
                  'Print Cheque',
                  'Create Jaquar Quotation',
                  'Bank Statement',
                  'Backup',
                  'Delete Product',
                  'Delete Vendor',
                  'Delete Customer',
                  'View Unsaved Invoices',
                  'Get GST Return Vendor Data',
                  'Check with Return',
                  'Quit']



def get_layout():
    custom_data.clear_screen()
    answer, choices = pick(layout_options, "Select a layout: ", indicator="->")
    print("You have selected {}".format(answer))
    return answer
    new_list = [layout_options[x:x + 1] for x in range(0, len(layout_options), 1)]
    print(tabulate(new_list,
                   showindex=range(1, len(layout_options) + 1),
                   headers=['No', 'Layout'],
                   tablefmt="psql"
                   ))
    while True:
        s = list(range(1, len(layout_options) + 1))
        s = [str(a) for a in s]
        TabCompleter(s)
        selected_layout = input(colored.blue("Enter a No: ")).strip()
        TabCompleter([])
        try:
            return layout_options[int(selected_layout) - 1]
        except Exception as e:
            if selected_layout == "b":
                custom_data.clear_screen()
                print("Exiting stack ...")
                exit()
            print(e)
        continue


if __name__ == '__main__':
    Database.initialise(database='gst_old', host='localhost', user='dba_tovak', password='j')
    custom_data.clear_screen()
    layout = get_layout()
    while True:
        if layout == 'Sale Invoice':
            custom_data.clear_screen()
            transaction_type = "sale"
            view_object = "Sale Invoice"
            # invoice_layout_instructions()
        elif layout == 'Purchase Invoice':
            custom_data.clear_screen()
            transaction_type = "purchase"
            view_object = "Purchase Invoice"
            # invoice_layout_instructions()
        elif layout == 'Receipt':
            custom_data.clear_screen()
            transaction_type = "receipt"
            view_object = "Receipt Voucher"
        elif layout == 'Payment':
            custom_data.clear_screen()
            transaction_type = "payment"
            view_object = "Payment Voucher"
        elif layout == "Sale Ledger":
            custom_data.clear_screen()
            transaction_type = "sale"
            transactor_name_list = get_transactor_name_list(transaction_type)
            view_sale_ledger(transactor_name_list)
            layout = get_layout()
            continue
        elif layout == "Purchase Ledger":
            custom_data.clear_screen()
            transaction_type = "purchase"
            transactor_name_list = get_transactor_name_list(transaction_type)
            view_sale_ledger(transactor_name_list)
            layout = get_layout()
            continue
        elif layout == "Stock":
            custom_data.clear_screen()
            print("Enter b to go back")
            # TabCompleter(get_product_name_list())

            pn_completer = WordCompleter(get_product_name_list(), ignore_case=True, sentence=True)
            get_product_name = prompt("Enter product name: ", completer=pn_completer).strip()
            # get_product_name = input(colored.blue("Enter Product Name: ")).strip()
            while True:
                if get_product_name.lower() == "b":
                    break
                sq = "select id from product where lower(name) = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (get_product_name.lower(),))
                    the_product_id = cursor.fetchone()
                sq = "select " \
                     "to_char(stock_date,'DD.MM.YYYY'), " \
                     "product_name, " \
                     "qty_purchase, " \
                     "qty_sale, " \
                     "tp-ts " \
                     "from stock_view where id_product = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (the_product_id,))
                    the_result = cursor.fetchall()
                headers_list = ["Date", "Name", "Purchased", "Sold", "Balance"]
                print(tabulate(the_result,
                               headers=headers_list,
                               tablefmt="psql"
                               )
                      )
                get_product_name = input(colored.blue("Enter Product Name: ")).strip()
            layout = get_layout()
            continue
        elif layout == "Work":
            sq = "select id, date, detail from work"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq)
                the_query_result = cursor.fetchall()
            custom_data.clear_screen()
            a_list = [el[1:] for el in (tuple(x) for x in the_query_result)]
            print(tabulate(a_list, tablefmt="psql", showindex=range(1, len(a_list) + 1)))
            go_back = input(colored.blue("Press b to go back:")).strip()
            if go_back == "b":
                layout = get_layout()
                continue
            if go_back.startswith("de"):
                sq = "delete from work where id = %s"
                delete_number = go_back.split("de ")[1]
                print("The delete number is {}".format(delete_number))
                with CursorFromConnectionFromPool() as cursor:
                    # print(the_query_result[int(delete_number)-1][0])
                    confirm_delete = input(colored.blue(
                        "Delete \n'{}'\n   ? (y/n):").format(the_query_result[int(delete_number) - 1][2])).strip()
                    if confirm_delete == "y":
                        cursor.execute(sq, (the_query_result[int(delete_number) - 1][0],))
                    continue
            else:
                continue
        elif layout == "Add Work":
            while True:
                new_work = input(colored.blue("Enter new work: ")).strip()
                if new_work == "b":
                    break
                else:
                    sq = "insert into work (detail) values (%s)"
                    with CursorFromConnectionFromPool() as cursor:
                        cursor.execute(sq, (new_work,))
                    continue
            layout = get_layout()
            continue
            # layout = get_layout()
        elif layout == "Report":
            custom_data.clear_screen()
            print("Enter b to go back")

            preset_sq1 = "select distinct name, tr from sale_balance_view, customer where sale_balance_view.id_customer = customer.id order by name;"
            preset_sq2 = "select sale_invoice.name, sum(total_amount_after_gst) from sale_invoice join customer on customer.id = sale_invoice.id_customer where customer.place = %s group by sale_invoice.name"
            print("Type 'acb' to view all customer balances")
            print("Type 'place' to view place-wise balance")
            with open("queries.txt") as f:
                print("\n")
                print(f.read())
            get_query = input(colored.blue("Enter a query:")).strip()
            while True:
                if get_query.lower() == "b":
                    break
                elif get_query.lower() == "acb":
                    with CursorFromConnectionFromPool() as cursor:
                        cursor.execute(preset_sq1)
                        all_balances_result = cursor.fetchall()
                    print(tabulate(all_balances_result))
                elif get_query.lower() == "place":
                    try:
                        place_sq = "select distinct place from customer"
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(place_sq)
                            t = cursor.fetchall()
                        place_only_list = [element for tupl in t for element in tupl]
                        pl_completer = WordCompleter(place_only_list, ignore_case=True, sentence=True)

                        get_place = prompt("Enter place: ", completer=pl_completer)
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(preset_sq2, (get_place,))
                            place_result = cursor.fetchall()
                        print(tabulate(place_result))
                    except Exception as e:
                        print("its this one")
                        print(e)
                else:
                    try:
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(get_query)
                            the_query_result = cursor.fetchall()
                        with open("queries.txt", "a") as myfile:
                            myfile.write("\n")
                            myfile.write(get_query)
                        custom_data.clear_screen()
                        print(tabulate(the_query_result, tablefmt="psql", floatfmt=".2f"))
                    except Exception as e:
                        print(e)
                get_query = input(colored.blue("Enter a query:")).strip()
            layout = get_layout()
            continue
        elif layout == "Add GST Number of Vendor":
            custom_data.clear_screen()
            print("Enter b to go back")
            transaction_type = "purchase"
            transactor_name_list = get_transactor_name_list(transaction_type)
            # TabCompleter(transactor_name_list)
            tr_completer = WordCompleter(transactor_name_list, ignore_case=True, sentence=True)

            while True:
                # get_query = input(colored.blue("Enter vendor name or s to exit:")).strip()
                get_query = prompt("Enter vendor name or s to exit", completer=tr_completer)
                get_only_name = get_query.split("(")[0].strip()
                print("the name is {}".format(get_only_name))
                if get_query == "s":
                    break
                sq = "select gst from vendor where name = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (get_only_name,))
                    old_gst_number = cursor.fetchone()[0]
                    print(old_gst_number)
                if str(old_gst_number) == "None":
                    if get_query in transactor_name_list:
                        get_gst_number = input(colored.blue("Enter gst number for {}:").format(get_query)).strip()
                        get_gst_number = str(get_gst_number)
                        print(get_gst_number)
                        sq = "update vendor set gst = %s where name = %s"
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(sq, (get_gst_number, get_only_name))
            layout = get_layout()
            continue
        elif layout == "GST Report Detailed":
            starting_date = input(colored.blue("Enter starting date (e.g. 1.7.2017): ")).strip()
            starting_date = starting_date.split(".")
            starting_date = starting_date[2] + "-" + starting_date[1] + "-" + starting_date[0]
            ending_date = input(colored.blue("Enter ending date (e.g. 31.7.2017): ")).strip()
            ending_date = ending_date.split(".")
            ending_date = ending_date[2] + "-" + ending_date[1] + "-" + ending_date[0]
            report_headers = ['GSTIN/UIN of Recipient', 'Invoice Number', 'Invoice date', 'Invoice Value',
                              'Place Of Supply', 'Reverse Charge', 'Invoice Type', 'E-Commerce GSTIN', 'Rate',
                              'Taxable Value', 'Freight', 'Cess Before Freight', 'Cess on Freight', 'Cess Amount']
            report_july_sq = "select " \
                             "customer.gst, " \
                             "sale_invoice.invoice_no, " \
                             "to_char(sale_invoice.date, 'DD/MM/YYYY'), " \
                             "sale_invoice.total_amount_after_gst, " \
                             "'27-Maharashtra', " \
                             "'N', " \
                             "'Regular', " \
                             "'', " \
                             "sale_invoice_detail.product_cgst_rate*2, " \
                             "Round(sum(sale_invoice_detail.amount_after_discount),2)," \
                             "sale_invoice.freight, " \
                             "Round(sum(sale_invoice_detail.cgst_amount + sale_invoice_detail.sgst_amount),2)," \
                             "Round((sale_invoice.freight*sale_invoice_detail.product_cgst_rate*0.02),2)" \
                             "from sale_invoice " \
                             "join sale_invoice_detail on sale_invoice.id = sale_invoice_detail.id_sale_invoice " \
                             "inner join customer on sale_invoice.id_customer = customer.id " \
                             "where date <= %s and date >= %s " \
                             "group by customer.gst, sale_invoice.invoice_no, sale_invoice.date, sale_invoice.total_amount_after_gst, sale_invoice_detail.product_cgst_rate, sale_invoice.amount_before_tax, sale_invoice.freight " \
                             "order by sale_invoice.invoice_no"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(report_july_sq, (ending_date, starting_date))
                report_july = cursor.fetchall()
            print(tabulate(report_july, headers=report_headers))

            # input("skladfjl")
            import csv
            import sys
            b2b_report_name = "b2b_" + starting_date + "_" + ending_date + ".csv"
            with open(b2b_report_name, 'wt') as f:
                try:
                    writer = csv.writer(f)
                    writer.writerow(report_headers)
                    for i in range(len(report_july)):
                        writer.writerow((str(report_july[i][0]),
                                         str(report_july[i][1]),
                                         str(report_july[i][2]),
                                         str(report_july[i][3]),
                                         str(report_july[i][4]),
                                         str(report_july[i][5]),
                                         str(report_july[i][6]),
                                         str(report_july[i][7]),
                                         str(report_july[i][8]),
                                         str(report_july[i][9]),
                                         str(report_july[i][10]),
                                         str(report_july[i][11]),
                                         str(report_july[i][12]),
                                         ))
                    # input("lskajfklajsf")
                    import os

                    if os.name == "nt":
                        os.system('start ' + "july.csv")
                    else:
                        input(" will try to open ")
                        os.system('open ' + "july.csv")
                except Exception as e:
                    print(e)
                    input("saflsafj")
            layout = get_layout()
            continue
        elif layout == "GST Report Purchase":
            try:
                # starting_date = "2017-7-1"
                # ending_date = "2017-7-31"
                starting_date = input(colored.blue("Enter starting date (e.g. 1.7.2017): ")).strip()
                starting_date = starting_date.split(".")
                starting_date = starting_date[2] + "-" + starting_date[1] + "-" + starting_date[0]
                ending_date = input(colored.blue("Enter ending date (e.g. 31.7.2017): ")).strip()
                ending_date = ending_date.split(".")
                ending_date = ending_date[2] + "-" + ending_date[1] + "-" + ending_date[0]
                sq = "select " \
                     "to_char(date, 'DD.MM.YY'), " \
                     "invoice_no, " \
                     "gst, " \
                     "concat(purchase_invoice.name,  ' (', purchase_invoice.place,  ')') as name, " \
                     "Round((amount_before_tax + coalesce(freight,0)),2), " \
                     "cgst9_taxable_amount, " \
                     "sgst9_taxable_amount, " \
                     "igst9_taxable_amount, " \
                     "cgst9_amount, " \
                     "sgst9_amount, " \
                     "Round((igst9_amount*2),2), " \
                     "cgst14_taxable_amount," \
                     "sgst14_taxable_amount, " \
                     "igst14_taxable_amount, " \
                     "cgst14_amount, " \
                     "sgst14_amount, " \
                     "Round((igst14_amount*2),2)," \
                     "Round(total_amount_after_gst,2) " \
                     "from purchase_invoice inner join vendor on vendor.name = purchase_invoice.name " \
                     "where date <= %s and date >= %s " \
                     "order by purchase_invoice.date"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (ending_date, starting_date))
                    transaction_report = cursor.fetchall()
                headers_list = ['Date', 'Invoice No', 'GST IN', 'Name', 'Amount Before Tax',
                                'CGST 9 Taxable Amount', 'SGST 9 Taxable Amount', 'IGST 18 Taxable Amount',
                                'CGST 9 Amount', 'SGST 9 Amount', 'IGST 18 Amount',
                                'CGST 14 Taxable Amount', 'SGST 14 Taxable Amount', 'IGST 28 Taxable Amount',
                                'CGST 14 Amount', 'SGST 14 Amount', 'IGST 28 Amount', 'Total Amount after GST']
                # print(tabulate(purchase_report,
                #                headers=headers_list,
                #                showindex=range(1, len(purchase_report) + 1),
                #                tablefmt="psql"))
                import csv
                import sys

                with open("purchase_report.csv", 'wt') as f:
                    try:
                        writer = csv.writer(f)
                        writer.writerow(headers_list)
                        for i in range(len(transaction_report)):
                            writer.writerow((str(transaction_report[i][0]),
                                             str(transaction_report[i][1]),
                                             str(transaction_report[i][2]),
                                             str(transaction_report[i][3]),
                                             str(transaction_report[i][4]),
                                             str(transaction_report[i][5]),
                                             str(transaction_report[i][6]),
                                             str(transaction_report[i][7]),
                                             str(transaction_report[i][8]),
                                             str(transaction_report[i][9]),
                                             str(transaction_report[i][10]),
                                             str(transaction_report[i][11]),
                                             str(transaction_report[i][12]),
                                             str(transaction_report[i][13]),
                                             str(transaction_report[i][14]),
                                             str(transaction_report[i][15]),
                                             str(transaction_report[i][16]),
                                             str(transaction_report[i][17])
                                             ))
                        import os

                        if os.name == "nt":
                            os.system('start ' + "purchase_report.csv")
                        else:
                            os.system('libreoffice ' + "purchase_report.csv")
                    except Exception as e:
                        print(e)
                sq = "select " \
                     "Round(sum(amount_before_tax+ freight),2)," \
                     "Round((sum(cgst9_amount)+sum(cgst14_amount)),2)," \
                     "Round((sum(sgst9_amount)+sum(sgst14_amount)),2)," \
                     "Round((sum(igst9_amount*2)+sum(igst14_amount*2)),2)," \
                     "Round(sum(total_amount_after_gst),2) " \
                     "from purchase_invoice where date <= %s and date >= %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (ending_date, starting_date))
                    summary_report = cursor.fetchall()
                headers_list = ['Amount Before GST', 'CGST', 'SGST', 'IGST', 'Amount After GST']
                import csv
                import sys

                with open("purchase_report_summary.csv", 'wt') as f:
                    try:
                        writer = csv.writer(f)
                        writer.writerow(headers_list)
                        for i in range(len(summary_report)):
                            writer.writerow((str(summary_report[i][0]),
                                             str(summary_report[i][1]),
                                             str(summary_report[i][2]),
                                             str(summary_report[i][3]),
                                             str(summary_report[i][4])
                                             ))
                            import os

                            if os.name == "nt":
                                os.system('start ' + "purchase_report_summary.csv")
                            else:
                                os.system('libreoffice ' + "purchase_report_summary.csv")
                    except Exception as e:
                        print(e)
                get_response = input(colored.blue("Press b to go back: ")).strip()
                if get_response == "b":
                    layout = get_layout()
                    continue

            except Exception as e:
                print(e)
                get_response = input(colored.blue("Press b to go back: ")).strip()
        elif layout == "GST Report Sale":
            try:
                starting_date = input(colored.blue("Enter starting date (e.g. 1.7.2017): ")).strip()
                starting_date = starting_date.split(".")
                starting_date = starting_date[2] + "-" + starting_date[1] + "-" + starting_date[0]
                ending_date = input(colored.blue("Enter ending date (e.g. 31.7.2017): ")).strip()
                ending_date = ending_date.split(".")
                ending_date = ending_date[2] + "-" + ending_date[1] + "-" + ending_date[0]
                # starting_date = "2017-7-1"
                # ending_date = "2017-7-31"
                # starting_date = input("Enter starting date (e.g. 2017-7-1): ").strip()
                # ending_date = input("Enter ending date (e.g. 2017-7-31): ").strip()
                sq = "select " \
                     "to_char(date, 'DD.MM.YY'), " \
                     "invoice_no, " \
                     "gst, " \
                     "concat(sale_invoice.name,  ' (', sale_invoice.place,  ')') as name, " \
                     "Round(amount_before_tax+ freight,2), " \
                     "Round((cgst9_taxable_amount/2),2), " \
                     "Round((sgst9_taxable_amount/2),2), " \
                     "cgst9_amount, " \
                     "sgst9_amount, " \
                     "Round((cgst14_taxable_amount/2),2), " \
                     "Round((sgst14_taxable_amount/2),2), " \
                     "cgst14_amount, " \
                     "sgst14_amount, " \
                     "total_amount_after_gst " \
                     "from sale_invoice inner join customer on customer.name = sale_invoice.name " \
                     "where date <= %s and date >= %s " \
                     "order by sale_invoice.date, invoice_no"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (ending_date, starting_date))
                    transaction_report = cursor.fetchall()
                headers_list = ['Date',
                                'Invoice No',
                                'GST IN',
                                'Name',
                                'Amount Before Tax',
                                'CGST 9 Taxable Amount',
                                'SGST 9 Taxable Amount',
                                'CGST 9 Amount',
                                'SGST 9 Amount',
                                'CGST 14 Taxable Amount',
                                'SGST 14 Taxable Amount',
                                'CGST 14 Amount',
                                'SGST 14 Amount',
                                'Total Amount After GST'
                                ]
                # print(tabulate(sale_report,
                #                headers=headers_list,
                #                showindex=range(1, len(sale_report) + 1),
                #                tablefmt="psql"))
                import csv
                import sys

                with open("sale_report.csv", 'wt') as f:
                    try:
                        writer = csv.writer(f)
                        writer.writerow(headers_list)
                        for i in range(len(transaction_report)):
                            writer.writerow((str(transaction_report[i][0]),
                                             str(transaction_report[i][1]),
                                             str(transaction_report[i][2]),
                                             str(transaction_report[i][3]),
                                             str(transaction_report[i][4]),
                                             str(transaction_report[i][5]),
                                             str(transaction_report[i][6]),
                                             str(transaction_report[i][7]),
                                             str(transaction_report[i][8]),
                                             str(transaction_report[i][9]),
                                             str(transaction_report[i][10]),
                                             str(transaction_report[i][11]),
                                             str(transaction_report[i][12]),
                                             str(transaction_report[i][13])
                                             ))
                        import os

                        if os.name == "nt":
                            os.system('start ' + "sale_report.csv")
                        else:
                            os.system('libreoffice ' + "sale_report.csv")
                    except Exception as e:
                        print(e)
                sq = "select " \
                     "Round(sum(amount_before_tax+ freight),2)," \
                     "Round((sum(cgst9_amount)+sum(cgst14_amount)),2)," \
                     "Round((sum(sgst9_amount)+sum(sgst14_amount)),2)," \
                     "Round(sum(total_amount_after_gst),2) " \
                     "from sale_invoice where date <= %s and date >= %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (ending_date, starting_date))
                    summary_report = cursor.fetchall()
                headers_list = ['Amount Before GST', 'CGST', 'SGST', 'Amount After GST']
                import csv
                import sys

                with open("sale_report_summary.csv", 'wt') as f:
                    try:
                        writer = csv.writer(f)
                        writer.writerow(headers_list)
                        for i in range(len(summary_report)):
                            writer.writerow((str(summary_report[i][0]),
                                             str(summary_report[i][1]),
                                             str(summary_report[i][2]),
                                             str(summary_report[i][3])
                                             ))
                        import os

                        if os.name == "nt":
                            os.system('start ' + "sale_report_summary.csv")
                        else:
                            os.system('xdg-open ' + "sale_report_summary.csv")
                    except Exception as e:
                        print(e)
                get_response = input(colored.blue("Press b to go back: ")).strip()
                if get_response == "b":
                    layout = get_layout()
                    continue

            except Exception as e:
                print(e)
                get_response = input(colored.blue("Press b to go back: ")).strip()
        elif layout == "Print Cheque":
            payee_list = ['CTS Express Logistics Pvt Ltd',
                          'MMC Logistic Pvt Ltd',
                          'Barque Trans and Logistics Pvt Ltd',
                          'Shree Niwas Roadlines']
            payee_list = [payee_list[x:x + 1] for x in range(0, len(payee_list), 1)]
            print(tabulate(payee_list, showindex=range(1, len(payee_list) + 1)))
            get_payee_name = input(colored.blue("Enter name to be printed on cheque: ")).strip()
            try:
                if int(get_payee_name) in range(1, len(payee_list) + 1):
                    get_payee_name = ''.join(payee_list[int(get_payee_name) - 1])
                else:
                    print("not in pay")
                    pass
            except Exception as e:
                print(e)
            print(get_payee_name)
            get_cheque_amount = input(colored.blue("Enter amount of cheque: ")).strip()
            import datetime

            dt = datetime.datetime.now()
            dt = datetime.date(dt.year, dt.month, dt.day)
            print(dt)
            i = str(dt)
            i = i.split("-")
            i = i[2] + "-" + i[1] + "-" + i[0]
            cheque_date = i
            print(get_cheque_amount)
            cheque_print(get_payee_name, get_cheque_amount, cheque_date)
            layout = get_layout()
            continue
        elif layout == "Create Jaquar Quotation":
            custom_data.clear_screen()

            margin_fixed_variable = input("Margin fixed per item? (y/n): ").strip()
            if margin_fixed_variable == "y":
                jaquar_margin = input("Enter fixed margin percentage: ")
            while True:
                jaquar_number = input(colored.blue("Enter last part of item code of Jaquar or s to exit: ")).strip()
                if margin_fixed_variable != "y" and jaquar_number != "s":
                    jaquar_margin = input("Enter margin percentage: ")
                if jaquar_number != "s":
                    jaquar_quotation_report = search_jaquar_function(jaquar_number, jaquar_margin, quotation="yes")
                else:
                    jaquar_report_confirmation = input("Do you want to save the quotation? (y/n): ").strip()
                    if jaquar_report_confirmation == "y":
                        jaquar_report_name = input("Enter name of the report: ").strip()
                        jaquar_report_headers_list = ["Item Code", "GST %", "MRP", "Including GST Price To You"]
                        with open((jaquar_report_name + ".csv"), 'wt') as f:
                            try:
                                writer = csv.writer(f)
                                writer.writerow(jaquar_report_headers_list)
                                for i in range(len(jaquar_quotation_report)):
                                    writer.writerow((
                                        (str(jaquar_quotation_report[i][0])),
                                        (str(jaquar_quotation_report[i][1])),
                                        (str(jaquar_quotation_report[i][3])),
                                        (str(jaquar_quotation_report[i][5])),
                                    ))
                                jaquar_open_report = input("Do you want to open the report? (y/n): ")
                                if jaquar_open_report == "y":
                                    import os

                                    if os.name == "nt":
                                        os.system('start ' + jaquar_report_name + ".csv")
                                    else:
                                        os.system('open ' + jaquar_report_name + ".csv")
                            except Exception as e:
                                print(e)
                                input("press any key to continue")
                    search_jaquar_function("", "", clear_report="yes")
                    break
            layout = get_layout()
            continue
        elif layout == "Bank Statement":
            break_while_flag = 0
            debit_options = ["Creditor", "Transport", "Bank Expenses", "Drawings", "Loans Paid", "Tax Paid", "Others",
                             "Before GST", "Cheque Returned", "Cash Withdrawn", "Saving"]
            credit_options = ["Debtor", "Bank Interest", "Drawings Reversed", "Others", "Before GST", "Loans Received", "Saving"]
            transport_list = ["MMC", "Barque", "Shree Niwas Roadlines", "Bharat Transline"]
            bank_sq = "select " \
                      "id, " \
                      "date_bank, " \
                      "description, " \
                      "ref_cheque, " \
                      "type_bank, " \
                      "amount, " \
                      "detail, " \
                      "detail_type, " \
                      "detail_note " \
                      "from bank order by id desc"
            bank_headers = ['Id', 'Date', 'Description', 'Ref / Cheque', 'Type', 'Amount', '', '', '']
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(bank_sq, ())
                bank_result = cursor.fetchall()
            while True:
                if break_while_flag == 1:
                    break
                for i in bank_result:
                    if i[6] is None:
                        custom_data.clear_screen()
                        # print(i)
                        i_list = [[str(element) for element in i]]
                        # i_list = [str(element) for tupl in i for element in tupl]
                        print(tabulate(i_list, tablefmt="psql", headers=bank_headers))
                        take_detail = input("Do you want to enter some detail? (y/n): ").strip()
                        if take_detail == "y":
                            if i[4] == "DR":
                                the_detail, choices = pick(debit_options, "Enter type of detail:", indicator="->")
                                if the_detail == "Creditor":
                                    detail_sq = "select concat (name, ' (', place, ')') from vendor"
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(detail_sq, ())
                                        vendor_list = cursor.fetchall()
                                        vendor_list = [element for tupl in vendor_list for element in tupl]
                                    # print(vendor_list)
                                    vendor_completer = WordCompleter(vendor_list, ignore_case=True, sentence=True)
                                    detail = prompt("Enter detail:", completer=vendor_completer).strip()
                                elif the_detail == "Transport":
                                    transport_completer = WordCompleter(transport_list, ignore_case=True, sentence=True)
                                    detail = prompt("Enter detail:", completer=transport_completer).strip()
                                elif the_detail == "Loans Paid":
                                    loan_sq = "select name from loan_person"
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(loan_sq, ())
                                        loan_person_list = cursor.fetchall()
                                    if loan_person_list is None:
                                        detail = input("Enter name of loan person:").strip()
                                    else:
                                        loan_person_list = [element for tupl in loan_person_list for element in tupl]
                                        # print(vendor_list)
                                        loan_person_completer = WordCompleter(loan_person_list, ignore_case=True,
                                                                              sentence=True)
                                        detail = prompt("Enter detail:", completer=loan_person_completer).strip()

                            elif i[4] == "CR":
                                the_detail, choices = pick(credit_options, "Enter type of detail:", indicator="->")
                                detail_sq = "select concat (name, ' (', place, ')') from customer"
                                with CursorFromConnectionFromPool() as cursor:
                                    cursor.execute(detail_sq, ())
                                    customer_list = cursor.fetchall()
                                    customer_list = [element for tupl in customer_list for element in tupl]
                                if the_detail == "Debtor":
                                    # print(vendor_list)
                                    customer_completer = WordCompleter(customer_list, ignore_case=True, sentence=True)
                                    detail = prompt("Enter detail:", completer=customer_completer).strip()
                                if the_detail == "Loans Received":
                                    loan_sq = "select name from loan_person"
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(loan_sq, ())
                                        loan_person_list = cursor.fetchall()
                                    if loan_person_list is None:
                                        detail = input("Enter name of loan person:").strip()
                                    else:
                                        loan_person_list = [element for tupl in loan_person_list for element in tupl]
                                        # print(vendor_list)
                                        loan_person_completer = WordCompleter(loan_person_list, ignore_case=True,
                                                                              sentence=True)
                                        detail = prompt("Enter detail:", completer=loan_person_completer).strip()

                            confirm_entry = input("Are you sure you want to make an entry? (y/n): ").strip()
                            if the_detail in credit_options or the_detail in debit_options and confirm_entry == "y":
                                update_bank_sq = "update bank set (detail, detail_type) = (%s, %s) where id = %s"
                                if the_detail == "Debtor":
                                    customer_name_only = detail.split(" (")[0]
                                    customer_place_only = detail.split(" (")[1]
                                    customer_place_only = customer_place_only.split(")")[0]
                                    print("cn is {}. and cp is {}.".format(customer_name_only, customer_place_only))
                                    get_id_sq = "select id from customer where name = %s and place = %s"
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(get_id_sq, (customer_name_only, customer_place_only))
                                        get_id = cursor.fetchone()[0]
                                    receipt_sq = "insert into receipt (id_customer, name, amount, type, date) values " \
                                                 "(%s, %s, %s, %s, %s) returning id"
                                    rsq = "insert into sale_transaction (id_receipt , date, id_customer, type, amount_receipt) values " \
                                          "(%s, %s, %s, %s, %s) returning id"
                                    rsq2 = "update receipt set id_sale_transaction =  %s where id = %s"
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(receipt_sq, (get_id,
                                                                    customer_name_only + " " + customer_place_only,
                                                                    i[5],
                                                                    "bank",
                                                                    i[1]))
                                        r_id = cursor.fetchone()[0]
                                        print("The receipt id is {}".format(r_id))
                                    print("Creating record in sale_transaction...")
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(rsq, (r_id, i[1], get_id, "receipt", i[5]))
                                        id_st = cursor.fetchone()[0]
                                    print("Updating receipt with sale_transaction.id")
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(rsq2, (id_st, r_id))
                                if the_detail == "Creditor":
                                    vendor_name_only = detail.split(" (")[0]
                                    vendor_place_only = detail.split(" (")[1]
                                    vendor_place_only = vendor_place_only.split(")")[0]
                                    print("vn is {}. and vp is {}.".format(vendor_name_only, vendor_place_only))
                                    get_id_sq = "select id from vendor where name = %s and place = %s"
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(get_id_sq, (vendor_name_only, vendor_place_only))
                                        get_id = cursor.fetchone()[0]
                                    payment_sq = "insert into payment (id_vendor, name, amount, type, date) values " \
                                                 "(%s, %s, %s, %s, %s) returning id"
                                    psq = "insert into purchase_transaction (id_payment , date, id_vendor, type, amount_payment) values " \
                                          "(%s, %s, %s, %s, %s) returning id"
                                    psq2 = "update payment set id_purchase_transaction =  %s where id = %s"
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(payment_sq, (get_id,
                                                                    vendor_name_only + " " + vendor_place_only,
                                                                    i[5],
                                                                    "bank",
                                                                    i[1]))
                                        p_id = cursor.fetchone()[0]
                                        print("The payment id is {}".format(p_id))
                                    print("Creating record in purchase_transaction...")
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(psq, (p_id, i[1], get_id, "payment", i[5]))
                                        id_pt = cursor.fetchone()[0]
                                    print("Updating payment with purchase_transaction.id")
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(psq2, (id_pt, p_id))
                                if the_detail == "Loans Paid" or the_detail == "Loans Received":
                                    if the_detail == "Loans Paid":
                                        type_of_payment = "paid"
                                    else:
                                        type_of_payment = "received"
                                    try:
                                        get_id_sq = "select id from loan_person where name = %s"
                                        with CursorFromConnectionFromPool() as cursor:
                                            cursor.execute(get_id_sq, (detail,))
                                            get_id = cursor.fetchone()[0]
                                    except:
                                        confirm_new_loan = input("This seems to be a new name. Add it? (y/n): ").strip()
                                        if confirm_new_loan == "y":
                                            new_loan_person_sq = "insert into loan_person (name) values (%s) returning id"
                                            with CursorFromConnectionFromPool() as cursor:
                                                cursor.execute(new_loan_person_sq, (detail,))
                                                get_id = cursor.fetchone()[0]
                                        else:
                                            print("Aborting current transaction. No changes were made.")
                                            continue
                                    loan_sq = "insert into loan (date_loan, amount, id_loan_person, type) values (%s, %s, %s, %s)"
                                    with CursorFromConnectionFromPool() as cursor:
                                        cursor.execute(loan_sq,
                                                       (i[1],
                                                        i[5],
                                                        get_id,
                                                        type_of_payment))
                                print("Updating bank statement...")
                                with CursorFromConnectionFromPool() as cursor:
                                    cursor.execute(update_bank_sq, (detail, the_detail, i[0]))
                        elif take_detail == "n":
                            continue
                        else:
                            break_while_flag = 1
                            break
            layout = get_layout()
            continue
        elif layout == "Backup":
            from sys import platform
            import os
            import datetime

            st = str(datetime.datetime.now()).split(".")[0]
            st = st.replace(":", ".")
            st = st.replace(" ", "_")
            print(st)
            project_dir = os.path.dirname(os.path.abspath(__file__))
            # input("Do you want to take a backup?")
            backup_file_name = st + ".backup"
            backup_dir = os.path.join(project_dir, "backups")
            backup_file_name = os.path.join(backup_dir, backup_file_name)
            backup_command = 'PGPASSWORD="j" pg_dump -Fc -U dba_tovak -d gst_old -h localhost > ' + backup_file_name
            if platform == "linux" or platform == "linux2" or platform == "darwin":
                os.system(backup_command)
            input("Backup has been completed successfully. Press any key to continue")
            layout = get_layout()
            continue
        elif layout == "Delete Product":
            while True:
                pn_completer = WordCompleter(get_product_name_list(), ignore_case=True, sentence=True)
                get_product_name = prompt("Enter product name to delete: ", completer=pn_completer).strip()
                if get_product_name.lower() == "b":
                    break
                elif get_product_name.lower() not in [x.lower() for x in get_product_name_list()]:
                    print("This product does not exit. Please try again")
                else:
                    confirm_product_deletion = input(
                        "Are you sure you want to delete the item {}? (y/n)".format(get_product_name))
                    if confirm_product_deletion == "y":
                        product_delete_sq = "delete from product where lower(name) = %s"
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(product_delete_sq, (get_product_name,))
                            if cursor.statusmessage == "DELETE 1":
                                print("The product {} was deleted successfully".format(get_product_name))
                            else:
                                print("Some error has occurred")
            layout = get_layout()
            continue
        elif layout == "Delete Vendor":
            transaction_type = "purchase"
            while True:
                transactor_name_list = get_transactor_name_list(transaction_type)
                pn_completer = WordCompleter(transactor_name_list, ignore_case=True, sentence=True)
                get_name = prompt("Enter name of vendor to delete: ", completer=pn_completer).strip()
                if get_name.lower() == "b":
                    break
                elif get_name.lower() not in [x.lower() for x in transactor_name_list]:
                    print("This vendor does not exit. Please try again")
                else:
                    confirm_name_deletion = input(
                        "Are you sure you want to delete the vendor {}? (y/n)".format(get_name))
                    if confirm_name_deletion == "y":
                        try:
                            name_only, place_only = separate_name_place(get_name)

                            print(name_only + ".")
                            name_delete_sq = "delete from vendor where lower(name) = %s"
                            with CursorFromConnectionFromPool() as cursor:
                                cursor.execute(name_delete_sq, (name_only.lower(),))
                                if cursor.statusmessage == "DELETE 1":
                                    print("The vendor {} was deleted successfully".format(get_name))
                                else:
                                    print("Some error has occurred")
                        except Exception as e:
                            print("Please delete all the invoices of this vendor")
                            print(e)
                            input("Press any key to continue")
            layout = get_layout()
            continue
        elif layout == "Delete Customer":
            transaction_type = "sale"
            while True:
                transactor_name_list = get_transactor_name_list(transaction_type)
                pn_completer = WordCompleter(transactor_name_list, ignore_case=True, sentence=True)
                get_name = prompt("Enter name of customer to delete: ", completer=pn_completer).strip()
                if get_name.lower() == "b":
                    break
                elif get_name.lower() not in [x.lower() for x in transactor_name_list]:
                    print("This customer does not exit. Please try again")
                else:
                    confirm_name_deletion = input(
                        "Are you sure you want to delete the customer {}? (y/n)".format(get_name))
                    if confirm_name_deletion == "y":
                        try:
                            name_only, place_only = separate_name_place(get_name)

                            print(name_only + ".")
                            name_delete_sq = "delete from customer where lower(name) = %s"
                            with CursorFromConnectionFromPool() as cursor:
                                cursor.execute(name_delete_sq, (name_only.lower(),))
                                if cursor.statusmessage == "DELETE 1":
                                    print("The customer {} was deleted successfully".format(get_name))
                                else:
                                    print("Some error has occurred")
                        except Exception as e:
                            print("Please delete all the invoices of this customer")
                            print(e)
                            input("Press any key to continue")
            layout = get_layout()
            continue
        elif layout == "View Unsaved Invoices":
            sale_invoice_nos_sq = "select id from sale_invoice"
            sale_transaction_invoice_nos_sq = "select id_sale_invoice from sale_transaction where type = 'sale'"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sale_invoice_nos_sq, ())
                sale_invoice_nos = cursor.fetchall()
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sale_transaction_invoice_nos_sq, ())
                sale_transaction_invoice_nos = cursor.fetchall()
            sale_invoice_nos = [int(element) for tupl in sale_invoice_nos for element in tupl]
            # print(sale_invoice_nos)
            sale_transaction_invoice_nos = [element for tupl in sale_transaction_invoice_nos for element in tupl]
            # print(sale_transaction_invoice_nos)
            s = set(sale_transaction_invoice_nos)
            temp3 = [x for x in sale_invoice_nos if x not in sale_transaction_invoice_nos]
            # print(tuple(temp3))
            if len(temp3) != 0:
                get_invoice_no_from_id_sq = "select invoice_no from sale_invoice where id in %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(get_invoice_no_from_id_sq, (tuple(temp3),))
                    unsaved = cursor.fetchall()
                # unsaved_sale_invoice_nos = [str(element) for tupl in unsaved for element in tupl]
                print("The following sale invoices have not been saved:")
                print(tabulate(unsaved, headers=["Invoice Nos"], tablefmt="psql"))
            else:
                print("All sale invoices have been saved")

            purchase_invoice_nos_sq = "select id from purchase_invoice"
            purchase_transaction_invoice_nos_sq = "select id_purchase_invoice from purchase_transaction where type = 'purchase'"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(purchase_invoice_nos_sq, ())
                purchase_invoice_nos = cursor.fetchall()
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(purchase_transaction_invoice_nos_sq, ())
                purchase_transaction_invoice_nos = cursor.fetchall()
            purchase_invoice_nos = [int(element) for tupl in purchase_invoice_nos for element in tupl]
            # print(sale_invoice_nos)
            purchase_transaction_invoice_nos = [element for tupl in purchase_transaction_invoice_nos for element in tupl]
            # print(sale_transaction_invoice_nos)
            s = set(purchase_transaction_invoice_nos)
            temp3 = [x for x in purchase_invoice_nos if x not in purchase_transaction_invoice_nos]
            # print(tuple(temp3))
            if len(temp3) != 0:
                get_invoice_no_from_id_sq = "select invoice_no, date, name, id from purchase_invoice where id in %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(get_invoice_no_from_id_sq, (tuple(temp3),))
                    unsaved = cursor.fetchall()
                # unsaved_sale_invoice_nos = [str(element) for tupl in unsaved for element in tupl]
                print("The following purchase invoices have not been saved:")
                print(tabulate(unsaved, headers=["Invoice No", "Date", "Name", "ID"], tablefmt="psql"))
            else:
                print("All purchase invoices have been saved")
            input("press any key to continue")
            layout = get_layout()
            continue
        elif layout == "Check with Return":
            print("1. Constraints: "\
            "If there is " \
            "more than one invoice of the same amount " \
            "on the same date " \
            "of the same vendor " \
            "this script will check only for one of those invoices")

            input("Press [Enter] to continue")
            starting_date = input(colored.blue("Enter starting date (e.g. 1.7.2017): ")).strip()
            starting_date = starting_date.split(".")
            starting_date = starting_date[2] + "-" + starting_date[1] + "-" + starting_date[0]
            ending_date = input(colored.blue("Enter ending date (e.g. 31.7.2017): ")).strip()
            ending_date = ending_date.split(".")
            ending_date = ending_date[2] + "-" + ending_date[1] + "-" + ending_date[0]
            ssq = "select gst, total_amount_after_gst, date from purchase_gst_amount_view " \
                  "where date >= %s and date <= %s"
            ssqr = "select gst, invoice_amount, date from gst_return_vendor " \
                   "where date >= %s and date <= %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(ssq, (starting_date, ending_date))
                ssq = cursor.fetchall()
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(ssqr, (starting_date, ending_date))
                ssqr = cursor.fetchall()
            notInOurRecord = []
            notInReturn = []
            print("Not in our Record: ")
            for a in ssqr:
                if a in ssq:
                    pass
                    # print(a)
                else:
                    print(a)
                    notInOurRecord.append(a)
                    # input("")
            print("Not in Return: ")
            for a in ssq:
                if a in ssqr:
                    pass
                    # print(a)
                else:
                    print(a)
                    notInReturn.append(a)
                    # input("")
            with open ("gstr2a_mismatch.csv", "wt") as f:
                writer = csv.writer(f)
                f.write("Not in Our Record\n")

                # writer.writerow("Not In Our Record")
                for a in notInOurRecord:
                    writer.writerow(a)
                f.write("Not in Return\n")
                for a in notInReturn:
                    writer.writerow(a)

            input("Press [Enter] to exit")
            layout = get_layout()
            continue
        elif layout == "Get GST Return Vendor Data":
            delete_confirm = input("Do you want to clear previous data? (y/n): ").strip().lower()
            if delete_confirm == "y":
                delete_sq = "delete from gst_return_vendor"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(delete_sq,())
                input("Data deleted successfully. Press [Enter] to load new data")
                gstr2a_file = "/Users/python/Dropbox/shop/tax/2017-2018/gst_july/gstr2a_july.json"
                with open(gstr2a_file) as data_file:
                    # json to dict
                    vendor_data = json.load(data_file)

                vendor_data = vendor_data['b2b']
                # print(len(vendor_data))
                vendor_dict = {}
                for some_counter in range(len(vendor_data)):
                    vendor_ctin = vendor_data[some_counter]['ctin']
                    vendor_dict[vendor_ctin] = {}
                    # print(vendor_data[some_counter]['ctin'])
                    # print("The number of invoices are {}".format(len(vendor_data[some_counter]['inv'])))
                    for noi in range(len(vendor_data[some_counter]['inv'])):
                        gst_return_sq = "insert into gst_return_vendor " \
                                        "(gst, " \
                                        "date, " \
                                        "invoice_amount) " \
                                        "values " \
                                        "(%s, " \
                                        "to_date(%s, 'DD.MM.YYYY')," \
                                        "%s)"

                        vendor_dict[vendor_ctin][noi] = {}
                        invoice_value = round(vendor_data[some_counter]['inv'][noi]['val'],0)
                        invoice_date = vendor_data[some_counter]['inv'][noi]['idt']
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(gst_return_sq,
                                           (vendor_ctin,
                                            invoice_date,
                                            invoice_value))

                        vendor_dict[vendor_ctin][noi]['date'] = invoice_date
                        vendor_dict[vendor_ctin][noi]['value'] = invoice_value

            layout = get_layout()
            continue
        elif layout == "Quit":
            custom_data.clear_screen()
            exit()
        elif layout == 'help':
            custom_data.clear_screen()
            layout = get_layout()
            continue

        transaction_options = ["Create New " + view_object, "View Previous " + view_object, "Back"]
        tr, transaction_choice = pick(transaction_options, "What do you want to do?", indicator="->")
        print(transaction_choice)
        transaction_choice = transaction_choice + 1
        # print("     " * 5 + view_object)
        # new_list = [transaction_options[x:x + 1] for x in range(0, len(transaction_options), 1)]
        # print(tabulate(new_list,
        #                headers=['No', 'Option'],
        #                showindex=range(1, len(transaction_options) + 1),
        #                tablefmt="psql"))
        # s = list(range(1, len(transaction_options) + 1))
        # s = [str(a) for a in s]
        # TabCompleter(s)
        # transaction_choice = input(colored.blue("Enter a No: ")).strip()
        # TabCompleter([])

        if transaction_choice == 1:
            custom_data.clear_screen()
            transactor_name_list = get_transactor_name_list(transaction_type)
            # TabCompleter(transactor_name_list)
            tr_completer = WordCompleter(transactor_name_list, ignore_case=True, sentence=True)
            transactor_name_place = prompt("Enter party name:", completer=tr_completer).strip()
            # transactor_name_place = input(colored.blue("Enter party name: ")).strip()
            if transactor_name_place in transactor_name_list:
                transactor_name, transactor_place = separate_name_place(transactor_name_place)
                id_transactor = get_id_transactor(transactor_name, transactor_place, transaction_type)
            else:
                while True:
                    try:
                        id_transactor, transactor_name, transactor_place = create_new_transactor(transactor_name_place,
                                                                                                 transaction_type)
                        if id_transactor == "old_name":
                            # print("yes old name")
                            # input("")
                            transactor_name, transactor_place = separate_name_place(transactor_name)
                            id_transactor = get_id_transactor(transactor_name, transactor_place, transaction_type)
                        break
                    except Exception as e:
                        print(e)
                        # input("")
                        transactor_name_place = prompt("Enter party name:", completer=tr_completer).strip()
                        # transactor_name_place = input(colored.blue(transaction_type + "_Enter party name: ")).strip()
                        continue
                # TabCompleter(transactor_name_list)
                if id_transactor == "error":
                    continue
            if id_transactor != "old_name":
                transactor_name_list = transactor_name_list.append(transactor_name + ' (' + transactor_place + ')')
            invoice = Invoice(transaction_type, id_transactor, transactor_name, transactor_place)
        elif transaction_choice == 2:
            custom_data.clear_screen()
            view_invoices(transaction_type)
            # any number other than invoice_no will go back
            # 0 and b are not
            continue
        elif transaction_choice == 3 or transaction_choice == "b":
            layout = get_layout()
            continue
