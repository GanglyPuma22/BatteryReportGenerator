#--------------------------------------------------------------------------------------------------------------------------
#**************************************************************************************************************************
# BatteryPlots
# GUI Version
# V1.0
#**************************************************************************************************************************
#--------------------------------------------------------------------------------------------------------------------------

#--------------------------------------------------------------------------------------------------------------------------
# Gen Imports
#--------------------------------------------------------------------------------------------------------------------------
from distutils.command.upload import upload
from queue import Empty
import unittest
import numpy as np
import pandas as pd
from pandas.io.pytables import Table
import zipfile
import os, glob, sys, time
from pathlib import Path

import base64
import io

# Plotly and Steamlight Imports
#--------------------------------------------------------------------------------------------------------------------------
import plotly.graph_objects as go
import plotly.express as px
import plotly.express as px
from plotly.subplots import make_subplots
import streamlit as st


#--------------------------------------------------------------------------------------------------------------------------
# Basic App
#--------------------------------------------------------------------------------------------------------------------------
df = pd.DataFrame() # dataframe for the Panda CSV import

figure = [] #Initialize data object to store figures as they are created

#Load only the required data columes to reduce memory consumption
req_cols = [
            'Time','Unit Voltage', 'Unit Current', 'Battery ID', 'Unit SOC', 'Discharge Relay Status', 'Charge Relay Status', 'Software Version',
            'Time','Unit Voltage', 'Unit Current', 'Battery ID', 'Unit SOC', 'Discharge Relay Status', 'Charge Relay Status', 'Software Version',
            'Cell1', 'Cell2', 'Cell3', 'Cell4', 'Cell5', 'Cell6', 'Cell7', 'Cell8',
            'Cell9', 'Cell10', 'Cell11', 'Cell12', 'Cell13', 'Cell14', 'Cell15', 'Cell16',
            'Temperature(?) #1', 'Temperature(?) #2', 'Temperature(?) #3', 'Temperature(?) #4', 'Temperature(?) #5', 'Temperature(?) #6', 'Temperature(?) #7', 'Temperature(?) #8'
]

#function to create a box annotation
def createBoxAnnotation(figName, xPos, yPos, textData):
    figName.add_annotation(x=xPos, y=yPos,
         xanchor="center",
         yanchor="middle",
         text= textData,
         showarrow=True,
         font=dict(
             family="Verdana, sans-serif",
             size=12,
             color="#000"
         ),
         align="center",
         arrowhead=2,
         arrowsize=1,
         arrowwidth=2,
         arrowcolor="#636363",
         ax=70,
         ay=50,
         bordercolor="#c7c7c7",
         borderwidth=2,
         borderpad=4,
         bgcolor="#fff",
         opacity=1
         )

def createAnnotationGraph(figToUpdate, xPos, yPos, textInp) :
    figToUpdate.add_annotation(x = xPos, y=yPos,
                        text=textInp,
                        showarrow=True,
                        font=dict(
                            family="Verdana, sans-serif",
                            size=12,
                            color="#000"
                        ),
                        align="center",
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=2,
                        arrowcolor="#636363",
                        ax=150,
                        ay=30,
                        bordercolor="#c7c7c7",
                        borderwidth=2,
                        borderpad=4,
                        bgcolor="#fff",
                        opacity=1
                        )

#Helper function that handles creating the graph and the title of the graph, appends it to figure for display
def createChargeAndDischarge(df, data_type) :
    unitVIFig = make_subplots(specs=[[{"secondary_y": True}]]) 
    unitVIFig = createVIGraph(df, unitVIFig, data_type) #create graph from 
    unitVIFig.update_layout(title_text="Battery Voltage and Current - Unit Ser#: " + str(df['Battery ID'][0]) + "<br><sup>Firmware V"+str(df['Software Version'][0])+" - " + data_type, hovermode="x unified")

    relayIndex = relayBreak(df[data_type + ' Relay Status'])
    if not relayIndex < 0 :
        st.text(data_type + " Relay Open at: " + df['Time'][relayIndex])

    st.plotly_chart(unitVIFig) #plot charge data
    figure.append(unitVIFig)


