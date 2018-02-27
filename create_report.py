from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import A4
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from num2words import num2words
import os
import custom_data
pagesize = A4
width, height = pagesize
project_dir = os.path.dirname(os.path.abspath(__file__))
pdf_dir = os.path.join(project_dir, "invoices")
font_path = os.path.join(project_dir, "CarroisGothic-Regular.ttf")
font_path2 = os.path.join(project_dir, "LiberationMono-Bold.ttf")
font_path3 = os.path.join(project_dir, "larabiefont free.ttf")
# pdf_file_name = os.path.join(project_dir, "temp.pdf")
# pdf_file_name = "/Users/python/
#
# /stack/project/temp.pdf"
image_path = os.path.join(project_dir,"some_pic.png")

def reverse_date(i):
    i = i.split("-")
    i = i[2] + "-" + i[1] + "-" + i[0]
    return i


def setup_page(invoice_detail_info_p, invoice_info_p, transactor_name_p, transactor_place_p, customer_details_p,c, memo_type_p):
    freight_p = invoice_info_p[0][29]
    if freight_p is None: freight_p = ""
    customer_gst_p = str(customer_details_p[0])
    if customer_details_p[1] is None:
        address_first_line = ""
    else:
        address_first_line = str(customer_details_p[1])
    if customer_details_p[2] is None:
        address_second_line = ""
    else:
        address_second_line = str(customer_details_p[2])
    if customer_details_p[3] is None:
        address_third_line = ""
    else:
        address_third_line = str(customer_details_p[3])
    if customer_details_p[4] is None:
        contact_no_first = ""
    else:
        contact_no_first = str(customer_details_p[4])
    state_name = custom_data.custom_state
    state_code = custom_data.custom_state_code
    invoice_date = str(invoice_info_p[0][0])
    transport_name = invoice_info_p[0][1]
    transport_lr_no = invoice_info_p[0][2]
    transport_lr_no_of_bags = invoice_info_p[0][3]
    invoice_no = str(invoice_info_p[0][4])
    amount_before_tax = invoice_info_p[0][5]
    # print(amount_before_tax)
    if amount_before_tax is None: amount_before_tax = 0
    # amount_before_tax = amount_before_tax.quantize(Decimal("1.00"))
    cgst9_amount = invoice_info_p[0][6]
    if cgst9_amount is None: cgst9_amount = 0
    # cgst9_amount = cgst9_amount.quantize(Decimal("1.00"))
    sgst9_amount = invoice_info_p[0][7]
    # sgst9_amount = sgst9_amount.quantize(Decimal("1.00"))
    cgst14_amount = invoice_info_p[0][8]
    if cgst14_amount is None: cgst14_amount = 0
    cgst2_5_amount = invoice_info_p[0][13]
    if cgst2_5_amount is None: cgst2_5_amount = 0
    cgst6_amount = invoice_info_p[0][15]
    if cgst6_amount is None: cgst6_amount = 0
    # cgst14_amount = cgst14_amount.quantize(Decimal("1.00"))
    sgst14_amount = invoice_info_p[0][9]
    cgst9_taxable_amount = invoice_info_p[0][10]
    if cgst9_taxable_amount is None: cgst9_taxable_amount = 0
    # cgst9_taxable_amount = cgst9_taxable_amount.quantize(Decimal("1.00"))
    cgst14_taxable_amount = invoice_info_p[0][11]
    if cgst14_taxable_amount is None: cgst14_taxable_amount = 0
    # cgst14_taxable_amount = cgst14_taxable_amount.quantize(Decimal("1.00"))
    cgst2_5_taxable_amount = invoice_info_p[0][17]
    if cgst2_5_taxable_amount is None: cgst2_5_taxable_amount = 0
    cgst6_taxable_amount = invoice_info_p[0][18]
    if cgst6_taxable_amount is None: cgst6_taxable_amount = 0
    total_amount_after_gst = invoice_info_p[0][12]
    # amount_after_gst = amount_after_gst.quantize(Decimal("1.00"))
    site = invoice_info_p[0][19]
    # barcode_font = r"/carrois-gothic/CarroisGothic-Regular.ttf"
    # print(font_path)

    pdfmetrics.registerFont(TTFont("CarroisGothic-Regular", font_path))
    pdfmetrics.registerFont(TTFont("ClassCoder", font_path2))
    pdfmetrics.registerFont(TTFont("larabie", font_path3))
    c.setFillColorRGB(0, 0, 102)
    c.setFont("CarroisGothic-Regular",14,leading=None)
    page_header = "Tax Invoice"

    y1 = 820

    c.setFont("larabie",14,leading=None)
    c.drawCentredString(300, y1, page_header)
    c.setFont("CarroisGothic-Regular",14,leading=None)
    c.setFillColorRGB(0, 0, 0)
    y1 = y1-15
    x = 30
    c.drawString(x, y1, custom_data.custom_name)
    c.setFont("CarroisGothic-Regular", 10, leading=None)
    y1 = y1 - 12
    c.drawString(x, y1, custom_data.custom_address_line_one)
    y1 = y1 - 12
    c.drawString(x, y1, custom_data.custom_address_line_two)
    y1 = y1 - 12
    c.drawString(x, y1, custom_data.custom_contact_no)
    y1 = y1 - 12
    c.setFont("ClassCoder", 10, leading=None)
    c.drawString(x,y1,custom_data.custom_gst_no)
    c.setFont("CarroisGothic-Regular", 12, leading=None)
    print(memo_type_p)
    c.drawString(470, y1+48, "Original / Duplicate")
    if memo_type_p is None:
        c.drawString(480, y1, "Credit Memo")
    elif memo_type_p == "cash":
        c.drawString(480, y1, "Cash Memo")
    y1 = y1 - 1
    c.rect(25, 625, 550, 125, fill=0)      # buyer rectangle
    c.line(337, 625,337, 750) # vertical line in buyer rectangle
    c.line(0, height/2, 10, height/2)
    c.setFont("CarroisGothic-Regular", 10, leading=None)
    c.drawString(35, 730, "Buyer:")
    c.drawRightString(330, 730,transactor_name_p + " (" + transactor_place_p + ")")
    c.drawString(35, 710, "Address:")
    c.drawString(35, 660, "Contact No:")
    c.drawRightString(330, 710, address_first_line)
    c.drawRightString(330, 695, address_second_line)
    c.drawRightString(330, 680, address_third_line)
    c.drawRightString(330, 660, contact_no_first)
    c.drawString(35, 640, "GST IN:")

    c.drawRightString(330, 640, customer_gst_p)
    # c.setFont("CarroisGothic-Regular", 10, leading=None)
    c.drawString(360, 730, "Invoice No:")
    c.drawRightString(550, 730,invoice_no)
    c.drawString(360, 710, "Date:")
    c.drawRightString(550, 710,reverse_date(invoice_date))
    c.drawString(360, 690, "State:")
    c.drawRightString(550, 690, state_name)
    c.drawString(360, 670, "State Code:")
    c.drawString(360, 650, "Place of Supply:")
    c.drawRightString(550, 650, transactor_place_p)
    c.drawRightString(550, 670, state_code)
    c.rect(25, 242, 550, 575, fill=0)  # main rectangle
    # table_heading = "Sr"+ t+"Name" + 7*t +"  HSN"+t+ "Qty" + t + "Unit" + t + "Rate" +\
    #                 t + "Disc"+t+"SGST" + " " +"CGST" + t + "      Amount"
    # c.setFont("Courier",10,leading=None)
    # c.drawString(30, 600, table_heading)
    c.setFont("CarroisGothic-Regular", 10, leading=None)
    c.line(25, 610, 575, 610)  # horizontal line in product table
    table_title_y = 613
    c.drawString(30, table_title_y, "Sr")
    x1,y1,x2,y2 = 45, 625, 45,242
    c.line(x1 + 2, y1, x2 + 2, y2)  # sr line
    c.drawString(x1 + 5, table_title_y, "Product")
    c.line(x1+170, y1, x1+170, y2)    # name
    c.drawRightString(x1 + 205+ 1, table_title_y, "HSN")
    c.line(x1 + 210, y1, x1 + 210, y2)  #hsn
    c.drawRightString(x1 + 255, table_title_y, "Qty")
    c.line(x1 + 260+2, y1, x1 + 260+2, y2) # qty
    c.drawRightString(x1 + 290, table_title_y, "Unit")
    c.line(x1 + 290+2, y1, x1 + 290+2, y2) # unit
    c.drawRightString(x1 + 335, table_title_y, "Rate")
    c.line(x1 + 340+2, y1, x1 + 340+2, y2) #rate
    c.drawRightString(x1 + 375, table_title_y, "Disc")
    c.line(x1 + 380 + 2, y1, x1 + 380 + 2, y2)# discount
    c.drawRightString(x1 + 410, table_title_y, "CGST")
    c.line(x1 + 410 + 2, y1, x1 + 410 + 2, y2) # cgst
    c.drawRightString(x1 + 440, table_title_y, "SGST")
    c.line(x1 + 440 + 2, y1, x1 + 440 + 2, y2)  # sgst
    c.drawRightString(x1 + 465, table_title_y, "IGST")
    c.line(x1 + 465+2, y1, x1 + 465+2, y2) #cgst
    c.drawRightString(x1 + 520, table_title_y, "Amount")
    c.rect(25,222,550,20) #total amt rect
    c.rect(25,122,550,100)# tax calculation
    c.line(387,122,387,102)#grand total vertical
    c.line(387,222,387,122)#tax calculation vertical
    c.setFont("CarroisGothic-Regular", 12, leading=None)
    c.drawString(390, 228, "Sub Total:")  # sub-total
    c.drawRightString(550, 228, str(amount_before_tax)) # sub-total
    c.drawString(30, 205, "GST @ 5%")
    if not cgst2_5_taxable_amount == 0:
        c.drawRightString(190, 205, str(cgst2_5_taxable_amount))
        c.drawRightString(310,205,str(cgst2_5_amount * 2))

    c.drawString(390,205,"Transport:")#transport
    if not freight_p == 0:
        c.drawRightString(550, 205, str(freight_p))
    c.line(25,198,575,198)#transport horizontal
    c.drawString(30, 180, "GST @ 12%")
    if not cgst6_taxable_amount == 0:
        c.drawRightString(190, 180, str(cgst6_taxable_amount))
        c.drawRightString(310, 180, str(cgst6_amount * 2))
    cgst = cgst9_amount + cgst14_amount + cgst2_5_amount + cgst6_amount
    c.drawRightString(550, 180, str(cgst))
    c.drawString(390,180,"CGST:")#cgst
    c.line(25,173,575,173)#cgst horizontal
    c.drawString(30, 155, "GST @ 18%")
    if not cgst9_taxable_amount == 0:
        c.drawRightString(190, 155, str(cgst9_taxable_amount))
        c.drawRightString(310,155,str(cgst9_amount*2))
    c.drawString(390, 155,"SGST:")  # sgst
    c.drawRightString(550, 155, str(cgst))
    c.line(25,148,575,148)#sgst horizontal
    c.drawString(30, 130, "GST @ 28%")
    # print(cgst14_taxable_amount)
    if not cgst14_taxable_amount == 0:
        c.drawRightString(190, 130, str(cgst14_taxable_amount))
        c.drawRightString(310, 130, str(cgst14_amount*2))  # transport
    c.drawString(390, 130, "IGST: ")  # igst
    c.drawString(390, 107, "Grand Total (Rs):")
    # grand_total = amount_before_tax + (cgst * 2)
    # grand_total = round(grand_total)
    c.drawString(30, 88, "Rs. " + num2words(total_amount_after_gst).title())
    c.drawRightString(550, 107,str(total_amount_after_gst))
    c.drawString(30, 227, "Tax Account")
    c.drawString(130, 227, "Taxable Amount")
    c.drawString(250, 227, "Tax Amount")
    c.line(387,242,387,222)#sub total
    c.rect(25, 102, 550, 20) #grand total
    c.rect(25, 82, 550, 20) #in words amt
    c.rect(25, 20, 550, 62)#sign
    c.line(387,82,387,20)
    c.line(25,50,387,50)
    c.drawString(30, 38, custom_data.custom_bank_line_one)
    c.drawString(30, 24, custom_data.custom_bank_line_two)
    c.drawString(30, 70, "Certified that the particulars given above are true and correct")
    c.drawString(30, 55, "Amount of tax subject to reverse charge:")
    c.drawString(400, 70, custom_data.custom_signatory)
    c.drawString(420, 25, "Authorised Signatory")
    # c.drawInlineImage(image_path, 425,35,70,30)
    # mask = [254, 255, 254, 255, 254, 255]
    c.drawImage(image_path, 425,35,70,30,mask='auto')
    c.setFont("CarroisGothic-Regular", 8, leading=None)
    c.drawString(30, 12, "Subject to " + custom_data.custom_city + " Jurisdiction")
    c.setFont("CarroisGothic-Regular", 12, leading=None)
    return c


