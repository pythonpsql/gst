from database import Database, CursorFromConnectionFromPool
from list_completer import TabCompleter
from clint.textui import colored, indent, puts


def get_product_name_list():
    with CursorFromConnectionFromPool() as cursor:
        some_query = "select name from product"  # same as select * from customer
        cursor.execute(some_query)
        name_list = cursor.fetchall()
        flat_list = [element for tupl in name_list for element in tupl]
        return flat_list


class Product:
    @classmethod
    def set_unit(cls, pi_p, new_unit_p):
        sq = "update product set unit = %s where id = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (new_unit_p, pi_p))

    @classmethod
    def set_cgst_rate(cls, pi_p, new_cgst_p):
        if new_cgst_p is not None:
            if not new_cgst_p == 0:
                # new_cgst_p = int(new_cgst_p)
                sq = "update product set cgst_rate = %s where id = %s"
                with CursorFromConnectionFromPool() as cursor:
                    cursor.execute(sq, (new_cgst_p, pi_p))

    @classmethod
    def set_hsn_code(cls, pi_p, new_hsn_p):
        sq = "update product set hsn = %s where id = %s"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(sq, (new_hsn_p, pi_p))

    @classmethod
    def create_new_product(cls, product_name_p):
        TabCompleter([])
        try:
            new_name_confirm = input(colored.blue("Do you want to create a new product \'" + product_name_p + "\'? (y/n): ")).strip()
            new_name_confirm = new_name_confirm.lower()
            if new_name_confirm == 'y':
                unit_p = "Nos"
                # while True:
                #     print("Example of units: Nos, Kg, Pkt, Box etc")
                #     unit_p = input("What is the unit for product '{}'?: ".format(product_name_p))
                #     if unit_p != "":
                #         break
                get_tax_rate = input(colored.blue("Enter gst rate: ")).strip()
                if get_tax_rate == '':
                    print("it is none")
                    get_tax_rate = 0
                else:
                    get_tax_rate = int(int(get_tax_rate)/2)
                get_hsn = input(colored.blue("Enter hsn code: ")).strip()
                with CursorFromConnectionFromPool() as cursor:
                    some_query = "insert into product (name, unit, cgst_rate, hsn) values (%s, %s, %s, %s) returning id"
                    cursor.execute(some_query, (product_name_p, unit_p, get_tax_rate, get_hsn))
                    id_product_p = cursor.fetchone()[0]
                return id_product_p, product_name_p
            else:
                return "Declined new product name", None
        except Exception as e:
            print(e)


    @classmethod
    def get_product_id(cls, product_name_p):
        some_query = "select id from product where abbr_name = lower(%s)"
        with CursorFromConnectionFromPool() as cursor:
            cursor.execute(some_query, (product_name_p,))
            product_id_tuple = cursor.fetchone()
        if product_id_tuple is not None:
            id_product = product_id_tuple[0]
            return id_product
        else:
            with CursorFromConnectionFromPool() as cursor:
                some_query = "select id from product where lower(name) = lower(%s)"
                cursor.execute(some_query, (product_name_p,))
                product_id_tuple = cursor.fetchone()
            if product_id_tuple is not None:
                id_product = product_id_tuple[0]
                return id_product
            else:
                return None

                # print("Creating new product ...")
                # id_product, product_name = self.create_new_product(product_name_p)
