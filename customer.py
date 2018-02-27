from database import CursorFromConnectionFromPool


class Customer:
    def __repr__(self):
        pass

    def add_customer(name_place_p):
        name_p, place_p = name_place_p.split('(')
        name_p = name_p.strip()
        place_p = place_p.split(')')[0]
        with CursorFromConnectionFromPool() as cursor:
            some_query = "insert into customer (name, place) values (%s, %s)"
            cursor.execute(some_query, (name_p, place_p))
    @classmethod
    def create_sale_invoice(cls, id_customer_p):
        with CursorFromConnectionFromPool() as cursor:
            some_query = "insert into sale_invoice (customer_id) values (%s) returning id"
            cursor.execute(some_query, (id_customer_p, ))
            sale_invoice_id = cursor.fetchone()[0]

            return sale_invoice_id
    @classmethod
    def get_customer_name_list(cls):
        with CursorFromConnectionFromPool() as cursor:
            some_query = "select name, place from customer"  # same as select * from customer
            cursor.execute(some_query)
            customer_name_tuple = cursor.fetchall()
            new_list = []
            for a in customer_name_tuple:
                new_list.append(a[0] + " (" + a[1] + ")")
            # flat_list = [element for tupl in customer_name_tuple for element in tupl]
            return new_list

    @classmethod
    def get_product_name_list(cls):
        with CursorFromConnectionFromPool() as cursor:
            some_query = "select name from product"  # same as select * from customer
            cursor.execute(some_query)
            customer_name_tuple = cursor.fetchall()
            flat_list = [element for tupl in customer_name_tuple for element in tupl]
            return flat_list

    @classmethod
    def get_customer_id(cls, name_p):
        with CursorFromConnectionFromPool() as cursor:
            some_query = "select id from customer where lower(name) = lower(%s)"
            cursor.execute(some_query, (name_p,))
            customer_id_tuple = cursor.fetchone()
            # print(customer_id_tuple)     # (99, )
            return customer_id_tuple[0]

    @classmethod
    def get_product_id(cls, name_p):
        with CursorFromConnectionFromPool() as cursor:
            some_query = "select id from product where lower(name) = lower(%s)"
            cursor.execute(some_query, (name_p,))
            product_id_tuple = cursor.fetchone()
            return product_id_tuple[0]
    @classmethod
    def get_rate_discount(cls, id_customer_p, id_product_p):
        with CursorFromConnectionFromPool() as cursor:
            some_query = "select rate, discount from customer_product_join " \
                         "where id_customer = %s and id_product = %s"
            cursor.execute(some_query, (id_customer_p, id_product_p))
            rd_id_tuple = cursor.fetchone()
            return rd_id_tuple[0], rd_id_tuple[1]
    @classmethod
    def get_customer_product_rate(cls):
        with CursorFromConnectionFromPool() as cursor:
            some_query = "select from product"  # same as select * from customer
            cursor.execute(some_query)
            customer_name_tuple = cursor.fetchall()
            flat_list = [element for tupl in customer_name_tuple for element in tupl]
            return flat_list