def create_sale_invoice_detail_csv(invoice_detail_info_p, invoice_info_p, transactor_name_p, transactor_place_p, customer_details_p, memo_type_p):
    print("1. {} 2. {} 3. {} 4. {} 5. {} 6 {}".format(invoice_detail_info_p, invoice_info_p, transactor_name_p, transactor_place_p, customer_details_p, memo_type_p))
    invoice_no = str(invoice_info_p[0][4])
    import os
    pdf_file_name = os.path.join(pdf_dir, invoice_no + ".pdf")
    c = canvas.Canvas(pdf_file_name, pagesize=A4)
    setup_page(invoice_detail_info_p, invoice_info_p, transactor_name_p, transactor_place_p, customer_details_p,c, memo_type_p)
    i_co = 1
    x_co = 45
    y_co = 595

    for a in invoice_detail_info_p:
        c.setFont("CarroisGothic-Regular", 10, leading=None)
        # print(a)
        c.drawRightString(45, y_co, str(i_co))                  # sr
        # c.drawString(x + 15, y, str(a[0]))
        c.drawString(x_co+5, y_co, str(a[1]))          # name
        if str(a[8]) == "None":
            c.drawRightString(x_co + 205, y_co, "")  # hsn
        else:
            c.drawRightString(x_co + 205, y_co, str(a[8]))            # hsn
        c.drawRightString(x_co + 260, y_co, str(a[2])) # qty
        c.drawRightString(x_co + 290, y_co, str(a[3]))    # unit
        c.drawRightString(x_co + 340, y_co, str(a[4]))    # rate

        if a[5] == 0.00:
            temp = ""
        else:
            temp = str(a[5])
        c.drawRightString(x_co + 380, y_co, str(temp))    # disc
        c.drawRightString(x_co + 410, y_co, str(a[9]))    # cgst
        c.drawRightString(x_co + 440, y_co, str(a[9]))  # sgst
        c.drawRightString(x_co + 465, y_co, "")  # igst
        c.drawRightString(x_co + 525, y_co, str(a[7]))    # amount
        i_co += 1
        y_co -= 15
        if y_co < 250:
            c.showPage()
            y_co = 595
            c = setup_page(invoice_detail_info_p, invoice_info_p, transactor_name_p, transactor_place_p, customer_details_p, c, memo_type_p)
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
from decimal import Decimal
import datetime
# i = [(471, 'Turbo Short Body', Decimal('10'), 'Nos', Decimal('93'), Decimal('0'), Decimal('93.00'), Decimal('930.00'), '8708', Decimal('9'), Decimal('83.70'), Decimal('83.70'), None, 463), (481, 'Society Short Body', Decimal('10'), 'Nos', Decimal('135'), Decimal('0'), Decimal('135.00'), Decimal('1350.00'), None, Decimal('14'), Decimal('189.00'), Decimal('189.00'), None, 534)]
# y = [("", None, None, None, Decimal('1'), Decimal('2280'), Decimal('84'), Decimal('84'), Decimal('189'), Decimal('189'), Decimal('930'), Decimal('1350'), None, None)]




