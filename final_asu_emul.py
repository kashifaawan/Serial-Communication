#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Thu Mar 25 13:31:32 2021

@author: Ahsan
"""

import matplotlib.pyplot as plt
import time
import threading
import sys
import numpy as np
import csv
current_version = "1.0"

ASU_Emul_port = '/dev/ttyS2'
ASU_Emul_port_baudrate = 115200

PYTHON3_INTERPRETER = True
try:
    import queue
except:
    PYTHON3_INTERPRETER = False
    print("Please run this program with python3+")
    sys.exit(1)

SERIAL_LIB = True
try:
    import serial
except:
    SERIAL_LIB = False
    print("serial library does not exist")

SCIPY_LIB = True
try:
    import scipy
except:
    SCIPY_LIB = False
    print("scipy library does not exist")

NUMPY_LIB = True
try:
    import numpy	
except:
    NUMPY_LIB = False
    print("numpy library does not exist")

MATPLOT_LIB = True
try:
    import matplot	
except:
    MATPLOT_LIB = False
    print("matplot library does not exist")

'''
PYTHON3_LIB = True
try:
	print "Test print to verify if python3 is running"
	PYTHON3_LIB = False
	#sys.exit(1)
except:
    print("Python3 is running this program")
''' 
    
#from Tkinter import * # Label, Entry, Button, BooleanVar, IntVar, Menu, Checkbutton, Radiobutton, spinbox
import tkinter as tk
#from ttk import Combobox, Progressbar, ScrolledText
from tkinter import ttk
    
_keep_running_rx_ASU_Emul_port = False
_keep_running_tx_rx_ASU_Emul_port = False

tab_conn_row=0
tab_ASU_Emul_section_row=0
tab_analysis_section_row=0

root_window = tk.Tk()
 
root_window.title("ASU Tester ver"+current_version) # introduced crc in rx
root_window.geometry('600x300')


tab_control = ttk.Notebook(root_window)
tab_conn = ttk.Frame(tab_control)
tab_ASU_Emul_section = ttk.Frame(tab_control)
tab_analysis_section = ttk.Frame(tab_control)
tab_aggression = ttk.Frame(tab_control)
tab_about = ttk.Frame(tab_control)
tab_control.add(tab_conn, text='Connection')
tab_control.add(tab_ASU_Emul_section, text='ASU_Emul')
tab_control.add(tab_analysis_section, text='Analysis')
tab_control.add(tab_aggression, text='Aggression')
tab_control.add(tab_about, text='About')

tab_control.grid(column=0, row=tab_conn_row)
tab_conn_row=tab_conn_row+1


class serial_tx_rx_ASU_Emul(threading.Thread):
    """
    start receiving on UDP socket for control channel 2 
    """
    def __init__(self,t_name="default_name"):
        threading.Thread.__init__(self)
        self._serialInterface=""
        self._handShakeCompleted = False
        self._LPMisConfigured = False
        self._receiverKeepRunning = True
        self.data_startup_time=0
        self._rxPktHeader = bytearray.fromhex('aa77')
        self._rxPktFooter = bytearray.fromhex('bb77')
        self.faultMsgType = bytearray.fromhex('f0')    #3rdbyte
        self.liveline_errorMsgType = bytearray.fromhex('00')  #4th byte
        self.feedbackupper_errorMsgType = bytearray.fromhex('01') #4th byte
        self.feedbacklower_errorMsgType = bytearray.fromhex('02')          #4th byte
        self.offstateMsgType = bytearray.fromhex('04') #3rd byte
        self.offstate_bothfailMsgType = bytearray.fromhex('00') #4th byte
        self.offstate_upperpass_lowerfailMsgType = bytearray.fromhex('01') #4th byte
        self.offstate_upperfail_lowerpassMsgType = bytearray.fromhex('02') #4th byte
        self.offstate_bothpassMsgType = bytearray.fromhex('03') #4th byte
        self.handShakeMsgType = bytearray.fromhex('00') #3rdbyte
        self.startupMsgType = bytearray.fromhex('01') #3rdbyte
        self.set_tdl_tacan_stateMsgtype=bytearray.fromhex('05') #3rd byte
        self.set_both_tdl_stateMsgType =bytearray.fromhex('01') #4th byte
        self.set_upr_tacan_lower_tdl_stateMsgType=bytearray.fromhex('02') #4th byte
        self.set_upr_tdl_lower_tacan_stateMsgType=bytearray.fromhex('03') #4th byte
        self.set_both_tacan__stateMsgType=bytearray.fromhex('04')#4th byte
        self.response_monitoring_upperMsgType = bytearray.fromhex('02') #3rdbyte
        self.response_monitoring_uppertacanMsgType = bytearray.fromhex('01')  #4th byte
        self.response_monitoring_uppertdlMsgType = bytearray.fromhex('02')    #4th byte
        self.response_monitoring_lowerMsgType = bytearray.fromhex('03')     #3rdbyte
        self.response_monitoring_lowertacanMsgType = bytearray.fromhex('01') #4th byte
        self.response_monitoring_lowertacanMsgType = bytearray.fromhex('02') #4th byte
        self.startup_voltage=0
        self.feedback_voltage=0
        self._rxPktIdentifierkeepRunning = True
        self._receiverQueue = queue.Queue(1000)
        self._txQueue = queue.Queue(100)
        self._port_is_configured = False
        self._ackFlag = False
        self._nackFlag = False
        self._rx_tx_threads_started = False
		
        
        #t3 = threading.Thread(target=self._serialTxThread)
        #t3.start()
        
    #Thread run function (called by thread_name.start())
    def config_tx_rx_serial_port(self,serial_port='/dev/ttyS2',baudrate=115200):
        try:
            if self._rx_tx_threads_started is False:
                t1 = threading.Thread(target=self._serialReadThread)
                t1.start()
                t3 = threading.Thread(target=self._serialTxThread)
                t3.start()
            self._serialInterface = serial.Serial(port=serial_port,baudrate=baudrate,timeout=0.3)
            self._port_is_configured = True
            print("ASU_Emul Rx and Tx serial port started")
        except:
            print(serial_port," port is not available, Port can not be Configured")
    def run(self,mode='config'):
        if mode == 'udp':
            t1 = threading.Thread(target=self._udpReadThread)
            t1.start()
            t3 = threading.Thread(target=self._udpTxThread)
            t3.start()
            self._rx_tx_threads_started = True
        elif mode == 'serial':
            t1 = threading.Thread(target=self._serialReadThread)
            t1.start()
            t3 = threading.Thread(target=self._serialTxThread)
            t3.start()
            self._rx_tx_threads_started = True
        t2 = threading.Thread(target=self._serialPktIdentifier)
        t2.start()

				
    def _serialReadThread(self):
        while self._port_is_configured is False:
            time.sleep(1)
        rx_stream=bytearray.fromhex("")
        
        while self._receiverKeepRunning is True:
            rx_byte = self._serialInterface.read(1) # tempo
            print(rx_byte)
            if rx_byte == "":
                continue
            rx_stream = rx_stream +rx_byte
            print(len(rx_stream),rx_stream)
            count_of_occurances = rx_stream.count(self._rxPktHeader)
            #print count_of_occurances
            if count_of_occurances > 1:
                rx_stream = rx_stream[len(self._rxPktHeader):len(rx_stream)]
            else:
                first_header = rx_stream.find(self._rxPktHeader)
                print("first_header=",first_header)
                if first_header > -1:
                    first_footer = rx_stream.find(self._rxPktFooter)
                    print("header found")
                    print("first_footer=",first_footer)
                    if first_footer>-1:
                        print("footer found")
                        payload=rx_stream[first_header+2:first_footer]
                        self._receiverQueue.put(payload)
                        print("payload has been put in queue")
                        #print "QUEUED:",payload
                        rx_stream = rx_stream[first_footer+2:len(rx_stream)]
                    else:
#                        print("header found but footer could not")
                        rx_stream = rx_stream[first_header:len(rx_stream)]
                else:
                    print("header could not be found")

    def _serialTxThread(self):
        while self._port_is_configured is False:
            time.sleep(1)
        while True:
            pkt = self._txQueue.get()
            self._serialInterface.write(pkt)
            print("Frame Sent::",pkt)

    def _serialPktIdentifier(self):
        while self._rxPktIdentifierkeepRunning is True:
     
            data = self._receiverQueue.get()
            print("payload",data)
            if len(data) > 0:
                if data[0] == self.faultMsgType[0]:
                    print("Fault Found")
                    #self.processFaultMsg(data)
                elif data[0] == self.handShakeMsgType[0]:
                    print("handshake from ASU Found")
                    #self.processhandShakeMsgType(data)
                elif data[0] == self.startupMsgType [0]:
                    print("startup_time of ASU is received ")
                    self.data_startup_time=data
                    t5 = threading.Thread(target=self.measure_startup_time)
                    t5.start()
                    filename = "startup_data.csv"    
# writing to csv file 
                    with open(filename, 'w') as csvfile: 
    # creating a csv writer object 
                      csvwriter = csv.writer(csvfile) 
                      time=['0msec','5msec','10msec','15msec','20msecc','25msec','30msec','40msec','45msec','50msec']	
    # writing the fields 
                    csvwriter.writerow(time) 
        
    # writing the data rows 
                    csvwriter.writerows(self.data_startup_time)
                    #self.measure_startup_time(data)	
                elif data[0] == self.response_monitoring_upperMsgType[0] and data[1] ==self.response_monitoring_uppertacanMsgType[0] :
                    print("Feedback response for upper tacan is received ")	
                    self.feedback_respnse_upperTacan()					
                elif data[0] == self.response_monitoring_upperMsgType[0] and data[1] ==self.response_monitoring_uppertdlMsgType[0] :	
                    print("Feedback response for upper tdl is received ")
                    self.feedback_respnse_upperTdl()
                elif data[0] == self.response_monitoring_lowerMsgType[0] and data[1] ==self.response_monitoring_lowertacanMsgType[0] :	
                    print("Feedback response for lower tacan is received ")	
                    self.feedback_respnse_lowerTdl()						
                elif data[0] == self.response_monitoring_lowerMsgType[0] and data[1] ==self.response_monitoring_lowertdlMsgType[0] :	
                    print("Feedback response for lower tdl is received ")
                    self.feedback_respnse_lowerTdl()
                elif data[0] == self.set_tdl_tacan_stateMsgtype[0] and data[1] ==self.set_both_tdl_stateMsgType[0] :	
                    print("Reply of set both chains to tdl is received ")
                    self.feedback_respnse_lowerTdl()
                elif data[0] == self.set_tdl_tacan_stateMsgtype[0] and data[1] ==self.set_upr_tacan_lower_tdl_stateMsgType[0] :	
                    print("Reply of set to upper tacan and lower tdl is received ")
                    self.feedback_respnse_lowerTdl()
                elif data[0] == self.set_tdl_tacan_stateMsgtype[0] and data[1] ==self.set_upr_tdl_lower_tacan_stateMsgType[0] :	
                    print("Reply of set to upper tdl and lower tacan is received ")
                    self.feedback_respnse_lowerTdl()
                elif data[0] == self.set_tdl_tacan_stateMsgtype[0] and data[1] ==self.set_both_tacan__stateMsgType[0] :	
                    print("Reply of set both chains to tacan is received ")
                    self.feedback_respnse_lowerTdl()	
                elif data[0] == self.offstateMsgType[0] and data[1] ==self.offstate_bothfailMsgType[0] :	
                    print("Both antenna fail ")
                elif data[0] == self.offstateMsgType[0] and data[1] ==self.offstate_upperpass_lowerfailMsgType [0] :	
                    print("upper antenna pass and lower antenna fail ")
                elif data[0] == self.offstateMsgType[0] and data[1] ==self.offstate_upperfail_lowerpassMsgType [0] :
                    print("upper antenna fail and lower antenna pass ")
                elif data[0] == self.offstateMsgType[0] and data[1] ==self.offstate_bothpassMsgType [0] :
                    print("both antenna pass ")  
                elif data[0] == self.faultMsgType[0] and data[1] ==self.liveline_errorMsgType[0] :
                    print("ASU line error ")
                elif data[0] == self.faultMsgType[0] and data[1] ==self.feedbackupper_errorMsgType[0] :
                     print("ASU upper antenna error ")
                elif data[0] == self.faultMsgType[0] and data[1] ==self.feedbacklower_errorMsgType[0] :
                    print("ASU lower antenna error ")		
                else:
                    print("Wrong msg type")

    def send_handshake(self):
        self.handShakeMsgType = bytearray.fromhex('ff')
        self.nullChar = bytearray.fromhex('00')
        frame = self._rxPktHeader + self.handShakeMsgType + self._rxPktFooter + self.nullChar
        print('put in tx queue',frame)
        self._txQueue.put(frame)

    def send_startup_Time_req(self):
        self.startupMsgType = bytearray.fromhex('01')
        self.nullChar = bytearray.fromhex('00')
        frame = self._rxPktHeader + self.startupMsgType + self._rxPktFooter + self.nullChar
        print('put in tx queue startup time req',frame)      
        self._txQueue.put(frame)                  
                        
    def measure_startup_time(self):
        startup_voltage= self.data_startup_time[0:len(self.data_startup_time)]
        time=np.arange(0,50,1)		
 
    '''       fig = plt.figure(figsize=(8,5))  #width,height
        plt.plot(time,startup_voltage)
        plt.title('ASU line status')
        plt.xlabel("Time")
        plt.ylabel("Status voltage")
        plt.xticks(time)
        plt.plot(time,startup_voltage)
        plt.show()
    '''
       
'''      
    # writing the data rows 
    def feedback_respnse_upperTacan(self):	
	    feedback_voltage= self.data[1:len(self.data)+1]			
    fig = plt.figure(figsize=(8, 5))  #width,height
    plt.plot(time,feedback_voltage)
    plt.title('ASU upper Tacan status')
    plt.xlabel("Time")
    plt.ylabel("Status voltage")
    plt.xticks(time)
    plt.plot(time,feedback_voltage)
    def feedback_respnse_upperTdl(self):	
	    feedback_voltage= self.data[1:len(self.data)+1]			
    fig = plt.figure(figsize=(8, 5))  #width,height
    plt.plot(time,startup_voltage)
    plt.title('ASU upper Tdl status')
    plt.xlabel("Time")
    plt.ylabel("Status voltage")
    plt.xticks(time)
    plt.plot(time,feedback_voltage)	
    def feedback_respnse_lowerTacan(self):	
	    feedback_voltage= data[0:len(data)]			
    fig = plt.figure(figsize=(8, 5))  #width,height
    plt.plot(time,startup_voltage)
    plt.title('ASU lower Tacan status')
    plt.xlabel("Time")
    plt.ylabel("Status voltage")
    plt.xticks(time)
    plt.plot(time,feedback_voltage)		
    def feedback_respnse_lowerTdl(self):	
        feedback_voltage= data[0:len(data)]			
    fig = plt.figure(figsize=(8, 5))  #width,height
    plt.plot(time,startup_voltage)
    plt.title('ASU lower Tdl status')
    plt.xlabel("Time")
    plt.ylabel("Status voltage")
    plt.xticks(time)
    plt.plot(time,feedback_voltage)	
'''
    		
		
			
		
                        
                        
serial_tx_rx_ASU_Emul_obj = serial_tx_rx_ASU_Emul()
serial_tx_rx_ASU_Emul_obj.start()



############################
"""
ASU_Emul section
"""
###########################


def set_config_ASU_Emul_port():
    global serial_tx_rx_ASU_Emul_obj
    global combo_ASU_Emul_port_name
    global combo_ASU_Emul_port_baudrate
    port_name = combo_ASU_Emul_port_name.get()
    port_baudrate = int(combo_ASU_Emul_port_baudrate.get())
    serial_tx_rx_ASU_Emul_obj.config_tx_rx_serial_port(port_name,port_baudrate)




lbl = tk.Label(tab_ASU_Emul_section, text="Trgt_Port")
lbl.grid(column=1, row=tab_ASU_Emul_section_row)
lbl = tk.Label(tab_ASU_Emul_section, text="Baudrate")
lbl.grid(column=2, row=tab_ASU_Emul_section_row)

tab_ASU_Emul_section_row=tab_ASU_Emul_section_row+1


btn_config_ASU_Emul_port = tk.Button(tab_ASU_Emul_section, text="Config Port", command=set_config_ASU_Emul_port, bg="yellow")
btn_config_ASU_Emul_port.grid(column=0, row=tab_ASU_Emul_section_row)

combo_ASU_Emul_port_name = ttk.Combobox(tab_ASU_Emul_section, width=15)
combo_ASU_Emul_port_name['values']= ("/dev/ttyUSB0","/dev/ttyUSB1","/dev/ttyS0","/dev/ttyS1","COM1","COM2","COM3","COM4")
combo_ASU_Emul_port_name.current(1) #set the selected item
combo_ASU_Emul_port_name.grid(column=1, row=tab_ASU_Emul_section_row)

combo_ASU_Emul_port_baudrate = ttk.Combobox(tab_ASU_Emul_section, width=7)
combo_ASU_Emul_port_baudrate['values']= ("115200", "9600")
combo_ASU_Emul_port_baudrate.current(0) #set the selected item
combo_ASU_Emul_port_baudrate.grid(column=2, row=tab_ASU_Emul_section_row)
tab_ASU_Emul_section_row = tab_ASU_Emul_section_row + 1
btn_ASU_Emul_handshake_req = tk.Button(tab_ASU_Emul_section, text="HandShake_Req", command=serial_tx_rx_ASU_Emul_obj.send_handshake, bg="yellow")
btn_ASU_Emul_handshake_req.grid(column=0, row=tab_ASU_Emul_section_row)
tab_ASU_Emul_section_row = tab_ASU_Emul_section_row + 1
btn_ASU_Emul_startup_Time = tk.Button(tab_ASU_Emul_section, text="Startup_Time", command=serial_tx_rx_ASU_Emul_obj.send_startup_Time_req, bg="yellow")
btn_ASU_Emul_startup_Time.grid(column=0, row=tab_ASU_Emul_section_row)
'''
tab_ASU_Emul_section_row = tab_ASU_Emul_section_row + 1
btn_config_ASU_Emul_port = tk.Button(tab_ASU_Emul_section, text="Set_chains ", bg="yellow")
btn_config_ASU_Emul_port.grid(column=0, row=tab_ASU_Emul_section_row)

combo_ASU_Emul_port_name = ttk.Combobox(tab_ASU_Emul_section, width=15)
combo_ASU_Emul_port_name['values']= ("both_tdl","upr_tdl_lower_tacan","lower_tacan_upr_tdl","both_tacan")
combo_ASU_Emul_port_name.current(0) #set the selected item
combo_ASU_Emul_port_name.grid(column=1, row=tab_ASU_Emul_section_row)
'''
root_window.mainloop()
