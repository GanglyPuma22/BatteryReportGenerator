from distutils.command.upload import upload
from email.policy import default
import streamlit as st
import pandas as pd
import zipfile
from io import StringIO
from reportlab.pdfgen import canvas
from reportlab.pdfbase.pdfmetrics import stringWidth
from reportlab.platypus.tables import Table
from reportlab.lib import colors
from reportlab.rl_config import defaultPageSize
from PIL import Image 
from reportlab.lib.utils import ImageReader

#Variables used to center elements and deal with text layout
PAGE_WIDTH = defaultPageSize[0]
PAGE_HEIGHT = defaultPageSize[1]
small_text_size = 14
large_text_size = 20

#global variable used to keep track of height where we draw text and images in the pdf
currentHeight = PAGE_HEIGHT

#Function updates global variable currentHieght, outputs where to draw element. 
#Inputs: gap indicates how much vertical space you want between last drawn element and next one
def updateHeight(gap):
    global currentHeight
    currentHeight = currentHeight - gap
    return currentHeight

#Streamlit Page Beginning
st.title('PDF Report Generator')

# Instructions
with st.expander("Usage Tips"):
     st.markdown("""Upload a zip folder created by the BatteryPlots app to automatically create a pdf of the 
     RMA Battery Tests. No need to extract any files. Optionally upload pngs, jpegs, and jpgs of images you want to include them in an appendix section of your report
     """)

#Store uploaded zip file
uploaded_zip = st.file_uploader('Upload a zip folder* from Battery Plots and optional appendix images', type=["zip", "png", "jpg", "jpeg"], accept_multiple_files=True) 

#Initialize variables that will store charging and discharging data and plots
df_charging = None
df_discharging = None
dischargeImageZip = None
chargeImageZip = None
appendixImages = []
zipFilePresent = False

if (uploaded_zip is not None): #make sure zip file was uploaded
    for file in uploaded_zip:
        print(file.type)
        if "zip" in file.type:
            zf = zipfile.ZipFile(file)
            zipFilePresent = True
            for name in zf.namelist():
                rawData = zf.open(name)
                if (name[-3:len(name)] == 'csv'):
                    if "Discharge" in name:
                        df_discharging = pd.read_csv(rawData)
                    elif "Charge" in name:
                        df_charging = pd.read_csv(rawData)
                    else:
                        st.error("The csv files' names in the zip folder need to contain Charge an Discharge respectively.")
                elif (name[-3:len(name)] == 'png'):
                    if "Discharge" in name:
                        dischargeImageZip = Image.open(rawData)
                    elif "Charge" in name:
                        chargeImageZip = Image.open(rawData)
                    else:
                        st.error("The png files' names in the zip folder need to contain Charge an Discharge respectively.")
        elif "png" in file.type or "jpeg" in file.type:
            appendixImages.append(file)
            print(len(appendixImages))