#function to create the voltage and current graph
def createVIGraph(dataFrame, unitVIFig, data_type):
    #Deal with data inputs
    graphPlaceholder.empty()

    #Initialize voltage Data as single column dataFrame full of zeroes
    unitVoltageData = pd.DataFrame(0, index=np.arange(len(dataFrame.index)), columns=['Unit Voltage'])

    #Compute voltage data by summing individual cell voltages
    for i in range(1,17):
        unitVoltageData['Unit Voltage'] = pd.to_numeric(unitVoltageData['Unit Voltage']) + pd.to_numeric(dataFrame['Cell' + str(i)])
   
    #Leave value at mV precision
    unitVoltageData['Unit Voltage'] = [int(x) / 1000.0 for x in unitVoltageData['Unit Voltage']]
    unitCurrentData = dataFrame['Unit Current'].abs()

    #Batt Voltage Min/Max
    Vmax = max(unitVoltageData['Unit Voltage'])
    Vmin = min(unitVoltageData['Unit Voltage'])

    # Add traces
    unitVIFig.add_trace(go.Scatter(x=dataFrame['Time'], y=unitVoltageData['Unit Voltage'], name="Volts",  hovertemplate =' %{y}<br>'), secondary_y=False)
    unitVIFig.add_trace(go.Scatter(x=dataFrame['Time'], y=unitCurrentData, name="Amps", hovertemplate =
    '%{y}' + 
    '<br> SOC: %{text} <br>' + 
    '<b> Timestamp</b>: %{x}',
    text = dataFrame['Unit SOC']), secondary_y=True)
    #Set y-axes titles and auto range
    unitVIFig.update_yaxes(title_text="<b>Voltage</b>", secondary_y=False, range=(Vmin, Vmax+0.25)) #set the voltage graph range to the min/max plus a little extra
    unitVIFig.update_yaxes(title_text="<b>Amps</b>", secondary_y=True)
    # Set x-axis title
    unitVIFig.update_xaxes(title_text="Timestamp")
    return unitVIFig

def relayBreak(data):
    for i in range(0, len(data)):
        if data[i] == 'Break':
            return i
    return -1


# Sidebar & App Config
#--------------------------------------------------------------------------------------------------------------------------
#icon emojis https://webfx.com/tools/emoji-cheat-sheet
st.set_page_config(
                    page_title="Battery Data Analyzer - FP",
                    page_icon=":chart_with_upwards_trend:"
)

# Show Fortress Logo in the sidebar
header_image_html = "<img src='https://aro365543254.sharepoint.com/sites/FortressPower/Fortress%20Power%20Company%20File/07_0%20Marketing/LOGO/NEW%20LOGO/Filled/Fortress%20Power%20Logo%20Filled%20Medium.png' class='img-fluid' width='100%'>"
st.sidebar.markdown(header_image_html, unsafe_allow_html=True)

st.sidebar.title('Battery Data Analyzer')
# file uploader
st.sidebar.header('CSV Upload')
uploaded_file = st.sidebar.file_uploader("Choose a file", accept_multiple_files=True)
showDataTable = st.sidebar.checkbox('Enable Data Table')

# Main Window
#--------------------------------------------------------------------------------------------------------------------------
#title for the graph
st.title('Battery Graph')
# Instructions
with st.expander("Usage Tips"):
     st.markdown("""First upload a combined CSV file containing recorded data from either eVault Max or eFlex (eVault Classic coming soon) BMS software, then choose the kind of graph you would like to see. The following types are supported:
     """)
     st.markdown("""
     - Charging V/I - *Graphs voltage and current with charge specific values highlighted*
     - Discharging V/I - *Graphs voltage and current with discharge specific values highlighted*
     - Cell Voltages - *Graphs all 16 cells of the battery together, allows you to find the Min/Max/Delta voltages of the cells*
    """)
     st.markdown("""**Note: using the charge graph type on a discharge file (or vice versa) will result in incorrect readings, be **sure** to select the correct type**
     """)
# graph type dropdown
options = st.selectbox(
     'Graph Output Type',
     ('Charge and Discharge', 'Charge', 'Discharge', 'Cell Voltages', 'Temperatures'))

#place holder for before we get data
graphPlaceholder = st.subheader('No Data to Display, Upload a File to Start')

# Graph Loops
#--------------------------------------------------------------------------------------------------------------------------   
chargingIndex = 0 #Two variables used to check what order discharge and charge data were uploaded in
dischargingIndex = 1

if uploaded_file is not Empty: #Make sure file was uploaded

    if len(uploaded_file) == 1 : #If one file uploaded treat data same way as before
        # Can be used wherever a "file-like" object is accepted:
        df = pd.read_csv(uploaded_file[0], usecols=req_cols, dtype={"Discharge Relay Status": "category"})

    elif len(uploaded_file) == 2: #If two files are uploaded treat it as Charge and Discharge data
        df_0 = pd.read_csv(uploaded_file[0], usecols=req_cols)
        df_1 = pd.read_csv(uploaded_file[1], usecols = req_cols)

        #Determine what data is charging or discharging based on change in voltage column of battery unit
        change = 0
        for i in range(0, int(len(df_0['Unit Voltage'])/2 - 1)):
            change = change + (df_0['Unit Voltage'][i+1] - df_0['Unit Voltage'][i])

        if change < 0: #negative change in voltage means unit is discharging, so index 1 is actually charging and index 0 is discharging data
            chargingIndex = 1
            dischargingIndex = 0

    elif len(uploaded_file) > 2: #Error if uploading 3 files
        st.error("Can upload a maximum of two files for charge and discharge option, one for all others")

