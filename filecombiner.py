#--------------------------------------------------------------------------------------------------------------------------
#**************************************************************************************************************************
# BMS File Combiner
# GUI Version
# V1.0
#**************************************************************************************************************************
#--------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------
# Gen Imports
#--------------------------------------------------------------------------------------------------------------------------
import os, glob, sys, time, openpyxl
from numpy import NaN
import base64, io

# Plotly, Pandas, and Steamlight Imports
#--------------------------------------------------------------------------------------------------------------------------
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd
from pandas.io.pytables import Table
import streamlit as st

#--------------------------------------------------------------------------------------------------------------------------
# Setup
#--------------------------------------------------------------------------------------------------------------------------
df = pd.DataFrame() # dataframe for the Panda CSV import

# Main
#--------------------------------------------------------------------------------------------------------------------------
#icon emojis https://webfx.com/tools/emoji-cheat-sheet
st.set_page_config(
                    page_title="BMS File Combiner - FP",
                    page_icon=":arrow_down:"
)
# Show Fortress Logo
header_image_html = "<img src='fortress_logo.png' class='img-fluid' width='50%'>"
st.markdown(header_image_html, unsafe_allow_html=True)

st.title('BMS Data File Combiner')

# Instructions
with st.expander("Instructions"):
     st.markdown("""First upload a CSV file containing individul recorded data files from the BMS software, then provide a title and sampling rate (default is to keep all rows)
     """)
# file uploader
st.header('CSV Upload')

#Choose battery type
batt_type = st.selectbox(
         'Battery Type',
         ('eFlex', 'eVault Max', 'eVault Classic'))

uploaded_files = None
#If battery isn't eflex ask for serial number before allowing file upload
if batt_type != 'eFlex':
    serial_num = st.text_input("Enter your battery serial number: ")
    software_version = st.text_input("Enter your battery software version: ")
    if serial_num and software_version: #make sure serial num and software version are filled
        if batt_type == 'eVault Max': #if eVault Max accept single csv upload
            uploaded_files = st.file_uploader("Choose a file", type= ["csv"], accept_multiple_files=False)
        else: #if eVault Classic accept single xls upload
            uploaded_files = st.file_uploader("Choose a file", type = ["xls","xlsx"], accept_multiple_files=False)
else: #if eflex accept multiple csv files
    uploaded_files = st.file_uploader("Choose a file", type= ["csv"], accept_multiple_files=True)

# Main Window
#-------------------------------------------------------------------------------------------------------------------------- 

concatenated_df = pd.DataFrame()

