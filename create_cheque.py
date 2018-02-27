from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from num2words import num2words
import os





project_dir = os.path.dirname(os.path.abspath(__file__))
font_path = os.path.join(project_dir, "CarroisGothic-Regular.ttf")
font_cursive_path = os.path.join(project_dir, "Allura-Regular.ttf")
font_micr_path = os.path.join(project_dir, "bitwise.ttf")
pdf_file_name = os.path.join(project_dir, "cheque.pdf")
# pdf_file_name = "/Users/python/projects/stack/project/temp.pdf"

def cheque_print(payee_name, amount, cheque_date):
    page_width = 576
    page_height = 265


    pdfmetrics.registerFont(TTFont("CarroisGothic-Regular", font_path))
    pdfmetrics.registerFont(TTFont("Allura-Regular", font_cursive_path))
    pdfmetrics.registerFont(TTFont("bitwise", font_micr_path))
    c = canvas.Canvas(pdf_file_name, pagesize=(page_width, page_height))
    # c.setFont("CarroisGothic-Regular",10,leading=None)
    c.setFont("bitwise",10,leading=None)
    date_start = 434
    date_distance = 14.17
    c.drawString(date_start, 229, cheque_date[0])
    c.drawString(date_start + date_distance, 229, cheque_date[1])
    c.drawString(date_start + (date_distance*2), 229, cheque_date[3])
    c.drawString(date_start + (date_distance * 3), 229, cheque_date[4])
    c.drawString(date_start + (date_distance * 4), 229, cheque_date[6])
    c.drawString(date_start + (date_distance * 5), 229, cheque_date[7])
    c.drawString(date_start + (date_distance * 6), 229, cheque_date[8])
    c.drawString(date_start + (date_distance * 7), 229, cheque_date[9])
    c.setFont("Allura-Regular", 24, leading=None)
    c.drawString(57, 190, payee_name)
    print("a is {}".format(amount))
    amount = int(amount)
    amount_words = num2words(amount).title()+" Only"
    print("length is {}".format(len(amount_words)))
    if len(amount_words) > 48:
        c.setFont("Allura-Regular", 18, leading=None)
    c.drawString(57, 165, amount_words)
    c.setFont("bitwise", 18, leading=None)
    # c.setFont("Allura-Regular", 24, leading=None)
    c.drawString(440, 140, str(str(amount))+ ".00")
    c.showPage()
    c.save()
    try:
        import os
        if os.name == "nt":
            os.system('start ' + pdf_file_name)
        else:
            os.system('open ' + pdf_file_name)
        # subprocess.Popen(pdf_file_name)
    except Exception as e:
        print(e)

# cheque_print("Chintamani Transport Services", 26550, "15.08.2017")