from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from decimal import Decimal
from _datetime import *
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.lib.pagesizes import landscape
from reportlab.platypus import Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.platypus import (
    BaseDocTemplate,
    PageTemplate,
    Frame,
    Paragraph
)
from num2words import num2words
import os
pagesize = A4
width, height = pagesize


project_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(project_dir, "CarroisGothic-Regular.ttf")
pdf_file_name = os.path.join(project_dir, "ledger.pdf")


def reverse_date(i):
    i = i.split("-")
    i = i[2] + "-" + i[1] + "-"+ i[0]
    return i


def setup_page(c, name_p, place_p):
    x1 = 35
    y1 = 800
    c.drawString(200, y1, name_p + " (" + place_p + ")")
    c.drawString(x1, y1-50, "Date")
    c.drawRightString(x1+200, y1-50, "Bill")
    c.drawRightString(x1+300, y1-50, "Receipt")
    c.drawRightString(x1+400, y1-50, "Balance")
    return c


def create_sale_ledger(ledger_info_p, name_p, place_p):
    c = canvas.Canvas(pdf_file_name, pagesize=A4)
    setup_page(c, name_p, place_p)

    # i_co = 1
    x_co = 35
    y_co = 730

    for a in ledger_info_p:
        bill_amount = str(a[1])
        if bill_amount == "None":
            bill_amount = ""
        receipt_amount = str(a[2])
        if receipt_amount == "None":
            receipt_amount = ""




        # c.setFont("CarroisGothic-Regular", 10, leading=None)
        c.drawString(x_co, y_co, str(a[0]))
        c.drawRightString(x_co+200, y_co, bill_amount)
        c.drawRightString(x_co+300, y_co, receipt_amount)
        c.drawRightString(x_co+400, y_co, str(a[3]))
        y_co -= 15
        if y_co < 250:
            c.showPage()
            y_co = 595
            c = setup_page()
    c.showPage()
    c.save()
    try:
        from sys import platform
        import os
        if platform == "linux" or platform == "linux2":
            os.system('xdg-open ' + pdf_file_name)
        elif platform == "darwin":
            os.system('open ' + pdf_file_name)
        elif platform == "win32":
            os.system('start ' + pdf_file_name)
            # subprocess.Popen(pdf_file_name)
    except Exception as e:
        print(e)
# some_query = [('12.07.2017', Decimal('20195'), None, Decimal('20195'), 134, 'sale', 405, None, 29), ('22.07.2017', None, Decimal('2'), Decimal('20193'), 201, 'receipt', None, 40, 29)]
# create_sale_ledger(some_query)