# Charge and Discharge Graphs
#--------------------------------------------------------------------------------------------------------------------------

if df.empty is True: #df is not empty when one csv file is uploaded
    if options == "Charge and Discharge" and len(uploaded_file) == 2: #Make sure option is charge and discharge and two file are uploaded
        if chargingIndex == 1: #Check which data frame df_0 or df_1 has charging data, other has discharge data
            createChargeAndDischarge(df_1, "Charge")
            createChargeAndDischarge(df_0, "Discharge")
        else :
            createChargeAndDischarge(df_0, "Charge")
            createChargeAndDischarge(df_1, "Discharge")

else: #df is not empty one file was uploaded, plot like before
# Discharge Graphs
#--------------------------------------------------------------------------------------------------------------------------
    if options == "Charge and Discharge":
        st.error("Have to upload exactly two files for charge and discharge option")

    elif options == "Discharge":
        #Record time stamp when discharging complete
        relayIndex = relayBreak(df['Discharge Relay Status'])
        if not relayIndex < 0 :
            st.text("Discharge Relay Open at: " + df['Time'][relayIndex])

        # Create figure with secondary y-axis
        unitVIFig = make_subplots(specs=[[{"secondary_y": True}]])
        unitVIFig = createVIGraph(df,unitVIFig, "Discharge")
        # find the row number where 0 current first occurs
        dsgRelayOpenLoc = (df['Discharge Relay Status'] == "Break").idxmax()
        # drop all rows starting from 0A to the end of the list
        df = df.drop(df.index[range(dsgRelayOpenLoc, df.shape[0])])
        unitVIFig.update_layout(title_text="Battery Voltage and Current - Unit Ser#: " + str(df['Battery ID'][0]) + "<br><sup>Firmware V"+str(df['Software Version'][0])+" - Discharging</sup>", hovermode="x unified") 
        #Annotation for SOC and Voltage at minimum volatage value of discharge
        #createAnnotationGraph(unitVIFig, np.argmin(df['Unit Voltage']), np.min(df['Unit Voltage']), "<b>SOC:</b>" + str(df.iloc[np.argmin(df['Unit Voltage'])]['Unit SOC']) + "\n" + "<b>Vstop:</b>" + str(np.min(df['Unit Voltage'])))
        figure.append(unitVIFig)
        st.plotly_chart(unitVIFig)

# Charge Graphs
#--------------------------------------------------------------------------------------------------------------------------
    elif options == "Charge":
        #Record time stamp when charging complete
        relayIndex = relayBreak(df['Charge Relay Status'])
        if not relayIndex < 0 :
            st.text("Charge Relay Open at: " + df['Time'][relayIndex])

        # Create figure with secondary y-axis
        unitVIFig = make_subplots(specs=[[{"secondary_y": True}]])
        unitVIFig = createVIGraph(df,unitVIFig, "Charge")
        #find the row number where 0 current first occurs
        currentZeroLoc = (df['Unit Current'] == 0).idxmax()
        #drop all rows starting from 0A to the end of the list
        df = df.drop(df.index[range(currentZeroLoc, df.shape[0])])
        # Add figure title
        unitVIFig.update_layout(title_text="Battery Voltage and Current - Unit Ser#: " + str(df['Battery ID'][0]) + "<br><sup>Firmware V"+str(df['Software Version'][0])+" - Charging</sup>", hovermode="x unified")
        # Add figure annotation at max voltage of charging cycle
        #createAnnotationGraph(unitVIFig, np.argmax(df['Unit Voltage']), np.max(df['Unit Voltage']), "<b>SOC:</b>" + str(df.iloc[np.argmax(df['Unit Voltage'])]['Unit SOC']) + "\n" + "<b>Vstop:</b>" + str(np.max(df['Unit Voltage'])))
        figure.append(unitVIFig)
        st.plotly_chart(unitVIFig)
        