'''

            some_query = "select id,
                            10
                         " from sale_invoice_detail " \
                         "where id_sale_invoice = %s order by id asc"
                         '''
x = [(3001, 'Wall Mixer', Decimal('3.00'), 'Nos', Decimal('950.00'), Decimal('0.00'), Decimal('950.00'), Decimal('2850.00'), '8481', Decimal('9'), Decimal('256.50'), Decimal('256.50'), Decimal('3363'), 4405, 833, Decimal('0')), (3002, 'Wall Mixer H', Decimal('10.00'), 'Nos', Decimal('1281.50'), Decimal('0.00'), Decimal('1281.50'), Decimal('12815.00'), '8481', Decimal('9.0'), Decimal('1153.35'), Decimal('1153.35'), Decimal('15122'), 4897, 833, Decimal('0')), (3003, 'Lift Cock', Decimal('12.00'), 'Nos', Decimal('110.00'), Decimal('0.00'), Decimal('110.00'), Decimal('1320.00'), '8481', Decimal('9.0'), Decimal('118.80'), Decimal('118.80'), Decimal('1558'), 5000, 833, Decimal('0')), (3004, 'Shower', Decimal('10.00'), 'Nos', Decimal('140.00'), Decimal('0.00'), Decimal('140.00'), Decimal('1400.00'), '8481', Decimal('9'), Decimal('126.00'), Decimal('126.00'), Decimal('1652'), 4611, 833, Decimal('0')), (3005, 'Health Faucet Set', Decimal('6.00'), 'Nos', Decimal('280.00'), Decimal('0.00'), Decimal('280.00'), Decimal('1680.00'), '8481', Decimal('9'), Decimal('151.20'), Decimal('151.20'), Decimal('1982'), 4825, 833, Decimal('0')), (3007, 'Washer', Decimal('10.00'), 'Nos', Decimal('10.00'), Decimal('0.00'), Decimal('10.00'), Decimal('100.00'), '8481', Decimal('9'), Decimal('9.00'), Decimal('9.00'), Decimal('118'), 4816, 833, Decimal('0')), (3008, 'Ball Valve H 15', Decimal('4.00'), 'Nos', Decimal('125.00'), Decimal('0.00'), Decimal('125.00'), Decimal('500.00'), '8481', Decimal('9'), Decimal('45.00'), Decimal('45.00'), Decimal('590'), 4695, 833, Decimal('0')), (3009, 'Short Body', Decimal('9.00'), 'Nos', Decimal('190.00'), Decimal('0.00'), Decimal('190.00'), Decimal('1710.00'), '8481', Decimal('9'), Decimal('153.90'), Decimal('153.90'), Decimal('2018'), 4491, 833, Decimal('0'))]
y = [(datetime.date(2017, 10, 4), None, None, None, Decimal('330'), Decimal('22375.00'), Decimal('2018.70'), Decimal('2018.70'), Decimal('0.00'), Decimal('0.00'), Decimal('22430.00'), Decimal('0.00'), Decimal('26467'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), None, Decimal('0.00'), Decimal('0.00'), Decimal('4.95'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), Decimal('0.00'), 114, Decimal('55.00'))]
z = "Krishna Sanitary"
a = "Satara"
b = ('27AOGPP5984C1ZM', '', '', '', '9975487787')
# create_sale_invoice_detail_csv(x,y,z,a,b,None)