if uploaded_files:

    if batt_type == 'eFlex':
        sorted_files = sorted(uploaded_files, key=lambda x: x.name) #sort the order of the uploaded files to go from the lowest number to the highest
        upload_file_df = (pd.read_csv(userFile) for userFile in sorted_files) #read in each uploaded file (in proper order) as a panda dataframe    
        concatenated_df = pd.concat(upload_file_df, ignore_index=True) #append each file into a single data frame and save it to a variable
        #concatenated_df['Battery ID'] = concatenated_df['Battery ID'].str[1:-1]
        #concatenated_df['Battery ID'] = concatenated_df['Battery ID'].str[1:-1]
        concatenated_df.insert(concatenated_df.columns.get_loc('Temperature(?) #6') + 1, 'Temperature(?) #7', 0) #insert row of zeroes for temperature sensor 7 after column for temp 6
        concatenated_df.insert(concatenated_df.columns.get_loc('Temperature(?) #7') + 1, 'Temperature(?) #8', 0) #insert row of zeroes for temperature sensor 8 after column for temp 7
        serial_num = str(concatenated_df['Battery ID'][0])
        concatenated_df['Unit Current'] = concatenated_df['Unit Current'].abs()
        concatenated_df['Unit Current'] = concatenated_df['Unit Current'].abs()

    elif batt_type == 'eVault Max':
        concatenated_df = pd.read_csv(uploaded_files)
        #Remap columns so that they work with plotting
        column_mapping = {}
        for i in range(0,16):
            column_mapping.update({'Volt' + str(i+1) : 'Cell' + str(i+1)}) #remap cell voltage fields
        for j in range(0, 8):
            column_mapping.update({'Temp' + str(j+1) : 'Temperature(?) #' + str(j+1)}) #remap temperature fields
        column_mapping.update({'SumVolt':'Unit Voltage', 'Curr':'Unit Current', 'SOC':'Unit SOC', 'DischargeRelay':'Discharge Relay Status'})    

        concatenated_df.rename(column_mapping, axis = 1, inplace= True) #update column names of data frame
        concatenated_df['Battery ID'] = " " + serial_num + " "#Add BatteryID and software version required column names
        concatenated_df['Battery ID'] = " " + serial_num + " "#Add BatteryID and software version required column names
        concatenated_df['Software Version'] = software_version
        concatenated_df['Unit Current'] = concatenated_df['Unit Current'].abs()
        concatenated_df['Unit Current'] = concatenated_df['Unit Current'].abs()

    else :
        #evault classic data uploaded as xls
        concatenated_df = pd.read_excel(uploaded_files)
        column_mapping = {}
        for i in range(0,16):
            column_mapping.update({'CELL' + str(i+1) : 'Cell' + str(i+1)}) #remap cell voltage fields
        for j in range(0, 6):
            column_mapping.update({'TEMP' + str(j+1) : 'Temperature(?) #' + str(j+1)}) #remap temperature fields
        column_mapping.update({'CELL_SUM':'Unit Voltage', 'Current':'Unit Current', 'SOC':'Unit SOC', 'DischargeRelay':'Discharge Relay Status'}) #add rest of required fields to column mapping

        concatenated_df.rename(column_mapping, axis = 1, inplace= True) #update column names of data frame

        concatenated_df.insert(concatenated_df.columns.get_loc('Temperature(?) #6') + 1, 'Temperature(?) #7', 0) #insert row of zeroes for temperature sensor 7 after column for temp 6
        concatenated_df.insert(concatenated_df.columns.get_loc('Temperature(?) #7') + 1, 'Temperature(?) #8', 0) #insert row of zeroes for temperature sensor 8 after column for temp 7
        concatenated_df['Battery ID'] = serial_num #Add BatteryID and software version required column names
        concatenated_df['Software Version'] = software_version
        concatenated_df['Unit SOC'] = 0 #Add temporary unit SOC and discharge relay status as they are required field
        concatenated_df['Discharge Relay Status'] = "NA"
        concatenated_df['Charge Relay Status'] = "NA"
        concatenated_df['Unit Current'] = concatenated_df['Unit Current'].abs()

    st.markdown("---")
    st.header('Options')
    file_name = st.text_input('File Output Name', value= batt_type + '-'+ serial_num +'.csv')
    st.caption('File format must be csv')
    s_rate = 1
    if batt_type == 'eFlex' :
        s_rate = st.number_input('Sampling Rate (in seconds)', min_value=1, max_value=None, value=1) # the number of lines between samples
    st.caption('eFlex and eVault Max files recordings default to 1 row/sec, while eVault Classic is configurable. Ex. To sample eFlex at a 5min interval set rate to 300')

    name_type = "" # kind of file type imported
    
    if batt_type == "eVault Classic":
        sep_value = '\t'
        name_type = "/*.xls"
    elif batt_type == "eFlex" or batt_type == "eVault Max":
        sep_value = ','
        name_type = "/*.csv"
    
    if file_name != "":
                
        total_file_len = concatenated_df.shape[0] # get the number of rows in our new file
        if batt_type == "eFlex":
            if s_rate > total_file_len: #check to see if the sampling rate is too high and let the user know
                st.error("Sampling rate is greater than the total file length, please enter a lower number")
        
        sampled_df = concatenated_df.iloc[::int(s_rate)].reset_index(drop=True) #sample the file at the rate defined by the user
        downloadFile = sampled_df.to_csv(index=False).encode('utf-8') #convert the final file to a UTF8 CSV
        sampled_file_len = sampled_df.shape[0] # get the number of rows in our new file

        #csv = export_CSV(df)
        st.markdown("---")            
        st.header('File Preview')
        st.text("Number of Rows in Input: "+str(total_file_len))
        st.text("Number of Rows in Output: "+str(sampled_file_len))
        st.write(sampled_df.iloc[0:5]) #write the preview table
        st.markdown("---")
        st.download_button(
                label="Download data as CSV",
                file_name=file_name,
                data=downloadFile,
                mime='text/csv'
        )