# Cell Voltage Graphs
#--------------------------------------------------------------------------------------------------------------------------
    elif options == "Cell Voltages":
        cellVoltFig = make_subplots(specs=[[{"secondary_y": True}]])
        cellVoltFig.update_layout(title_text="Battery Cell Voltages - Unit Ser#: " + str(df['Battery ID'][0]) + "<br><sup>Firmware V"+str(df['Software Version'][0])+" - Cells 1-16</sup>")
        
        #Create 16 Cell Voltage Plot
        for i in range(0, 16):
            # Add traces
            #add 1 to the number used since we are starting at 0
            cellVoltFig.add_trace(
                go.Scatter(x=df['Time'], y=df['Cell'+str(i+1)], name="Cell" + str(i+1)),
                secondary_y=False,
            )

        #create an array to store the max value for each cell voltage
        cellVoltMinArray = []
        cellVoltMaxArray = []
        
        #create an array to store the timestamp when the highest cell voltage occurs
        cellVoltMinTimeArray = []
        cellVoltMaxTimeArray = []
        #for all 16 cells, create a line on the plot corresponding to each cells voltage
        for i in range(1, 16):
            # Add traces
            cellVoltMaxArray.append(np.amax(df['Cell' + str(i)]))
            cellVoltMaxTimeArray.append(np.argmax(df['Cell' + str(i)]))
            
            cellVoltMinArray.append(np.amin(df['Cell' + str(i)]))
            cellVoltMinTimeArray.append(np.argmin(df['Cell' + str(i)]))

        #Find the max cell voltage in the array of 16
        cellVoltMaxArray = np.amax(cellVoltMaxArray)
        #Get the cell number that is the highest, for reference add one because the array is zero based
        highCellNum = np.argmax(cellVoltMaxTimeArray)
        
        #Find the max cell voltage in the array of 16
        cellVoltMinArray = np.amin(cellVoltMinArray)
        #Get the cell number that is the highest, for reference add one because the array is zero based
        lowCellNum = np.argmin(cellVoltMinTimeArray)
  
        #ask the user what annotation they would like to see
        cellMinMaxType = st.radio(
             "Show Min or Max Cell",
             ('None', 'Min', 'Max', 'Delta'))
        
        if cellMinMaxType == 'Min':
            createAnnotationGraph(cellVoltFig, cellVoltMinTimeArray[lowCellNum], cellVoltMinArray, "Vmin on Cell #" + str(lowCellNum+1) + " :" + str(cellVoltMinArray) + "mV")
        elif cellMinMaxType == 'Max':
            createAnnotationGraph(cellVoltFig, cellVoltMaxTimeArray[highCellNum], cellVoltMaxArray, "Vmax on Cell #" + str(highCellNum+1) + " :" + str(cellVoltMaxArray) + "mV")
        elif cellMinMaxType == 'Delta':
            cellVoltFig.add_annotation(
                xref="paper",
                yref="paper",
                xanchor="auto",
                yanchor= "auto",
                yshift=-50,
                text="Min/Max Cell Delta:" + str(cellVoltMaxArray - cellVoltMinArray) + "mV",
                font=dict(
                    family="Verdana, sans-serif",
                    size=12,
                    color="#000"
                ),
                showarrow=False,
                align="center",
                bordercolor="#c7c7c7",
                borderwidth=2,
                borderpad=4,
                bgcolor="#fff",
                opacity=1
            )
        st.plotly_chart(cellVoltFig)
        figure.append(cellVoltFig)

