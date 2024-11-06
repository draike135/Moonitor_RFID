import utime
import struct
import urandom
from loraCOM import loraCOM
import sys
from sx127x import TTN, SX127x
from machine import Pin, SPI, UART
import binascii

# Handler function for LoRa messages
def rx_handler(mess, port):
    print("MESSAGE RECEIVED: ", ''.join('{:02x}'.format(x) for x in mess), mess, " port =", port)

# Initialize LoRa communication
loracom = loraCOM(rx_handler)
jo = loracom.join()

# Initialize UART with RX and TX pins
uart = UART(1, baudrate=9600, tx=13, rx=14)  # Adjust the TX and RX pins as per your setup

# Helper function to convert hex to integer
def from_hex(c):
    if '0' <= c <= '9':
        return ord(c) - ord('0')
    return ord(c) - ord('A') + 10

# Class to handle RFID tag data
class TagInfo:
    def __init__(self, buffer):
        self.buffer = buffer
        self.m_data = buffer

        # Convert the ascii hex values to a single integer
        self.m_tag_id = 0
        for i in range(len(self.m_data['tag_id']) - 1, -1, -1):
            self.m_tag_id = (self.m_tag_id << 4)
            self.m_tag_id += from_hex(chr(self.m_data['tag_id'][i]))

        self.m_country_id = 0
        for i in range(len(self.m_data['country_id']) - 1, -1, -1):
            self.m_country_id = (self.m_country_id << 4)
            self.m_country_id += from_hex(chr(self.m_data['country_id'][i]))

    # Validate tag data
    def validate(self):
        if self.m_data['start_byte'] != 0x02:
            return False
        if self.m_data['end_byte'] != 0x03:
            return False
        # TODO: Add checksum validation if needed
        return True

    # Getter methods
    def get_tag_id(self):
        return self.m_tag_id

    def get_country_id(self):
        return self.m_country_id

# Setup function to initialize
def setup():
    print("Initializing...")

# Main loop to read RFID data
def loop():
    if uart.any() > 0:
        tag_data = b''
        while uart.any() > 0:
            tag_data += uart.read(1)  # Read a byte from RFID reader

        hex_data = binascii.hexlify(tag_data).decode('ascii')

        if len(hex_data) > 3:
            hex_data = "02" + hex_data
            spaced_hex_string = ' '.join(hex_data[i:i + 2] for i in range(0, len(hex_data, 2)))
            
            hex_list = spaced_hex_string.split()

            # Convert hex strings to integers
            buffer = {
                'start_byte': int(hex_list[0], 16),
                'tag_id': [int(hex_value, 16) for hex_value in hex_list[1:11]],
                'country_id': [int(hex_value, 16) for hex_value in hex_list[11:15]],
                'data_block': int(hex_list[15], 16),
                'animal_flag': int(hex_list[16], 16),
                'reserved4': [int(hex_value, 16) for hex_value in hex_list[17:21]],
                'reserved6': [int(hex_value, 16) for hex_value in hex_list[21:27]],
                'crc1': int(hex_list[27], 16),
                'crc2': int(hex_list[28], 16),
                'end_byte': int(hex_list[29], 16)
            }
            
            tag_info = TagInfo(buffer)
            if tag_info.validate():
                country_id = tag_info.get_country_id()
                tag_id = tag_info.get_tag_id()
                
                # Print the tag data
                print(f"Country ID: {country_id}, Tag ID: {tag_id}")
                
                # Send the tag data via LoRa
                loracom.send_message(f'{country_id}{tag_id}', 1)  # Send country ID and tag ID as message on port 1
                
        utime.sleep(1)  # Delay to prevent rapid reading

# Initialize setup and start the loop
setup()
while True:
    loop()
