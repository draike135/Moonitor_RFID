import utime
import struct
import urandom
from loraCOM import loraCOM
import sys

from sx127x import TTN, SX127x
from machine import Pin, SPI
from config import *
from sys import exit

__DEBUG__ = False


def rx_handler(mess, port):
    print("MESSAGE RECEIVED: ",''.join('{:02x}'.format(x) for x in mess),mess, " port =",port)
    
    
    
loracom = loraCOM(rx_handler)
jo=loracom.join()


while(True):

   utime.sleep(15)
   loracom.send_message('12345',1)    # (message,port))