# Temperature Graphs
#--------------------------------------------------------------------------------------------------------------------------
    elif options == "Temperatures":
        upperRange = 6 #eFlex and eVault Classic only have 6 temp sensors
        if df['Temperature(?) #7'][0] != 0: #Check if data is filled out for temp sensors 7 and 8 for eMax data
            upperRange = 8

        cellTempFig = make_subplots()
        cellTempFig.update_layout(title_text="Temperature Sensor Results - Unit Ser#: " + str(df['Battery ID'][0]) + "<br><sup>Firmware V"+str(df['Software Version'][0])+" - Sensors 1-" + str(upperRange) +"</sup>")
        
        #Create up to 8 Sensor Temperature Plot
        for i in range(0, upperRange):
            # Add traces
            #add 1 to the number used since we are starting at 0
            cellTempFig.add_trace(
            go.Scatter(x=df['Time'], y=df['Temperature(?) #'+str(i+1)], name="Temperature" + str(i+1)),
            secondary_y=False, )

        #create an array to store the max value for each cell temp
        cellTempMinArray = []
        cellTempMaxArray = []

        #create an array to store the timestamp when the highest cell temp occurs
        cellTempMinTimeArray = []
        cellTempMaxTimeArray = []
        #for up to 8 sensors, create a line on the plot corresponding to each cells voltage
        for i in range(1, upperRange):
            # Add traces
            cellTempMaxArray.append(np.amax(df['Temperature(?) #' + str(i)]))
            cellTempMaxTimeArray.append(np.argmax(df['Temperature(?) #' + str(i)]))

            cellTempMinArray.append(np.amin(df['Temperature(?) #' + str(i)]))
            cellTempMinTimeArray.append(np.argmin(df['Temperature(?) #' + str(i)]))

        #Find the max cell temp in the array of up to 8
        tempMaxArray = np.amax(cellTempMaxArray)
        #Get the cell number that is the highest, for reference add one because the array is zero based
        highCellTempNum = np.argmax(cellTempMaxTimeArray)

        #Find the min cell temp in array of up to 8
        tempMinArray = np.amin(cellTempMinArray)
        #Get the cell number that is the highest, for reference add one because the array is zero based
        lowCellTempNum = np.argmin(cellTempMinTimeArray)

        #ask the user what annotation they would like to see
        cellTempMinMaxType = st.radio(
             "Show Min or Max Cell",
             ('None', 'Min', 'Max', 'Delta'))
        
        if cellTempMinMaxType == 'Min':
            createAnnotationGraph(cellTempFig, cellTempMinTimeArray[lowCellTempNum], cellTempMinArray, "Min Temp on Sensor #" + str(lowCellTempNum+1) + " :" + str(tempMinArray) + "°C")

        elif cellTempMinMaxType == 'Max':
            createAnnotationGraph(cellTempFig, cellTempMaxTimeArray[highCellTempNum], cellTempMaxArray, "Max Temp on Sensor #" + str(highCellTempNum+1) + " :" + str(tempMaxArray) + "°C")
        elif cellTempMinMaxType == 'Delta':
            cellTempFig.add_annotation(
                xref="paper",
                yref="paper",
                xanchor="auto",
                yanchor= "auto",
                yshift=-50,
                text="Min/Max Temp Delta:" + str(tempMaxArray - tempMinArray) + "°C",
                font=dict(
                    family="Verdana, sans-serif",
                    size=12,
                    color="#000"
                ),
                showarrow=False,
                align="center",
                bordercolor="#c7c7c7",
                borderwidth=2,
                borderpad=4,
                bgcolor="#fff",
                opacity=1
            )

        figure.append(cellTempFig)
        st.plotly_chart(cellTempFig) #Create plot


#After figure is created allow users to dowload png image of it
if len(figure) == 1 :
    #Allow user to specify file name and show dowload button
    image_file_name = st.text_input("File Name", value=figure[0].layout.title.text)
    st.download_button("Dowload png of graph", figure[0].to_image(format="png"), file_name = image_file_name + "- " + options + ".png") 

#Charge and discharge option would create multiple figures
elif len(figure) > 1 :
    zipPath = uploaded_file[chargingIndex].name[0:-4] + ".zip" #create zip folder name, it will be stored in current directory
    my_zipfile = zipfile.ZipFile(zipPath, mode='w') #create local zip file to write all these files to

    if chargingIndex == 0: #Based on which dataframe is charging save datafrane as correct path
        chargingPath = df_0.to_csv(index=False)
        dischargingPath = df_1.to_csv(index=False)
    else: 
        chargingPath = df_1.to_csv(index=False)
        dischargingPath = df_0.to_csv(index=False)

    #Write the two csvs and two pngs to local zip folder, their name will allow us to parse them later.
    my_zipfile.writestr(uploaded_file[chargingIndex].name[0:-4] + "_Data_Charge.csv", chargingPath)
    my_zipfile.writestr(uploaded_file[dischargingIndex].name[0:-4] + "_Data_Discharge.csv", dischargingPath)
    my_zipfile.writestr(uploaded_file[chargingIndex].name[0:-4] + "_Plot_Charge.png", figure[0].to_image(format="png"))
    my_zipfile.writestr(uploaded_file[dischargingIndex].name[0:-4] + "_Plot_Discharge.png", figure[1].to_image(format="png")) 

    my_zipfile.close() #finished writing to zip file

    #open local zip to save its file data to download button
    with open(zipPath, "rb") as fp: 
        btn = st.download_button(
            label="Download ZIP of graphs and your data",
            data=fp,
            file_name=zipPath,
            mime="application/zip"
        )

if showDataTable and options != "Charge and Discharge":
     #display the first 5 lines of the incoming CSV as a table
     st.header("File Debug Preview")
     st.markdown("The first 5 lines of the CSV")
     if uploaded_file is not None:
         st.write(df[0:5])
# EOL        
    