from database import CursorFromConnectionFromPool
from list_completer import TabCompleter
from input_validation import product_qty_validate, product_qty_validate2, rate_discount_validate, float_check
from calculations import get_rate_after_discount, get_amount_after_discount, get_cgst
from create_report import create_sale_invoice_detail_csv
from tabulate import tabulate
from product import Product, get_product_name_list
from os import system
from decimal import Decimal
from instructions import sale_detail_layout_instructions
import custom_data
from readline_input import rlinput
from clint.textui import colored, indent, puts
from search_jaquar import search_jaquar_function

from prompt_toolkit import prompt
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from word_completer import WordCompleter
# from prompt_toolkit.contrib.completers import WordCompleter
error_list = ["Invalid customer name", "Declined new customer name", "No customer name",
              "Declined new product name", "Invalid product name"]


#   TODO: honour case of new items when saving them in the db
#   TODO: insert timestamp when saving rates, then allow multiple rate saves
#   TODO: Bug -- vin and vip must be re-written completely

class Invoice:
    def __init__(self, transaction_type, id_transactor, transactor_name, transactor_place, **kwargs):
        # system('clear && printf "\e[3J"')
        self.debug = 0
        self.show_invoice_flag = 0
        self.transaction_type = transaction_type
        self.id_transactor = id_transactor
        self.transactor_name = transactor_name
        self.transactor_place = transactor_place
        if self.transaction_type == "purchase" or self.transaction_type == "sale":
            self.gst_type = self.get_gst_type()
        if self.transaction_type == "purchase":
            if self.gst_type is None:
                ask_gst_type = input(colored.blue("Enter gst type (i/c)")).lower()
                sq = "update vendor set gst_type = %s where id = %s"
                if ask_gst_type == "i":
                    with CursorFromConnectionFromPool() as cursor:
                        cursor.execute(sq, ("igst", self.id_transactor))
                    self.gst_type = "igst"
                elif ask_gst_type == "c":
                    with CursorFromConnectionFromPool() as cursor:
                        cursor.execute(sq, ("cgst", self.id_transactor))
                    self.gst_type = "cgst"
        self.product_name_list = get_product_name_list()
        self.total_afd = 0
        self.total_igst2_5 = 0
        self.total_igst6 = 0
        self.total_igst9 = 0
        self.total_igst14 = 0
        self.total_cgst2_5 = 0
        self.total_cgst6 = 0
        self.total_cgst9 = 0
        self.total_cgst14 = 0
        self.taxable_total_igst2_5 = 0
        self.taxable_total_igst6 = 0
        self.taxable_total_igst9 = 0
        self.taxable_total_igst14 = 0
        self.taxable_total_cgst2_5 = 0
        self.taxable_total_cgst6 = 0
        self.taxable_total_cgst9 = 0
        self.taxable_total_cgst14 = 0
        self.freight = 0
        self.ask_freight_gst = 0
        self.total_amount_after_gst = 0
        self.invoice_no = 0
        self.already_deleted = 0
        if 'id_invoice' in kwargs:
            self.id_invoice = kwargs['id_invoice']
            # print(self.id_invoice)
            # input("")
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            if self.transaction_type in ["purchase", "sale"]:
                self.invoice_no = self.invoice_info[0][4]
                # self.save_transaction()
                # return

                TabCompleter(self.product_name_list)
            self.get_details()
        else:
            self.id_invoice = self.create_invoice()
            if self.transaction_type == "purchase":
                try:
                    print("The format for entering date is dd.mm.yy")
                    print("e.g. 5.12.17 for 5th December 2017")
                    new_date = input(colored.blue("Enter the date: "))
                    self.update_date(new_date)
                except Exception as e:
                    print(e)
                    print("Deleting current invoice...")
                    self.delete_invoice()
                    return
                new_number = input(colored.blue("Enter invoice number: ")).strip()
                sq = "update purchase_invoice set (invoice_no) = (%s) where id = %s"
                try:
                    with CursorFromConnectionFromPool() as cursor:
                        cursor.execute(sq, (new_number, self.id_invoice))
                except Exception as e:
                    print(e)
                    print("Deleting current invoice...")
                    self.delete_invoice()
                    return
            if self.transaction_type == "receipt":
                self.save_transaction()
                return
            if self.transaction_type == "payment":
                self.save_transaction()
                return
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            TabCompleter(self.product_name_list)
            self.get_details()
        if self.transaction_type == "sale" or self.transaction_type == "purchase":
            if not self.invoice_detail_info and self.already_deleted == 0:
                del_confirm = input(colored.red("Invoice seems empty, do you want to delete it? (y/n): ")).strip()
                if del_confirm.lower() == "y":
                    self.delete_invoice()
                    print("Invoice {} has been deleted".format(self.invoice_no))

    def set_next_invoice_no(self):
        if self.transaction_type == "sale":
            last_invoice_no_sq = "select invoice_no from sale_invoice order by invoice_no desc limit 1"
        elif self.transaction_type == "purchase":
            last_invoice_no_sq = "select invoice_no from purchase_invoice order by invoice_no desc limit 1"
        elif self.transaction_type == "receipt":
            last_invoice_no_sq = "select invoice_no from receipt order by invoice_no desc limit 1"
        elif self.transaction_type == "payment":
            last_invoice_no_sq = "select invoice_no from payment order by invoice_no desc limit 1"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(last_invoice_no_sq, ())
            last_invoice_no = cursor.fetchone()
            # print(last_invoice_no)
        if last_invoice_no is None:
            self.invoice_no = 1
        else:
            self.invoice_no = int(last_invoice_no[0]) + 1
            print("current_invoice_no is {}".format(self.invoice_no))

    def create_invoice(self):

        if self.transaction_type == "sale":
            self.set_next_invoice_no()
            some_query = "insert into sale_invoice (id_customer, name, place, invoice_no) " \
                         "values (%s, %s, %s, %s) returning id"
        elif self.transaction_type == "purchase":
            some_query = "insert into purchase_invoice (id_vendor, name, place, invoice_no) " \
                         "values (%s, %s, %s, %s) returning id"
        elif self.transaction_type == "receipt":
            self.set_next_invoice_no()
            receipt_amount = input(colored.blue("Enter the amount received: ")).strip()
            receipt_type = input(colored.blue("Enter the type of receipt: ")).strip()
            receipt_detail = input(colored.blue("Enter any additional detail: ")).strip()
            some_query = "insert into receipt (id_customer, name, place, amount, type, detail, invoice_no) " \
                         "values (%s, %s, %s, %s, %s, %s, %s) returning id"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(some_query, (
                    self.id_transactor, self.transactor_name, self.transactor_place, receipt_amount, receipt_type,
                    receipt_detail, self.invoice_no))
                return cursor.fetchone()[0]
        elif self.transaction_type == "payment":
            self.set_next_invoice_no()
            receipt_amount = input(colored.blue("Enter the amount paid: ")).strip()
            receipt_type = input(colored.blue("Enter the type of payment: ")).strip()
            receipt_detail = input(colored.blue("Enter any additional detail: ")).strip()
            with CursorFromConnectionFromPool() as cursor:
                some_query = "insert into payment (id_vendor, name, place, amount, type, detail, invoice_no) " \
                             "values (%s, %s, %s, %s, %s, %s, %s) returning id"
                cursor.execute(some_query, (
                    self.id_transactor, self.transactor_name, self.transactor_place, receipt_amount, receipt_type,
                    receipt_detail, self.invoice_no))
                return cursor.fetchone()[0]
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(some_query,
                           (self.id_transactor, self.transactor_name, self.transactor_place, self.invoice_no))
        return cursor.fetchone()[0]

    def view_invoice(self):
        # custom_data.clear_screen()
        if self.transaction_type == "sale":
            custom_data.clear_screen()
            print("\n\t\t\t Sale Invoice:  {} ({})".format(self.transactor_name, self.transactor_place))
            # print("Invoice No: {}".format(self.invoice_no))
            print(tabulate([
                [str(self.invoice_no),
                reverse_date(str(self.invoice_info[0][0]))]
                            ],
                            headers=['Invoice No', 'Date'],
                            tablefmt="psql"))
            # print("Date: {}".format(reverse_date(str(self.invoice_info[0][0]))))
        elif self.transaction_type == "purchase":
            custom_data.clear_screen()
            print("\n\t\t\t Purchase Invoice:  {} ({})".format(self.transactor_name, self.transactor_place))
            print(tabulate([
                [str(self.invoice_no),
                 reverse_date(str(self.invoice_info[0][0]))]
            ],
                headers=['Invoice No', 'Date'],
                tablefmt="psql"))
        elif self.transaction_type == "receipt":
            custom_data.clear_screen()
            print("\n\t\t\t Receipt:  {} ({})".format(self.transactor_name, self.transactor_place))
        elif self.transaction_type == "payment":
            custom_data.clear_screen()
            print("\n\t\t\t Payment:  {} ({})".format(self.transactor_name, self.transactor_place))
        self.view_invoice_detail()
        if self.transaction_type == "sale" or self.transaction_type == "purchase":
            if self.invoice_info[0][1] is not None:
                print("\nTransport: {} - {} - {}".format(self.invoice_info[0][1],
                                                         self.invoice_info[0][2],
                                                         self.invoice_info[0][3]))
            headers_footer = ['Amount Before Tax', 'Total GST', 'Amount After Tax']
            # print("Amount Before Tax: {}".format(self.total_afd))
            if self.transaction_type == "sale":
                self.update_invoice_total()
            elif self.transaction_type == "purchase":
                pass
                # self.update_invoice_total()
                # self.update_invoice_total(freight=self.ask_freight_gst)
            # print("Total GST: {}".format(self.total_amount_after_gst-self.total_afd))
            # print("Amount After Tax: {}\n".format(self.total_amount_after_gst))
            print(tabulate([[str(self.total_afd),
                            str(self.total_amount_after_gst-self.total_afd),
                            str(self.total_amount_after_gst)]],
                           headers=headers_footer,
                           tablefmt="psql"))
    def get_details(self):
        if self.transaction_type == "sale" or self.transaction_type == "purchase":
            self.show_invoice_flag = 0
            while True:

                product_name, product_qty = self.get_product_name_qty()


                if product_name is None:
                    break
                if product_name == "change invoice":
                    self.id_invoice = product_qty[0]
                    self.transactor_name = product_qty[1]
                    self.transactor_place = product_qty[2]
                    self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                    continue
                if product_name == "continue":
                    continue
                id_product = Product.get_product_id(product_name)
                if id_product is None:
                    id_product, product_name = Product.create_new_product(product_name)
                    TabCompleter(self.product_name_list)
                    if product_name is not None:
                        self.product_name_list.append(product_name)
                if id_product not in error_list:
                    product_rate, product_discount = self.get_rate_discount(id_product)
                    if product_rate is None and product_discount is None:
                        TabCompleter([])
                        product_rate, product_discount = rate_discount_validate(product_name)
                        TabCompleter(self.product_name_list)
                        if product_rate is not None:
                            self.update_rate_discount(id_product, product_rate, product_discount)
                    if product_discount is None:
                        product_discount = 0
                    if self.transaction_type == "sale":
                        with CursorFromConnectionFromPool() as cursor:
                            sq = "select date from sale_invoice where id = %s"
                            cursor.execute(sq, (self.id_invoice,))
                            invoice_date = cursor.fetchone()
                    if self.transaction_type == "purchase":
                        with CursorFromConnectionFromPool() as cursor:
                            sq = "select date from purchase_invoice where id = %s"
                            cursor.execute(sq, (self.id_invoice,))
                            invoice_date = cursor.fetchone()
                    self.create_invoice_detail(id_product, product_qty, product_rate, product_discount, invoice_date)
                    self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                    # self.view_invoice()
                else:
                    continue
        elif self.transaction_type in ["receipt", "payment"]:
            print("1. Change Amount")
            print("2. Change Date")
            print("3. Delete")
            user_choice = input(colored.blue("Choose a number: ")).strip()
            if self.transaction_type == "receipt":
                amount_change_query = "update receipt set amount = %s where id = %s"
                transaction_query = "update sale_transaction set amount_receipt = %s where id_receipt = %s"
                delete_query = "delete from receipt where id = %s"
            elif self.transaction_type == "payment":
                amount_change_query = "update payment set amount = %s where id = %s"
                transaction_query = "update purchase_transaction set amount_payment = %s where id_payment = %s"
                delete_query = "delete from payment where id = %s"
            if user_choice == "1":
                while True:
                    new_amount = input(colored.blue("Enter the new amount:")).strip()
                    if float_check(new_amount) != "False":
                        break
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(amount_change_query, (new_amount , self.id_invoice))
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(transaction_query, (new_amount, self.id_invoice))
                print("Amount has been changed")
            elif user_choice == "2":
                try:
                    print("The format for entering date is dd.mm.yy")
                    print("e.g. 5.12.17 for 5th December 2017")
                    new_date = input(colored.blue("Enter the date: ")).strip()
                    self.update_date(new_date)
                    # return "continue", ""
                except Exception as e:
                    print(e)
                    # return "continue", ""
            elif user_choice == "3": # Delete
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(delete_query, (self.id_invoice,))
                print("Deleted")


    def change_rate(self, serial_no_p, new_rate):
        serial_no_p = int(serial_no_p) - 1
        modify_invoice_id = self.invoice_detail_info[serial_no_p][0]
        pn = self.invoice_detail_info[serial_no_p][1]
        pq = self.invoice_detail_info[serial_no_p][2]
        pr = self.invoice_detail_info[serial_no_p][4]
        pd = self.invoice_detail_info[serial_no_p][5]
        rad = self.invoice_detail_info[serial_no_p][6]
        afd = self.invoice_detail_info[serial_no_p][7]
        pi = self.invoice_detail_info[serial_no_p][13]
        if self.transaction_type == "sale":
            sq = "update sale_invoice_detail " \
                 "set (" \
                 "product_rate, " \
                 "rate_after_discount, " \
                 "amount_after_discount, " \
                 "cgst_amount, " \
                 "sgst_amount, " \
                 "amount_after_gst, " \
                 "igst_amount " \
                 ")" \
                 " = (%s, %s, %s, %s, %s, %s, %s) " \
                 "where id  = %s"
        elif self.transaction_type == "purchase":
            sq = "update purchase_invoice_detail " \
                 "set (" \
                 "product_rate, " \
                 "rate_after_discount, " \
                 "amount_after_discount, " \
                 "cgst_amount, " \
                 "sgst_amount, " \
                 "amount_after_gst, " \
                 "igst_amount " \
                 ")" \
                 " = (%s, %s, %s, %s, %s, %s, %s) " \
                 "where id  = %s"
        new_rad = Decimal(new_rate) - (Decimal(new_rate) * (Decimal(pd) / 100))
        amount_after_discount = Decimal(pq) * new_rad
        if self.gst_type == "igst":
            igst_rate = self.invoice_detail_info[serial_no_p][15]
            igst = get_cgst(amount_after_discount, igst_rate)
            cgst = 0
        else:
            cgst_rate = self.invoice_detail_info[serial_no_p][9]
            cgst = get_cgst(amount_after_discount, cgst_rate)
            igst = 0
        sgst = cgst
        amount_after_gst = Decimal(amount_after_discount) + cgst + sgst + igst
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq,
                           (new_rate,
                            new_rad,
                            amount_after_discount,
                            cgst,
                            sgst,
                            amount_after_gst,
                            igst,
                            modify_invoice_id))
        self.update_rate_discount(int(pi), new_rate, pd)
        self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
        self.view_invoice()
        print("{} rate has changed from {} to {}".format(
            pn,
            pr,
            new_rate))

    def change_qty(self, serial_no_p, new_qty):
        new_qty = Decimal(new_qty)
        serial_no_p = int(serial_no_p) - 1
        modify_invoice_id = self.invoice_detail_info[serial_no_p][0]
        pn = self.invoice_detail_info[serial_no_p][1]
        pq = Decimal(self.invoice_detail_info[serial_no_p][2])
        pr = self.invoice_detail_info[serial_no_p][4]
        pd = self.invoice_detail_info[serial_no_p][5]
        rad = Decimal(self.invoice_detail_info[serial_no_p][6])
        # print("rad is {}".format(rad))
        afd = self.invoice_detail_info[serial_no_p][7]
        if self.transaction_type == "sale":
            sq = "update sale_invoice_detail " \
                 "set (product_qty, " \
                 "amount_after_discount, " \
                 "cgst_amount, " \
                 "sgst_amount, " \
                 "amount_after_gst, " \
                 "igst_amount)" \
                 " = (%s, %s, %s, %s, %s, %s) " \
                 "where id  = %s"
            stock_query = "update stock set (" \
                          "qty_sale " \
                          ") = (%s) where id_sale_invoice_detail = %s"
        elif self.transaction_type == "purchase":
            sq = "update purchase_invoice_detail " \
                 "set (" \
                 "product_qty, " \
                 "amount_after_discount, " \
                 "cgst_amount, " \
                 "sgst_amount, " \
                 "amount_after_gst, " \
                 "igst_amount " \
                 ")" \
                 " = (%s, %s, %s, %s, %s, %s) " \
                 "where id  = %s"
            stock_query = "update stock set (" \
                          "qty_purchase " \
                          ") = (%s) where id_purchase_invoice_detail = %s"
        amount_after_discount = new_qty * rad
        if self.gst_type == "igst":
            igst_rate = self.invoice_detail_info[serial_no_p][15]
            igst = get_cgst(amount_after_discount, igst_rate)
            cgst = 0
        else:
            cgst_rate = self.invoice_detail_info[serial_no_p][9]
            cgst = get_cgst(amount_after_discount, cgst_rate)
            igst = 0
        sgst = cgst
        amount_after_gst = Decimal(amount_after_discount) + cgst + sgst + igst
        print(amount_after_gst)

        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (new_qty, amount_after_discount, cgst, sgst, amount_after_gst, igst, modify_invoice_id))
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(stock_query, (new_qty, modify_invoice_id))
        self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")

        self.view_invoice()
        print("{} qty has changed from {} to {}".format(
            pn,
            pq,
            new_qty))

    def change_disc(self, serial_no_p, new_disc):
        serial_no_p = int(serial_no_p) - 1
        modify_invoice_id = self.invoice_detail_info[serial_no_p][0]
        pn = self.invoice_detail_info[serial_no_p][1]
        pq = self.invoice_detail_info[serial_no_p][2]
        pr = self.invoice_detail_info[serial_no_p][4]
        pd = self.invoice_detail_info[serial_no_p][5]
        rad = self.invoice_detail_info[serial_no_p][6]
        # print("rad is {}".format(rad))
        afd = self.invoice_detail_info[serial_no_p][7]
        pi = self.invoice_detail_info[serial_no_p][13]
        if self.transaction_type == "sale":
            sq = "update sale_invoice_detail " \
                 "set (" \
                 "product_discount, " \
                 "rate_after_discount, " \
                 "amount_after_discount, " \
                 "cgst_amount, " \
                 "sgst_amount, " \
                 "amount_after_gst, " \
                 "igst_amount)" \
                 " = (%s, %s, %s, %s, %s, %s, %s) " \
                 "where id  = %s"
        elif self.transaction_type == "purchase":
            sq = "update purchase_invoice_detail " \
                 "set (" \
                 "product_discount, " \
                 "rate_after_discount, " \
                 "amount_after_discount, " \
                 "cgst_amount, " \
                 "sgst_amount, " \
                 "amount_after_gst, " \
                 "igst_amount " \
                 ")" \
                 " = (%s, %s, %s, %s, %s, %s, %s) " \
                 "where id  = %s"
        pr = Decimal(pr)
        new_disc = Decimal(new_disc)
        pq = Decimal(pq)
        new_rad = pr - (pr * (new_disc / 100))
        amount_after_discount = pq * new_rad
        if self.gst_type == "igst":
            igst_rate = self.invoice_detail_info[serial_no_p][15]
            igst = get_cgst(amount_after_discount, igst_rate)
            cgst = 0
        else:
            cgst_rate = self.invoice_detail_info[serial_no_p][9]
            cgst = get_cgst(amount_after_discount, cgst_rate)
            igst = 0
        sgst = cgst
        amount_after_gst = Decimal(amount_after_discount) + cgst + sgst + igst
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq,
                           (new_disc, new_rad, amount_after_discount, cgst, sgst, amount_after_gst, igst, modify_invoice_id))
        self.update_rate_discount(int(pi), pr, new_disc)
        self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
        self.view_invoice()
        print("{} disc has changed from {} to {}".format(
            pn,
            pd,
            new_disc))

    # def update_total_amount_after_gst(self):
    #     sq = "update sale_invoice set total_amount_after_gst = "
    #     with CursorFromConnectionFromPool as cursor:
    #         pass
    def get_address(self):
        if self.transaction_type == "sale":
            sq = "select " \
                 "address_first_line, " \
                 "address_second_line, " \
                 "address_third_line," \
                 "contact_no_one," \
                 "contact_no_two," \
                 "contact_no_three," \
                 "email_address from customer where id = %s"
        elif self.transaction_type == "purchase":
            sq = "select " \
                 "address_first_line, " \
                 "address_second_line, " \
                 "address_third_line," \
                 "contact_no_one," \
                 "contact_no_two," \
                 "contact_no_three," \
                 "email_address from vendor where id = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (self.id_transactor,))
            address = cursor.fetchone()
        i = 1
        temp = ["address_first_line", "address_second_line",
                "address_third_line", "contact_no_one",
                "contact_no_two", "contact_no_three",
                "email_address"]
        for a in address:
            print("{}. <{}>:       {}".format(i, temp[i - 1], a))
            i += 1

        get_address_first_line = rlinput(colored.blue("Enter address first line: ", address[0])).strip()
        get_address_second_line = rlinput(colored.blue("Enter address second line: ", address[1])).strip()
        get_address_third_line = rlinput(colored.blue("Enter address third line: ", address[2])).strip()
        get_contact_no_one = rlinput(colored.blue("Enter contact number one: ", address[3])).strip()
        get_contact_no_two = rlinput(colored.blue("Enter contact number two: ", address[4])).strip()
        get_contact_no_three = rlinput(colored.blue("Enter contact number three: ", address[5])).strip()
        get_email_address = rlinput(colored.blue("Enter email address: ", address[6])).strip()
        if self.transaction_type == "sale":
            sq = "update customer set (" \
                 "address_first_line, " \
                 "address_second_line, " \
                 "address_third_line, " \
                 "contact_no_one, " \
                 "contact_no_two, " \
                 "contact_no_three, " \
                 "email_address" \
                 ") = (%s, %s, %s, %s, %s, %s, %s) where id = %s"
        elif self.transaction_type == "purchase":
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
                                self.id_transactor))
        except Exception as e:
            print(e)
            print("There was an error in entering address. Please try again")
        # while True:
        #     choice = input("Enter number from above list to edit, enter s to exit editing: ")
        #     if choice == "s":
        #         break
        #     try:
        #         choice = int(choice)
        #         if choice not in [1, 2, 3, 4, 5, 6, 7]:
        #             break
        #         print("Enter new value for <{}> ".format(temp[choice - 1]))
        #         new_entry = input("")
        #         # print(new_entry)
        #         if self.transaction_type == "sale":
        #             sq = "update customer set " + temp[choice - 1] + " = %s where id = %s"
        #         elif self.transaction_type == "purchase":
        #             sq = "update vendor set " + temp[choice - 1] + " = %s where id = %s"
        #         # print(sq)
        #         with CursorFromConnectionFromPool() as cursor:
        #             cursor.execute(sq, (new_entry, self.id_transactor))
        #     except Exception as e:
        #         print(e)

    def product_qty_options(self, product_name_p):
        if product_name_p.startswith("jaquar "):
            jq_number = product_name_p.split("jaquar ")[1]
            print("jq_number is {}".format(jq_number))
            search_jaquar_function(jq_number)
            self.show_invoice_flag=1
            return "continue", ""
        if product_name_p.startswith("f "):
            self.freight = product_name_p.split(" ")[1]
            self.freight = Decimal(self.freight)
            if self.transaction_type == "sale":
                sq = "update sale_invoice set freight = %s where id = %s"
            elif self.transaction_type == "purchase":
                sq = "update purchase_invoice set freight = %s where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (self.freight, self.id_invoice))
            print("freight is {}".format(self.freight))
            return "continue", ""
        if product_name_p == "cash":
            sq = "update sale_invoice set memo_type = %s where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, ("cash", self.id_invoice))
            return "continue", ""
        if product_name_p == "igst":
            if self.transaction_type == "sale":
                sq = "update customer set gst_type = %s where id = %s"
            elif self.transaction_type == "purchase":
                sq = "update vendor set gst_type = %s where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, ("igst", self.id_transactor))
            return "continue", ""
        if product_name_p.startswith("u "):
            if self.transaction_type == "sale":
                sq = "update sale_invoice_detail " \
                     "set (product_unit)" \
                     " = (%s) " \
                     "where id  = %s"
            elif self.transaction_type == "purchase":
                sq = "update purchase_invoice_detail " \
                     "set (product_unit)" \
                     " = (%s) " \
                     "where id  = %s"
            t = product_name_p.split("u ")[1]
            t = t.strip()
            if t.startswith("["):
                try:
                    range_starting = t.split(":")[0]
                    range_starting = range_starting.split("[")[1]
                    print("range_s {}".format(range_starting))
                    range_ending = (t.split(":")[1]).strip()
                    range_ending = (range_ending.split("]")[0]).strip()
                    new_unit = (t.split("] ")[1]).strip()
                    for a in range(int(range_starting), int(range_ending) + 1):
                        serial_no = a
                        pi = self.invoice_detail_info[int(serial_no) - 1][13]
                        Product.set_unit(pi, new_unit)
                        sid = self.invoice_detail_info[int(serial_no) - 1][0]
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(sq, (new_unit, sid))
                    self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                    self.view_invoice()
                    return "continue", ""
                except Exception as e:
                    print(e)
                    print("correct format is: u [1,5] Nos")
                    return "continue", ""
            serial_no, new_unit = t.split(" ")[0], t.split(" ")[1]
            pi = self.invoice_detail_info[int(serial_no) - 1][13]
            Product.set_unit(pi, new_unit)
            sid = self.invoice_detail_info[int(serial_no) - 1][0]
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (new_unit, sid))
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            self.view_invoice()
            return "continue", ""
        if product_name_p.startswith("number "):
            t = product_name_p.split("number ")[1]
            new_number = t.strip()
            if self.transaction_type == "sale":
                sq = "update sale_invoice set (invoice_no) = (%s) where id = %s"
            elif self.transaction_type == "purchase":
                sq = "update purchase_invoice set (invoice_no) = (%s) where id = %s"
            try:
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (new_number, self.id_invoice))
            except Exception as e:
                print(e)
            self.show_invoice_flag = 1
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            self.view_invoice()
            return "continue", ""
        if product_name_p == "address":
            self.get_address()
            return "continue", ""
        if product_name_p.startswith("gst "):
            t = product_name_p.split("gst ")[1]
            new_gst = t.strip()
            if self.transaction_type == "sale":
                sq = "update customer set (gst) = (%s) where id = %s"
            elif self.transaction_type == "purchase":
                sq = "update vendor set (gst) = (%s) where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (new_gst, self.id_transactor))
            return "continue", ""
        if product_name_p.startswith("h "):
            if self.transaction_type == "sale":
                sq = "update sale_invoice_detail " \
                     "set (product_hsn)" \
                     " = (%s) " \
                     "where id  = %s"
            elif self.transaction_type == "purchase":
                sq = "update purchase_invoice_detail " \
                     "set (product_hsn)" \
                     " = (%s) " \
                     "where id  = %s"
            t = product_name_p.split("h ")[1]
            t = t.strip()
            if t.startswith("["):
                try:
                    range_starting = t.split(":")[0]
                    range_starting = range_starting.split("[")[1]
                    print("range_s {}".format(range_starting))
                    range_ending = (t.split(":")[1]).strip()
                    range_ending = (range_ending.split("]")[0]).strip()
                    new_hsn = (t.split("] ")[1]).strip()
                    for a in range(int(range_starting), int(range_ending) + 1):
                        serial_no = a
                        pi = self.invoice_detail_info[int(serial_no) - 1][13]
                        Product.set_hsn_code(pi, new_hsn)
                        sid = self.invoice_detail_info[int(serial_no) - 1][0]
                        # print(new_hsn, sid)
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(sq, (new_hsn, sid))
                    self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                    self.view_invoice()
                    return "continue", ""
                except Exception as e:
                    print(e)
                    print("correct format is: hsn [1:5] 8708")
                    return "continue", ""
            serial_no, new_hsn = t.split(" ")[0], t.split(" ")[1]
            pi = self.invoice_detail_info[int(serial_no) - 1][13]
            Product.set_hsn_code(pi, new_hsn)

            sid = self.invoice_detail_info[int(serial_no) - 1][0]
            # print(new_hsn, sid)
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (new_hsn, sid))
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            self.view_invoice()
            return "continue", ""
        if product_name_p.startswith("igst "):
            if self.transaction_type == "sale":
                sq = "update sale_invoice_detail " \
                     "set (product_igst_rate, igst_amount)" \
                     " = (%s, %s) " \
                     "where id  = %s"
            elif self.transaction_type == "purchase":
                sq = "update purchase_invoice_detail " \
                     "set (product_igst_rate, igst_amount)" \
                     " = (%s, %s) " \
                     "where id  = %s"
            t = product_name_p.split("igst ")[1]
            t = t.strip()
            if t.startswith("["):
                try:
                    range_starting = t.split(":")[0]
                    range_starting = range_starting.split("[")[1]
                    range_ending = (t.split(":")[1]).strip()
                    range_ending = (range_ending.split("]")[0]).strip()
                    new_igst = (t.split("] ")[1]).strip()
                    new_igst = int(new_igst)/2
                    for a in range(int(range_starting), int(range_ending) + 1):
                        serial_no = a
                        pi = self.invoice_detail_info[int(serial_no) - 1][13]
                        afd = self.invoice_detail_info[int(serial_no) - 1][7]
                        print("pi and cgst are {} and {}".format(pi, new_igst))
                        Product.set_cgst_rate(pi, new_igst)
                        sid = self.invoice_detail_info[int(serial_no) - 1][0]
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(sq, (new_igst, get_cgst(afd, new_igst), sid))
                    self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                    self.view_invoice()
                    return "continue", ""
                except Exception as e:
                    print(e)
                    print("correct format is: hsn [1,5] 8708")
                    return "continue", ""
            serial_no, new_igst = t.split(" ")[0], t.split(" ")[1]
            pi = self.invoice_detail_info[int(serial_no) - 1][13]
            afd = self.invoice_detail_info[int(serial_no) - 1][7]
            print("pi and cgst are {} and {}".format(pi, new_igst))
            new_igst = int(new_igst)/2
            Product.set_cgst_rate(pi, new_igst)
            sid = self.invoice_detail_info[int(serial_no) - 1][0]
            # print(sid)
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (new_igst, get_cgst(afd, new_igst), sid))
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            self.view_invoice()
            return "continue", ""
        if product_name_p.startswith("t "):
            if self.transaction_type == "sale":
                sq = "update sale_invoice_detail " \
                     "set (product_cgst_rate, cgst_amount, sgst_amount)" \
                     " = (%s, %s, %s) " \
                     "where id  = %s"
            elif self.transaction_type == "purchase":
                sq = "update purchase_invoice_detail " \
                     "set (product_cgst_rate, cgst_amount, sgst_amount)" \
                     " = (%s, %s, %s) " \
                     "where id  = %s"
            t = product_name_p.split("t ")[1]
            t = t.strip()
            if t.startswith("["):
                try:
                    range_starting = t.split(":")[0]
                    range_starting = range_starting.split("[")[1]
                    range_ending = (t.split(":")[1]).strip()
                    range_ending = (range_ending.split("]")[0]).strip()
                    new_cgst = (t.split("] ")[1]).strip()
                    new_cgst = int(new_cgst/2)
                    for a in range(int(range_starting), int(range_ending) + 1):
                        serial_no = a
                        pi = self.invoice_detail_info[int(serial_no) - 1][13]
                        afd = self.invoice_detail_info[int(serial_no) - 1][7]
                        print("pi and cgst are {} and {}".format(pi, new_cgst))
                        Product.set_cgst_rate(pi, new_cgst)
                        sid = self.invoice_detail_info[int(serial_no) - 1][0]
                        with CursorFromConnectionFromPool() as cursor:
                            cursor.execute(sq, (new_cgst, get_cgst(afd, new_cgst), get_cgst(afd, new_cgst), sid))
                    self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                    self.view_invoice()
                    return "continue", ""
                except Exception as e:
                    print(e)
                    print("correct format is: hsn [1,5] 8708")
                    return "continue", ""
            serial_no, new_cgst = t.split(" ")[0], t.split(" ")[1]
            new_cgst = int(new_cgst)/2
            pi = self.invoice_detail_info[int(serial_no) - 1][13]
            afd = self.invoice_detail_info[int(serial_no) - 1][7]
            print("pi and cgst are {} and {}".format(pi, new_cgst))

            Product.set_cgst_rate(pi, new_cgst)
            sid = self.invoice_detail_info[int(serial_no) - 1][0]
            # print(sid)

            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (new_cgst, get_cgst(afd, new_cgst), get_cgst(afd, new_cgst), sid))
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            self.view_invoice()
            return "continue", ""
        if product_name_p == "p":
            if self.transaction_type == "sale":
                self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                self.create_report_sale_invoice()
            if self.transaction_type == "purchase":
                self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                self.create_report_sale_invoice()
            return "continue", ""
        if product_name_p == "save":
            self.save_transaction()
            return "continue", ""
        if product_name_p.startswith("de "):
            t = product_name_p.split("de ")[-1]
            if t.startswith("["):
                try:
                    range_starting = t.split(":")[0]
                    range_starting = range_starting.split("[")[1]
                    print("range_s {}".format(range_starting))
                    range_ending = (t.split(":")[1]).strip()
                    range_ending = (range_ending.split("]")[0]).strip()
                    print("range_e {}".format(range_ending))
                    for a in range(int(range_starting), int(range_ending) + 1):
                        serial_no = a
                        self.delete_invoice_detail(serial_no)
                    self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
                    self.view_invoice()
                    return "continue", ""
                except Exception as e:
                    print(e)
                    return "continue", ""
            serial_no = t.strip()
            self.delete_invoice_detail(serial_no)
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            self.view_invoice()
            return "continue", ""
        if product_name_p.startswith("r "):
            t = product_name_p.split("r ")[1]
            t = t.strip()
            if t.startswith("["):
                try:
                    range_starting = t.split(":")[0]
                    range_starting = range_starting.split("[")[1]
                    range_ending = (t.split(":")[1]).strip()
                    range_ending = (range_ending.split("]")[0]).strip()
                    new_rate = (t.split("] ")[1]).strip()
                    for a in range(int(range_starting), int(range_ending) + 1):
                        serial_no = a
                        confirm_change = input(colored.blue("Change rate of item {} from {} to {}? (y/n): ").format(
                            self.invoice_detail_info[int(a)-1][1],
                            self.invoice_detail_info[int(a)-1][4],
                            new_rate))
                        confirm_change = confirm_change.strip()
                        if confirm_change.lower() == "y":
                            self.change_rate(serial_no, new_rate)
                        else:
                            print("No changes were made")
                            self.show_invoice_flag = 1
                    return "continue", ""
                except Exception as e:
                    print(e)
                    print("correct format is: rate [1,5] 52")
                    return "continue", ""
            serial_no, new_rate = t.split(" ")[0], t.split(" ")[1]
            # input("Change old rate {} to {}".format(self.invoice_detail_info[int(serial_no)-1][4], new_rate))
            confirm_change = input(colored.blue("Change rate of item {} from {} to {}? (y/n): ").format(
                self.invoice_detail_info[int(serial_no)-1][1],
                self.invoice_detail_info[int(serial_no)-1][4],
                new_rate))
            confirm_change = confirm_change.strip()
            if confirm_change.lower() == "y":
                self.change_rate(serial_no, new_rate)
            else:
                print("No changes were made")
                self.show_invoice_flag = 1
            return "continue", ""
        if product_name_p.startswith("q "):
            t = product_name_p.split("q ")[1]
            t = t.strip()
            if t.startswith("["):
                try:
                    range_starting = t.split(":")[0]
                    range_starting = range_starting.split("[")[1]
                    range_ending = (t.split(":")[1]).strip()
                    range_ending = (range_ending.split("]")[0]).strip()
                    new_qty = (t.split("] ")[1]).strip()
                    for a in range(int(range_starting), int(range_ending) + 1):
                        serial_no = a
                        confirm_change = input(colored.blue("Change qty of item {} from {} to {}? (y/n): ").format(
                            self.invoice_detail_info[int(a)-1][1],
                            self.invoice_detail_info[int(a)-1][2],
                            new_qty))
                        confirm_change = confirm_change.strip()
                        if confirm_change.lower() == "y":
                            self.change_qty(serial_no, new_qty)
                        else:
                            print("No changes were made")
                            self.show_invoice_flag = 1
                        # self.change_qty(serial_no, new_qty)
                    return "continue", ""
                except Exception as e:
                    print(e)
                    print("correct format is: rate [1,5] 52")
                    return "continue", ""
            serial_no, new_qty = t.split(" ")[0], t.split(" ")[1]
            confirm_change = input(colored.blue("Change qty of item {} from {} to {}? (y/n): ").format(
                self.invoice_detail_info[int(serial_no)-1][1],
                self.invoice_detail_info[int(serial_no)-1][2],
                new_qty))
            confirm_change = confirm_change.strip()
            if confirm_change.lower() == "y":
                self.change_qty(serial_no, new_qty)
            else:
                print("No changes were made")
                self.show_invoice_flag = 1
            return "continue", ""
        if product_name_p.startswith("d "):
            t = product_name_p.split("d ")[1]
            t = t.strip()
            if t.startswith("["):
                try:
                    range_starting = t.split(":")[0]
                    range_starting = range_starting.split("[")[1]
                    range_ending = (t.split(":")[1]).strip()
                    range_ending = (range_ending.split("]")[0]).strip()
                    new_disc = (t.split("] ")[1]).strip()
                    for a in range(int(range_starting), int(range_ending) + 1):
                        serial_no = a
                        self.change_disc(serial_no, new_disc)
                    return "continue", ""
                except Exception as e:
                    print(e)
                    print("correct format is: rate [1,5] 52")
                    return "continue", ""
            serial_no, new_disc = t.split(" ")[0], t.split(" ")[1]
            self.change_disc(serial_no, new_disc)
            return "continue", ""
        if product_name_p == "etd":
            if self.transaction_type == "sale":
                sq = "select preferred_transport from customer " \
                     "inner join sale_invoice on customer.id = sale_invoice.id_customer " \
                     "where sale_invoice.id = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (self.id_invoice,))
                    transport_name = cursor.fetchone()
                if transport_name[0] is None:
                    transport_name = input(colored.blue("Enter tranport name: ")).strip()
                print("Transport name is {}".format(transport_name))
                lr_no = input(colored.blue("Enter transport lr no: ")).strip()
                bags = input(colored.blue("Enter no of bags: ")).strip()
                sq = "update sale_invoice " \
                     "set (transport, transport_lr_no, transport_lr_no_of_bags) = " \
                     "(%s, %s, %s) where id = %s"
            elif self.transaction_type == "purchase":
                sq = "select preferred_transport from vendor" \
                     "inner join purchase_invoice on vendor.id = purchase_invoice.id_vendor" \
                     "where purchase_invoice.id = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (self.id_invoice,))
                    transport_name = cursor.fetchone()
                if transport_name[0] is None:
                    transport_name = input(colored.blue("Enter tranport name: ")).strip()
                print("Transport name is {}".format(transport_name))
                lr_no = input(colored.blue("Enter transport lr no: ")).strip()
                bags = input(colored.blue("Enter no of bags: ")).strip()
                sq = "update purchase_invoice " \
                     "set (transport, transport_lr_no, transport_lr_no_of_bags) = " \
                     "(%s, %s, %s) where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (transport_name, lr_no, bags, self.id_invoice))
            return "continue", ""
        if product_name_p == "date":
            try:
                print("The format for entering date is dd.mm.yy")
                print("e.g. 5.12.17 for 5th December 2017")
                new_date = input(colored.blue("Enter the date: ")).strip()
                self.update_date(new_date)
                return "continue", ""
            except Exception as e:
                print(e)
                return "continue", ""
        if product_name_p == "vip":

            return None, ""
            # return self.view_invoice_previous()
        if product_name_p == "vin":
            return None, ""
            # return self.view_invoice_next()
        if product_name_p == "vic":
            self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
            self.view_invoice()
            # self.create_report_sale_invoice()
            return "continue", ""
        if product_name_p == "del":
            self.delete_invoice()
            print("The invoice has been deleted.")
            return None, ""
            # return self.view_invoice_previous()
        if product_name_p == "q":
            import sys
            sys.exit()
            # return None, ""
        if product_name_p == "b":
            self.save_transaction()
            # import sys
            # sys.exit()
            return None, ""
        if product_name_p == "help":
            # system('clear && printf "\e[3J"')  # on linux / os x
            sale_detail_layout_instructions()
            self.show_invoice_flag = 1

            return "continue", ""

    def get_product_name_qty(self):
        options = ["vic", "vip", "vin", "b", "del", "help",
                   "date", "etd",
                   "save", "p", "q", "address", "igst", "cash"]
        options_start_with = ["jaquar ", "r ", "q ", "d ", "de ", "h ", "t ", "gst ", "number ", "u ", "igst ", "f "]
        try:
            while True:
                # sale_detail_layout_instructions()
                if self.show_invoice_flag == 0:
                    self.view_invoice()
                else:
                    self.show_invoice_flag = 0
                print("Enter b to go back")
                print("Enter help to see help")
                # product_name_qty = input(colored.blue("Enter product name: ")).strip()
                pr_completer = WordCompleter(self.product_name_list, ignore_case=True, sentence=True, match_middle=True)
                product_name_qty = prompt('Enter product name:', completer=pr_completer).strip()
                # product_name_qty = input(self.transaction_type
                #                          + "_"
                #                          + self.transactor_name
                #                          + " (" + self.transactor_place
                #                          + "): ").strip()
                if product_name_qty is None:
                    continue
                # product_name_qty = input("Enter product name and quantity or b to go back").strip()
                if not any([(product_name_qty.lower()).startswith(o) for o in options_start_with]) and not any(
                        [product_name_qty.lower() in options]):
                    # product_name, product_qty = product_qty_validate(product_name_qty)
                    product_name, product_qty = product_qty_validate2(product_name_qty)
                    if product_name is None:
                        self.show_invoice_flag = 1
                        continue
                    return product_name, product_qty
                else:
                    if not (product_name_qty.lower()).startswith("gst "):
                        product_name_qty = product_name_qty.lower()
                    return self.product_qty_options(product_name_qty)
        except Exception as e:
            print(e)
            return None, None

    def get_invoice_detail(self, **kwargs):
        # if self.debug == 0: print("get_invoice_detail")
        transaction_query_result = ""
        if self.transaction_type == "sale":
            if "extended" in kwargs:
                sq = "select Round(freight,2) from sale_invoice where id = %s"
                # print(sq)

                # input("")

                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (self.id_invoice, ))
                    self.freight = cursor.fetchone()[0]
                if self.freight is None: self.freight = 0
                self.update_invoice_total()
                transaction_query = "select " \
                                    "date, " \
                                    "transport, " \
                                    "transport_lr_no, " \
                                    "transport_lr_no_of_bags," \
                                    "invoice_no, " \
                                    "Round(amount_before_tax,2), " \
                                    "Round(cgst9_amount,2), " \
                                    "Round(sgst9_amount,2), " \
                                    "Round(cgst14_amount,2), " \
                                    "Round(sgst14_amount,2), " \
                                    "Round(cgst9_taxable_amount,2), " \
                                    "Round(cgst14_taxable_amount,2), " \
                                    "Round(total_amount_after_gst,0), " \
                                    "Round(cgst2_5_amount,2), " \
                                    "Round(sgst2_5_amount, 2), " \
                                    "Round(cgst6_amount,2), " \
                                    "Round(sgst6_amount,2), " \
                                    "Round(cgst2_5_taxable_amount,2), " \
                                    "Round(cgst6_taxable_amount, 2), " \
                                    "site, " \
                                    "Round(igst2_5_amount,2)," \
                                    "Round(igst6_amount,2), " \
                                    "Round(igst9_amount,2), " \
                                    "Round(igst14_amount,2), " \
                                    "Round(igst2_5_taxable_amount,2), " \
                                    "Round(igst6_taxable_amount,2), " \
                                    "Round(igst9_taxable_amount,2), " \
                                    "Round(igst14_taxable_amount,2), " \
                                    "id_customer," \
                                    "Round(freight,2) "\
                                    "from sale_invoice where id = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(transaction_query, (self.id_invoice,))
                    transaction_query_result = cursor.fetchall()
                print(transaction_query_result[0][0])
                self.invoice_no = transaction_query_result[0][4]
            some_query = "select " \
                         "id, " \
                         "product_name, " \
                         "Round(product_qty,2), " \
                         "product_unit, " \
                         "Round(product_rate,2), " \
                         "Round(product_discount,2), " \
                         "Round(rate_after_discount,2), " \
                         "Round(amount_after_discount,2), " \
                         "product_hsn, " \
                         "product_cgst_rate, " \
                         "Round(cgst_amount,2), " \
                         "Round(sgst_amount,2), " \
                         "Round(amount_after_gst), " \
                         "id_product, " \
                         "id_sale_invoice, " \
                         "product_igst_rate " \
                         "from sale_invoice_detail " \
                         "where id_sale_invoice = %s order by id asc"
        elif self.transaction_type == "purchase":
            if "extended" in kwargs:
                sq = "select Round(freight,2) from purchase_invoice where id = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (self.id_invoice, ))
                    self.freight = cursor.fetchone()[0]
                if self.ask_freight_gst != 0:
                    self.ask_freight_gst = input(colored.blue("Enter freight gst rate: ")).strip()
                else:
                    # this else covers both: freight = None and freight = 0
                    self.freight = 0
                    self.ask_freight_gst = 0

                self.update_invoice_total(freight_gst=self.ask_freight_gst)
                transaction_query = "select " \
                                    "date, " \
                                    "transport, " \
                                    "transport_lr_no, " \
                                    "transport_lr_no_of_bags," \
                                    "invoice_no, " \
                                    "Round(amount_before_tax,2), " \
                                    "Round(cgst9_amount,2), " \
                                    "Round(sgst9_amount,2), " \
                                    "Round(cgst14_amount,2), " \
                                    "Round(sgst14_amount,2), " \
                                    "Round(cgst9_taxable_amount,2), " \
                                    "Round(cgst14_taxable_amount,2), " \
                                    "Round(total_amount_after_gst,0), " \
                                    "Round(cgst2_5_amount,2), " \
                                    "Round(sgst2_5_amount, 2), " \
                                    "Round(cgst6_amount,2), " \
                                    "Round(sgst6_amount,2), " \
                                    "Round(cgst2_5_taxable_amount,2), " \
                                    "Round(cgst6_taxable_amount, 2), " \
                                    "site, " \
                                    "Round(igst2_5_amount,2)," \
                                    "Round(igst6_amount,2), " \
                                    "Round(igst9_amount,2), " \
                                    "Round(igst14_amount,2), " \
                                    "Round(igst2_5_taxable_amount,2), " \
                                    "Round(igst6_taxable_amount,2), " \
                                    "Round(igst9_taxable_amount,2), " \
                                    "Round(igst14_taxable_amount,2), " \
                                    "id_vendor," \
                                    "Round(freight,2) " \
                                    "from purchase_invoice where id = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(transaction_query, (self.id_invoice,))
                    transaction_query_result = cursor.fetchall()
            some_query = "select " \
                         "id, " \
                         "product_name, " \
                         "Round(product_qty, 2), " \
                         "product_unit, " \
                         "Round(product_rate, 2), " \
                         "Round(product_discount, 2), " \
                         "Round(rate_after_discount, 2), " \
                         "Round(amount_after_discount, 2), " \
                         "product_hsn, " \
                         "product_cgst_rate, " \
                         "Round(cgst_amount, 2), " \
                         "Round(sgst_amount, 2)," \
                         "Round(amount_after_gst), " \
                         "id_product, " \
                         "id_purchase_invoice, " \
                         "product_igst_rate " \
                         "from purchase_invoice_detail " \
                         "where id_purchase_invoice = %s order by id asc"
        elif self.transaction_type == "receipt":
            transaction_query = "select date, id_customer, amount, id, invoice_no from receipt where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(transaction_query, (self.id_invoice,))
                transaction_query_result = cursor.fetchall()
            tabulate(str(transaction_query_result[0][0]), str(transaction_query_result[0][1]))
            # print(transaction_query_result)
            return transaction_query_result, transaction_query_result
        elif self.transaction_type == "payment":
            transaction_query = "select date, id_vendor, amount, id, invoice_no from payment where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(transaction_query, (self.id_invoice,))
                transaction_query_result = cursor.fetchall()
            tabulate(str(transaction_query_result[0][0]), str(transaction_query_result[0][1]))
            # print(transaction_query_result)
            return transaction_query_result, transaction_query_result

        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(some_query, (self.id_invoice,))
            some_query_result = cursor.fetchall()
            # print("s is {}".format(some_query_result))
            return some_query_result, transaction_query_result

    def update_date(self, new_date_p):
        if self.transaction_type == "sale":
            sq = "update sale_invoice set date = to_date(%s, 'DD.MM.YY') where id  = %s"
            sq2 = "update sale_transaction set date = to_date(%s, 'DD.MM.YY') where id_sale_invoice  = %s"
        if self.transaction_type == "purchase":
            sq = "update purchase_invoice set date = to_date(%s, 'DD.MM.YY') where id  = %s"
            sq2 = "update purchase_transaction set date = to_date(%s, 'DD.MM.YY') where id_purchase_invoice  = %s"
        if self.transaction_type == "receipt":
            sq = "update receipt set date = to_date(%s, 'DD.MM.YY') where id  = %s"
            sq2 = "update sale_transaction set date = to_date(%s, 'DD.MM.YY') where id_receipt = %s"
        if self.transaction_type == "payment":
            sq = "update payment set date = to_date(%s, 'DD.MM.YY') where id  = %s"
            sq2 = "update purchase_transaction set date = to_date(%s, 'DD.MM.YY') where id_payment  = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (new_date_p, self.id_invoice))
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq2, (new_date_p, self.id_invoice))
        self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
        self.view_invoice()

    def create_report_sale_invoice(self):
        # import time
        # time.sleep(3)
        if self.transaction_type == "sale":
            sq = "select memo_type from sale_invoice where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (self.id_invoice,))
                memo_type = cursor.fetchone()[0]
            print("printing..")
            sq = "select gst, address_first_line, address_second_line, address_third_line, contact_no_one from customer where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (self.id_transactor,))
                customer_details = cursor.fetchone()
            create_sale_invoice_detail_csv(self.invoice_detail_info, self.invoice_info, self.transactor_name,
                                           self.transactor_place, customer_details, memo_type)
        self.save_transaction()
        # pdf_file_name = "/Users/python/projects/stack/project/temp.pdf"
        # exit()

    def view_invoice_detail(self):
        # if self.debug == 0: print("view_invoice_detail")
        if self.transaction_type == "sale" or self.transaction_type == "purchase":
            a_list = [el[1:] for el in (tuple(x) for x in self.invoice_detail_info)]
            a_list = replace_zero_with_none(a_list)
            a_list = [el[:-5]+(el[14],) for el in (x for x in a_list)]
            print(tabulate(a_list,
                           headers=['Sr', 'Name', 'Qty', 'Unit', 'Rate', 'Disc', 'Net Rate', 'Amount', 'HSN',
                                    'Tax Rate', 'CGST', "IGST"],
                           numalign="right",
                           floatfmt="0.2f",
                           tablefmt="psql",
                           showindex=range(1, len(self.invoice_detail_info) + 1)))
        elif self.transaction_type == "receipt" or self.transaction_type == "payment":
            a_list = [el[2:] for el in (tuple(x) for x in self.invoice_detail_info)]
            print(tabulate(a_list,
                           headers=['Sr', 'Amount', 'Type', 'Detail'],
                           numalign="right",
                           floatfmt="0.2f",
                           tablefmt="psql",
                           showindex=range(1, len(self.invoice_detail_info) + 1)))

    def get_rate_discount(self, id_product_p):
        if self.transaction_type == "sale":
            some_query = "select rate, discount from customer_product_join " \
                         "where id_customer = %s and id_product = %s"
        if self.transaction_type == "purchase":
            some_query = "select rate, discount from vendor_product_join " \
                         "where id_vendor = %s and id_product = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(some_query, (self.id_transactor, id_product_p))
            rd_id_tuple = cursor.fetchone()
            if rd_id_tuple is None:
                print("There are no previous rates for this product.")
                return None, None
            return rd_id_tuple[0], rd_id_tuple[1]

    def delete_invoice(self):
        confirm_delete_invoice = input(colored.blue("Are you sure you want to delete this invoice? (y/n): ")).strip()
        if confirm_delete_invoice.lower() == "y":
            if self.transaction_type == "sale":
                sq = "delete from sale_invoice where id = %s"
            elif self.transaction_type == "purchase":
                sq = "delete from purchase_invoice where id = %s"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (self.id_invoice,))
            self.already_deleted = 1

    def view_invoice_previous(self):
        if self.transaction_type == "sale":
            sq = "select row_number() over(order by id desc) as row_rank, id, id_customer, name, place " \
                 "from sale_invoice where id < %s limit 1"
        elif self.transaction_type == "purchase":
            sq = "select row_number() over(order by id desc) as row_rank, id, id_vendor, name, place " \
                 "from purchase_invoice where id < %s limit 1"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (self.id_invoice,))
            tf = cursor.fetchone()
            try:
                return "change invoice", [str(tf[1]), tf[3], tf[4]]
            except Exception as e:
                print("Exception in vip': {}".format(e))
                return None, ""

    def view_invoice_next(self):
        if self.transaction_type == "sale":
            sq = "select row_number() over(order by invoice_no asc) as row_rank, id, id_customer, name, place " \
                 "from sale_invoice where invoice_no > %s limit 1"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (self.invoice_no,))
                tf = cursor.fetchone()
            try:
                return "change invoice", [str(tf[1]), tf[3], tf[4]]
            except Exception as e:
                print("Exception in 'vin': {}".format(e))
                print(str(tf[1]))
                return None, ""
        elif self.transaction_type == "purchase":
            sq = "select row_number() over(order by id asc) as row_rank, id, id_vendor, name, place " \
                 "from purchase_invoice where id > %s limit 1"
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (self.id_invoice,))
                tf = cursor.fetchone()
            try:
                return "change invoice", [str(tf[1]), tf[3], tf[4]]
            except Exception as e:
                print("Exception in 'vin': {}".format(e))
                return None, ""

    def get_gst_type(self):
        if self.transaction_type == "sale":
            sq = "select gst_type from customer where id = %s"
        if self.transaction_type == "purchase":
            sq = "select gst_type from vendor where id = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (self.id_transactor,))
            return cursor.fetchone()[0]

    def create_invoice_detail(self, id_product_p, product_qty_p, product_rate_p, product_discount_p, sale_invoice_date_p):
        rate_after_discount = get_rate_after_discount(product_rate_p, product_discount_p)
        amount_after_discount = get_amount_after_discount(rate_after_discount, product_qty_p)
        with CursorFromConnectionFromPool() as cursor:
            some_query = "select name, unit, hsn, cgst_rate from product where id = %s"
            cursor.execute(some_query, (id_product_p,))
            product_details_p = cursor.fetchone()
            product_name_p = product_details_p[0]
            product_unit_p = product_details_p[1]
            product_hsn_p = product_details_p[2]
            product_cgst_p = product_details_p[3]
        if self.gst_type == "igst":
            igst = get_cgst(amount_after_discount, product_cgst_p)
            cgst = 0
            product_igst = product_cgst_p
            product_cgst_p = 0
        else:
            cgst = get_cgst(amount_after_discount, product_cgst_p)
            igst = 0
            product_igst = 0
        sgst = cgst

        if self.transaction_type == "sale":

            some_query = "insert into sale_invoice_detail " \
                         "(id_sale_invoice, id_product, " \
                         "product_name, product_qty, product_unit, " \
                         "product_rate, product_discount, rate_after_discount, amount_after_discount, " \
                         "product_hsn, product_cgst_rate, cgst_amount, sgst_amount, amount_after_gst, igst_amount, product_igst_rate, d_date) " \
                         "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id"
            stock_query = "insert into stock (" \
                          "id_sale_invoice_detail, " \
                          "id_product, " \
                          "product_name, " \
                          "product_unit, " \
                          "qty_sale, " \
                          "stock_date " \
                          ") values (%s, %s, %s, %s, %s, %s)"
        elif self.transaction_type == "purchase":
            some_query = "insert into purchase_invoice_detail " \
                         "(id_purchase_invoice, id_product, " \
                         "product_name, product_qty, product_unit, " \
                         "product_rate, product_discount, rate_after_discount, amount_after_discount," \
                         "product_hsn, product_cgst_rate, cgst_amount, sgst_amount, amount_after_gst, igst_amount, product_igst_rate, d_date) " \
                         "values (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s) returning id"
            stock_query = "insert into stock " \
                          "(id_purchase_invoice_detail, " \
                          "id_product, " \
                          "product_name, " \
                          "product_unit, " \
                          "qty_purchase," \
                          "stock_date " \
                          ") values (%s, %s, %s, %s, %s, %s)"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(some_query, (self.id_invoice, id_product_p,
                                        product_name_p, product_qty_p, product_unit_p,
                                        product_rate_p, product_discount_p,
                                        rate_after_discount, amount_after_discount,
                                        product_hsn_p, product_cgst_p, cgst, sgst,
                                        (amount_after_discount + (cgst * 2) + igst), igst, product_igst, sale_invoice_date_p))
            sale_invoice_detail_id = cursor.fetchone()
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(stock_query, (sale_invoice_detail_id,
                                         id_product_p,
                                         product_name_p,
                                         product_unit_p,
                                         product_qty_p,
                                         sale_invoice_date_p
                                         ))

    def delete_invoice_detail(self, serial_no_p):
        if self.transaction_type == "sale":
            sq = "delete from sale_invoice_detail where id = %s"
        elif self.transaction_type == "purchase":
            sq = "delete from purchase_invoice_detail where id = %s"
        modify_invoice_id = int(self.invoice_detail_info[int(serial_no_p) - 1][0])
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (modify_invoice_id,))
        print("deleted")

    def update_rate_discount(self, id_product_p, product_rate, product_discount):
        # set or update rate,discount in customer product join table
        if self.transaction_type == "sale":
            some_query = "insert into customer_product_join (id_customer, id_product, rate, discount) values " \
                         "(%s, %s, %s, %s)"
            alt_query = "update customer_product_join set (rate, discount) = " \
                        "(%s, %s) where id_customer = %s and id_product = %s"
        elif self.transaction_type == "purchase":
            some_query = "insert into vendor_product_join (id_vendor, id_product, rate, discount) values " \
                         "(%s, %s, %s, %s)"
            alt_query = "update vendor_product_join set (rate, discount) = " \
                        "(%s, %s) where id_vendor = %s and id_product = %s"
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(some_query, (self.id_transactor, id_product_p, product_rate, product_discount))
                print("added new values.")
        except Exception as e:
            if str(e).startswith("duplicate key value violates unique constraint"):
                with CursorFromConnectionFromPool() as cursor:
                    print("updating old values...")
                    cursor.execute(alt_query, (product_rate, product_discount, self.id_transactor, id_product_p))

    def save_transaction(self):
        if self.transaction_type == "sale":
            sq = "insert into sale_transaction (id_sale_invoice, date, id_customer, type, amount_sale) values " \
                 "(%s, %s, %s, %s, %s) returning id"
            sq2 = "update sale_invoice set id_sale_transaction =  %s where id = %s"
            sq_alt = "update sale_transaction set (amount_sale, date) = (%s, %s) where id_sale_invoice = %s"
        elif self.transaction_type == "purchase":
            sq = "insert into purchase_transaction (id_purchase_invoice, date, id_vendor, type, amount_purchase) values " \
                 "(%s, %s, %s, %s, %s) returning id"
            sq2 = "update purchase_invoice set id_purchase_transaction =  %s where id = %s"
            sq_alt = "update purchase_transaction set (amount_purchase, date) = (%s, %s) where id_purchase_invoice = %s"
        elif self.transaction_type == "receipt":
            sq = "insert into sale_transaction (id_receipt , date, id_customer, type, amount_receipt) values " \
                 "(%s, %s, %s, %s, %s) returning id"
            sq2 = "update receipt set id_sale_transaction =  %s where id = %s"
            sq_alt = "update sale_transaction set amount_receipt= %s where id_receipt = %s"
        elif self.transaction_type == "payment":
            sq = "insert into purchase_transaction (id_payment , date, id_vendor, type, amount_payment) values " \
                 "(%s, %s, %s, %s, %s) returning id"
            sq2 = "update payment set id_purchase_transaction =  %s where id = %s"
            sq_alt = "update purchase_transaction set amount_payment= %s where id_payment = %s"
        self.invoice_detail_info, self.invoice_info = self.get_invoice_detail(extended="yes")
        if self.transaction_type == "sale" or self.transaction_type == "purchase":
            self.id_transactor = self.invoice_info[0][28]
        elif self.transaction_type == "receipt" or self.transaction_type == "payment":
            print(self.invoice_info)
            self.id_transactor = self.invoice_info[0][1]
            self.total_amount_after_gst = self.invoice_info[0][2]
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq, (self.id_invoice,
                                    self.invoice_info[0][0],
                                    self.id_transactor,
                                    self.transaction_type,
                                    self.total_amount_after_gst))
                stid = cursor.fetchone()[0]
        except Exception as e:
            print("e: {}".format(e))
            if str(e).startswith("duplicate key value violates unique constraint"):

                print("Attempting to update...")
                try:
                    with CursorFromConnectionFromPool() as cursor:
                        cursor.execute(sq_alt, (self.total_amount_after_gst, self.invoice_info[0][0], self.id_invoice))
                    print("{} transaction has been updated".format(self.transaction_type))
                except Exception as e:
                    print("Error while attempting to update transaction")
                    print(e)
                return None
            else:
                return None
        try:
            with CursorFromConnectionFromPool() as cursor:
                cursor.execute(sq2, (stid, self.id_invoice))
            print("{} transaction has been saved".format(self.transaction_type))
        except Exception as e:
            print(e)

    def get_taxable_total_igst(self, rate):
        if self.transaction_type == "sale":
            get_taxable_total_igst = "select Round(sum(amount_after_discount),2) as s from sale_invoice_detail" \
                                     " inner join sale_invoice" \
                                     " on sale_invoice.id = sale_invoice_detail.id_sale_invoice " \
                                     "where sale_invoice.id = %s and sale_invoice_detail.product_igst_rate = %s"
        elif self.transaction_type == "purchase":
            get_taxable_total_igst = "select Round(sum(amount_after_discount),2) as s from purchase_invoice_detail " \
                                     "inner join purchase_invoice " \
                                     "on purchase_invoice.id = purchase_invoice_detail.id_purchase_invoice " \
                                     "where purchase_invoice.id = %s and purchase_invoice_detail.product_igst_rate = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(get_taxable_total_igst, (self.id_invoice, rate))
            taxable_total = cursor.fetchone()[0]
            if taxable_total is None: taxable_total = 0
            return taxable_total

    def get_taxable_total_cgst(self, rate):
        if self.transaction_type == "sale":
            get_taxable_total_cgst = "select Round(sum(amount_after_discount),2) as s from sale_invoice_detail " \
                                     "inner join sale_invoice " \
                                     "on sale_invoice.id = sale_invoice_detail.id_sale_invoice " \
                                     "where sale_invoice.id = %s and sale_invoice_detail.product_cgst_rate = %s"
        elif self.transaction_type == "purchase":
            get_taxable_total_cgst = "select Round(sum(amount_after_discount),2) as s from purchase_invoice_detail " \
                                     "inner join purchase_invoice " \
                                     "on purchase_invoice.id = purchase_invoice_detail.id_purchase_invoice " \
                                     "where purchase_invoice.id = %s and purchase_invoice_detail.product_cgst_rate = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(get_taxable_total_cgst, (self.id_invoice, rate))
            taxable_total = cursor.fetchone()[0]
            if taxable_total is None: taxable_total = 0
            return taxable_total

    def get_total_igst(self, rate):
        if self.transaction_type == "sale":
            get_total_igst = "select Round(sum(igst_amount),2) as s from sale_invoice_detail" \
                             " inner join sale_invoice" \
                             " on sale_invoice.id = sale_invoice_detail.id_sale_invoice " \
                             "where sale_invoice.id = %s and sale_invoice_detail.product_igst_rate = %s"
        elif self.transaction_type == "purchase":
            get_total_igst = "select Round(sum(igst_amount),2) as s from purchase_invoice_detail " \
                             "inner join purchase_invoice " \
                             "on purchase_invoice.id = purchase_invoice_detail.id_purchase_invoice " \
                             "where purchase_invoice.id = %s and purchase_invoice_detail.product_igst_rate = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(get_total_igst, (self.id_invoice, rate))
            total_igst = cursor.fetchone()[0]
            if total_igst is None: total_igst = 0
            return total_igst

    def get_total_cgst(self, rate):
        if self.transaction_type == "sale":
            get_total_cgst = "select Round(sum(cgst_amount),2) as s from sale_invoice_detail" \
                             " inner join sale_invoice" \
                             " on sale_invoice.id = sale_invoice_detail.id_sale_invoice " \
                             "where sale_invoice.id = %s and sale_invoice_detail.product_cgst_rate = %s"
        elif self.transaction_type == "purchase":
            get_total_cgst = "select Round(sum(cgst_amount),2) as s from purchase_invoice_detail" \
                             " inner join purchase_invoice" \
                             " on purchase_invoice.id = purchase_invoice_detail.id_purchase_invoice " \
                             "where purchase_invoice.id = %s and purchase_invoice_detail.product_cgst_rate = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(get_total_cgst, (self.id_invoice, rate))
            total_cgst = cursor.fetchone()[0]
            if total_cgst is None: total_cgst = 0
            return total_cgst

    def update_invoice_total(self, **kwargs):
        if self.transaction_type == "sale":
            get_total_afd = "select Round(sum(amount_after_discount),2) as s from sale_invoice_detail " \
                            "inner join" \
                            " sale_invoice on sale_invoice.id = sale_invoice_detail.id_sale_invoice " \
                            "where sale_invoice.id = %s"
        if self.transaction_type == "purchase":
            get_total_afd = "select Round(sum(amount_after_discount),2) as s from purchase_invoice_detail " \
                            "inner join " \
                            "purchase_invoice on purchase_invoice.id = purchase_invoice_detail.id_purchase_invoice " \
                            "where purchase_invoice.id = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(get_total_afd, (self.id_invoice,))
            self.total_afd = cursor.fetchone()[0]
            print("total afd is {}".format(self.total_afd))
            if self.total_afd is None: self.total_afd = 0
        self.taxable_total_cgst2_5 = self.get_taxable_total_cgst(2.5)
        self.taxable_total_cgst6 = self.get_taxable_total_cgst(6)
        self.taxable_total_cgst9 = self.get_taxable_total_cgst(9)
        self.taxable_total_cgst14 = self.get_taxable_total_cgst(14)
        self.taxable_total_igst2_5 = self.get_taxable_total_igst(2.5)
        self.taxable_total_igst6 = self.get_taxable_total_igst(6)
        self.taxable_total_igst9 = self.get_taxable_total_igst(9)
        self.taxable_total_igst14 = self.get_taxable_total_igst(14)
        freight_gst14 = 0
        freight_gst9 = 0
        freight_gst6 = 0
        freight_gst2_5 = 0
        if "freight_gst" in kwargs:
            print("freight is {}".format(self.freight))
            if self.taxable_total_igst14 != 0:
                self.taxable_total_igst14 = Decimal(self.taxable_total_igst14) + self.freight
                freight_gst14 = round(self.freight*Decimal(0.14),2)
            elif self.taxable_total_igst9 != 0:
                self.taxable_total_igst9 = Decimal(self.taxable_total_igst9) + self.freight
                freight_gst9 = round(self.freight * Decimal(0.09),2)
            elif self.taxable_total_igst6 != 0:
                self.taxable_total_igst6 = Decimal(self.taxable_total_igst6) + self.freight
                freight_gst6 = round(self.freight * Decimal(0.06),2)
            elif self.taxable_total_igst2_5 != 0:
                self.taxable_total_igst2_5 = Decimal(self.taxable_total_igst2_5) + self.freight
                freight_gst2_5 = round(self.freight * Decimal(0.025),2)
        else:
            if self.freight != 0:
                if self.taxable_total_cgst14 != 0:
                    self.taxable_total_cgst14 = Decimal(self.taxable_total_cgst14) + self.freight
                    freight_gst14 = round(self.freight*Decimal(0.14),2)
                elif self.taxable_total_cgst9 != 0:
                    self.taxable_total_cgst9 = Decimal(self.taxable_total_cgst9) + self.freight
                    freight_gst9 = round(self.freight * Decimal(0.09),2)
                elif self.taxable_total_cgst6 != 0:
                    self.taxable_total_cgst6 = Decimal(self.taxable_total_cgst6) + self.freight
                    freight_gst6 = round(self.freight * Decimal(0.06),2)
                elif self.taxable_total_cgst2_5 != 0:
                    self.taxable_total_cgst2_5 = Decimal(self.taxable_total_cgst2_5) + self.freight
                    freight_gst2_5 = round(self.freight * Decimal(0.025),2)
        self.total_cgst2_5 = self.get_total_cgst(2.5) + freight_gst2_5
        self.total_cgst6 = self.get_total_cgst(6) + freight_gst6
        self.total_cgst9 = self.get_total_cgst(9) + freight_gst9
        self.total_cgst14 = self.get_total_cgst(14) + freight_gst14
        self.total_igst2_5 = self.get_total_igst(2.5) + freight_gst2_5
        self.total_igst6 = self.get_total_igst(6) + freight_gst6
        self.total_igst9 = self.get_total_igst(9) + freight_gst9
        self.total_igst14 = self.get_total_igst(14) + freight_gst14

        if self.gst_type == "igst":
            self.total_amount_after_gst = self.total_afd + self.freight + \
                                          (2 * self.total_igst2_5) + \
                                          (2 * self.total_igst6) + \
                                          (2 * self.total_igst9) + \
                                          (2 * self.total_igst14)
            print("{} is afd".format(self.total_afd))
            # print(self.total_igst9)
            print("{} is total amount after gst".format(self.total_amount_after_gst))
        else:
            self.total_amount_after_gst = self.total_afd + self.freight + \
                                          (2 * self.total_cgst2_5) + \
                                          (2 * self.total_cgst6) + \
                                          (2 * self.total_cgst9) + \
                                          (2 * self.total_cgst14)
        self.total_amount_after_gst = round(self.total_amount_after_gst, 0)
        if self.transaction_type == "sale":
            update_total = "update sale_invoice " \
                           "set (" \
                           "amount_before_tax, " \
                           "cgst9_amount, " \
                           "sgst9_amount, " \
                           "cgst14_amount, " \
                           "sgst14_amount, " \
                           "cgst2_5_amount, " \
                           "sgst2_5_amount," \
                           "cgst6_amount, " \
                           "sgst6_amount," \
                           "cgst9_taxable_amount, " \
                           "sgst9_taxable_amount, " \
                           "cgst14_taxable_amount, " \
                           "sgst14_taxable_amount, " \
                           "cgst2_5_taxable_amount, " \
                           "sgst2_5_taxable_amount, " \
                           "cgst6_taxable_amount, " \
                           "sgst6_taxable_amount, " \
                           "total_amount_after_gst, " \
                           "igst2_5_amount, " \
                           "igst6_amount, " \
                           "igst9_amount, " \
                           "igst14_amount, " \
                           "igst2_5_taxable_amount, " \
                           "igst6_taxable_amount, " \
                           "igst9_taxable_amount, " \
                           "igst14_taxable_amount) " \
                           "= (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                           "%s, %s, %s, %s, %s, %s, %s, %s ) where id = %s"
        elif self.transaction_type == "purchase":
            update_total = "update purchase_invoice " \
                           "set (" \
                           "amount_before_tax, " \
                           "cgst9_amount, " \
                           "sgst9_amount, " \
                           "cgst14_amount, " \
                           "sgst14_amount, " \
                           "cgst2_5_amount, " \
                           "sgst2_5_amount," \
                           "cgst6_amount, " \
                           "sgst6_amount," \
                           "cgst9_taxable_amount, " \
                           "sgst9_taxable_amount, " \
                           "cgst14_taxable_amount, " \
                           "sgst14_taxable_amount, " \
                           "cgst2_5_taxable_amount, " \
                           "sgst2_5_taxable_amount, " \
                           "cgst6_taxable_amount, " \
                           "sgst6_taxable_amount, " \
                           "total_amount_after_gst, " \
                           "igst2_5_amount, " \
                           "igst6_amount, " \
                           "igst9_amount, " \
                           "igst14_amount, " \
                           "igst2_5_taxable_amount, " \
                           "igst6_taxable_amount, " \
                           "igst9_taxable_amount, " \
                           "igst14_taxable_amount) " \
                           "= (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, " \
                           "%s, %s, %s, %s, %s, %s, %s, %s ) where id = %s"
            print("selftotalafd is {} and freight is {}".format(self.total_afd, self.freight))
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(update_total, (self.total_afd,
                                          self.total_cgst9, self.total_cgst9,
                                          self.total_cgst14, self.total_cgst14,
                                          self.total_cgst2_5, self.total_cgst2_5,
                                          self.total_cgst6, self.total_cgst6,
                                          self.taxable_total_cgst9, self.taxable_total_cgst9,
                                          self.taxable_total_cgst14, self.taxable_total_cgst14,
                                          self.taxable_total_cgst2_5, self.taxable_total_cgst2_5,
                                          self.taxable_total_cgst6, self.taxable_total_cgst6,
                                          self.total_amount_after_gst,
                                          self.total_igst2_5, self.total_igst6, self.total_igst9, self.total_igst14,
                                          self.taxable_total_igst2_5, self.taxable_total_igst6,self.taxable_total_igst9, self.taxable_total_igst14,
                                          self.id_invoice))


def replace_zero_with_none(lot):
    temp_list = []
    for a in lot:
        start_string = a[:4]
        # print(start_string)
        if int(a[4]) == 0:
            # print("0")
            # print(a[0])
            middle_string = None
        else:
            middle_string = a[4]
        # print(middle_string)
        last_string = a[5:]
        # print(last_string)
        start_string += (middle_string,)
        start_string += last_string
        # inside_list = []
        # inside_list = start_string + (middle_string, )
        # print("inside_list is {}".format(inside_list))
        temp_list.append(start_string)
    return temp_list


def reverse_date(i):
    i = i.split("-")
    i = i[2] + "-" + i[1] + "-"+ i[0]
    return i