if zipFilePresent:
        c = canvas.Canvas("generatedBatteryTestReport.pdf")
        c.setFont("Helvetica-Bold", large_text_size)
        c.drawString((PAGE_WIDTH - stringWidth("RMA Battery Test Report", "Helvetica-Bold", large_text_size)) / 2.0, PAGE_HEIGHT - 90, "RMA Battery Test Report")
        data = None

        #Fill out data in first table automatically if battery csv was uploaded
        if df_charging is not None:
            data = [['Serial Number', df_charging['Battery ID'][0]],
                ['Incoming Software', df_charging['Software Version'][0]],
                ['Outgoing Software', ''],
                ['Support Ticket Reference:', ''],
                ['Notes', 'details'],
                ['','']]
        else:
            data=  [['Serial Number', ''],
                ['Incoming Software', ''],
                ['Outgoing Software', ''],
                ['Support Ticket Reference:', ''],
                ['Notes', 'details'],
                ['','']]

        #Specify table formatting
        t=Table(data, colWidths=2*PAGE_WIDTH/5, rowHeights = 25, style = [('GRID',(0,0),(-1,-1),1,colors.black), 
        ('SPAN',(-2,-2),(-1,-1)), 
        ('VALIGN', (0,0), (-1,-1), "TOP"),
        ('FONTNAME', (-2,-2), (-2,-2), "Helvetica-Bold"),
        ('FONTNAME', (1,0), (1,0), "Helvetica-Bold"),
        ('FONTSIZE', (0,0), (-1,-1), small_text_size)])
        w,h = t.wrapOn(c, 4*PAGE_WIDTH/5, 125)
        tableHeight = PAGE_HEIGHT - 2*h + 30
        t.drawOn(c, (PAGE_WIDTH - 4*PAGE_WIDTH/5) / 2.0, tableHeight) #draw table
        
        #Fill out text between tables
        c.drawString((PAGE_WIDTH - stringWidth("Cycle Test Report", "Helvetica-Bold", large_text_size)) / 2.0, tableHeight - 40, "Cycle Test Report")
        c.setFont("Helvetica", small_text_size)
        cycle_string = "charge and discharge test at 0.5C or less, with a >15min rest period between tests"
        c.drawString((PAGE_WIDTH - stringWidth(cycle_string, "Helvetica", small_text_size)) / 2.0, tableHeight - 40 - 25, cycle_string)
        c.setFont("Helvetica-Bold", large_text_size - 2)
        c.drawString((PAGE_WIDTH - stringWidth("Test Grading", "Helvetica-Bold", large_text_size - 2)) / 2.0, tableHeight - 40 - 80, "Test Grading")

        #Specify format and draw second table
        data2 = [['Test Engineer', ''],['',''],['',''],['',''],['','']]

        secondt=Table(data2, colWidths=2*PAGE_WIDTH/5, rowHeights = 25, style = [('GRID',(0,0),(-1,-1),1,colors.black),  
        ('VALIGN', (0,0), (-1,-1), "TOP"),
        ('FONTNAME', (0,0), (-1,-1), "Helvetica"),
        ('FONTNAME', (1,0), (1,0), "Helvetica-Bold"),
        ('FONTSIZE', (0,0), (-1,-1), small_text_size)])

        secondw,secondh = secondt.wrapOn(c, 4*PAGE_WIDTH/5, 125)
        secondTableHeight = tableHeight - 120 - secondh - 10
        secondt.drawOn(c, (PAGE_WIDTH - 4*PAGE_WIDTH/5) / 2.0, secondTableHeight)

        #Start on new page for Discharge Test Stuff
        c.showPage()
        c.setFont("Helvetica-Bold", 16)
        c.drawString((PAGE_WIDTH - stringWidth("Discharge Testing", "Helvetica-Bold", 16)) / 2.0, updateHeight(60), "Discharge Testing")
        left_allign_pos = 20
        text_gap = 20
        #Fill out starting value information first
        c.setFont("Helvetica-Bold", small_text_size)
        c.drawString(left_allign_pos,updateHeight(text_gap), "Starting Values")
        c.setFont("Helvetica", small_text_size)
        c.drawString(left_allign_pos,updateHeight(text_gap), "Voltage: " + str(df_discharging['Unit Voltage'][0]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "SOC: " + str(df_discharging['Unit SOC'][0]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "Discharge Current: " + str(df_discharging['Unit Current'][0]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "Test Start Date: ")
        c.drawString(left_allign_pos,updateHeight(text_gap), "Test Start Time: " + str(df_discharging['Time'][0]))

        #Fill out ending values
        endingIndex = len(df_discharging.index) - 1
        c.setFont("Helvetica-Bold", small_text_size)
        c.drawString(left_allign_pos, updateHeight(text_gap * 2), "Ending Values")
        c.setFont("Helvetica", small_text_size)
        c.drawString(left_allign_pos,updateHeight(text_gap), "Voltage: " + str(df_discharging['Unit Voltage'][endingIndex]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "SOC: " + str(df_discharging['Unit SOC'][endingIndex]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "Discharge Current: " + str(df_discharging['Unit Current'][endingIndex]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "Test End Date: ")
        c.drawString(left_allign_pos,updateHeight(text_gap), "Test End Time: " + str(df_discharging['Time'][endingIndex]))

        c.setFont("Helvetica-Bold", large_text_size - 2)
        c.drawString(left_allign_pos, updateHeight(text_gap  * 2), "Discharge Test Graph")

        #Draw uploaded image of discharge graph
        if dischargeImageZip:
            dischargeWidth, dischargeHeight = dischargeImageZip.size
            #Open uploaded image with PIL and read it into pdf
            c.drawImage(ImageReader(dischargeImageZip), (PAGE_WIDTH - dischargeWidth/1.3) / 2.0, updateHeight(dischargeHeight/1.3 + text_gap), width = dischargeWidth/1.3, height = dischargeHeight/1.3)
        #Start on new page for Charge Test Stuff
        c.showPage()
        currentHeight = PAGE_HEIGHT #Reset current height on new page
        c.setFont("Helvetica-Bold", 16)
        c.drawString((PAGE_WIDTH - stringWidth("Charge Testing", "Helvetica-Bold", 16)) / 2.0, updateHeight(60), "Charge Testing")
        left_allign_pos = 20
        text_gap = 20
        #Fill out starting value information first
        c.setFont("Helvetica-Bold", small_text_size)
        c.drawString(left_allign_pos,updateHeight(text_gap), "Starting Values")
        c.setFont("Helvetica", small_text_size)
        c.drawString(left_allign_pos,updateHeight(text_gap), "Voltage: " + str(df_charging['Unit Voltage'][0]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "SOC: " + str(df_charging['Unit SOC'][0]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "Discharge Current: " + str(df_charging['Unit Current'][0]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "Test Start Date: ")
        c.drawString(left_allign_pos,updateHeight(text_gap), "Test Start Time: " + str(df_charging['Time'][0]))

        #Fill out ending values
        endingIndex = len(df_charging.index) - 1
        c.setFont("Helvetica-Bold", small_text_size)
        c.drawString(left_allign_pos, updateHeight(text_gap * 2), "Ending Values")
        c.setFont("Helvetica", small_text_size)
        c.drawString(left_allign_pos,updateHeight(text_gap), "Voltage: " + str(df_charging['Unit Voltage'][endingIndex]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "SOC: " + str(df_charging['Unit SOC'][endingIndex]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "Discharge Current: " + str(df_charging['Unit Current'][endingIndex]))
        c.drawString(left_allign_pos,updateHeight(text_gap), "Test End Date: ")
        c.drawString(left_allign_pos,updateHeight(text_gap), "Test End Time: " + str(df_charging['Time'][endingIndex]))

        c.setFont("Helvetica-Bold", large_text_size - 2)
        c.drawString(left_allign_pos, updateHeight(text_gap  * 2), "Charge Test Graph")

        if chargeImageZip:
            chargeWidth, chargeHeight = chargeImageZip.size
            #Open uploaded image with PIL and read it into pdf
            c.drawImage(ImageReader(chargeImageZip), (PAGE_WIDTH - chargeWidth/1.3) / 2.0, updateHeight(chargeHeight/1.3 + text_gap), width = chargeWidth/1.3, height = chargeHeight/1.3)
        
        if (len(appendixImages) > 0): #Block takes care of drawing all appendix images
            c.showPage()
            currentHeight = PAGE_HEIGHT
            c.setFont("Helvetica-Bold", large_text_size)
            c.drawString((PAGE_WIDTH - stringWidth("Charge Testing", "Helvetica-Bold", 16)) / 2.0, updateHeight(60), "Appendix")
            for img in appendixImages: #img is the uploaded file that is png or jpg
                image = Image.open(img) #image is of type png when opened
                imgWidth, imgHeight = image.size
                aspectRatio = imgWidth / imgHeight
                if aspectRatio > 1: 
                    if imgWidth > PAGE_WIDTH : #Conserve aspect ratio of image when it is too wide 
                        imgWidth = PAGE_WIDTH
                        imgHeight = imgWidth / aspectRatio
                else :
                    if imgHeight > PAGE_HEIGHT: #Conserve aspect ratio of image when it is too high 
                        imgHeight = PAGE_HEIGHT
                        imgWidth = aspectRatio * imgHeight

                if updateHeight(0) - imgHeight - small_text_size< 0: #If image will not fit on the screen make new page
                    c.showPage()
                    currentHeight = PAGE_HEIGHT

                c.setFont("Helvetica-Bold", small_text_size) #Write image name above it
                c.drawString(left_allign_pos, updateHeight(text_gap), img.name)
                c.drawImage(ImageReader(image), (PAGE_WIDTH - imgWidth/1.3) / 2.0, updateHeight(imgHeight/1.3 + text_gap), width = imgWidth/1.3, height = imgHeight/1.3)


        fileName = "generatedReport.pdf"
        if df_charging is not None: #If zip file was uploaded use its name for pdf name, it will be 'battery type - serial number'
            for file in uploaded_zip:
                if ".zip" in file.type:
                    fileName = "Battery_Report_" + uploaded_zip.name.replace('.zip', '.pdf')

        #After we process the files and create a pdf dowload it
        st.download_button("Dowload battery report pdf", c.getpdfdata(), file_name=fileName)