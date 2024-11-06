import utime
from machine import SPI, Pin
from encryption_aes import AESnew
from encryption_aes import AES
import gc
import urandom
import ubinascii
import json
from config import *

PA_OUTPUT_RFO_PIN = 0
PA_OUTPUT_PA_BOOST_PIN = 1

# registers
REG_FIFO = 0x00
REG_OP_MODE = 0x01
REG_FRF_MSB = 0x06
REG_FRF_MID = 0x07
REG_FRF_LSB = 0x08
REG_PA_CONFIG = 0x09
REG_LNA = 0x0C
REG_FIFO_ADDR_PTR = 0x0D

REG_FIFO_TX_BASE_ADDR = 0x0E
FifoRxBaseAddr = 0x00
FifoTxBaseAddr = 0x00
#FifoTxBaseAddr = 0x80    # PRV

REG_FIFO_RX_BASE_ADDR = 0x0F
FifoRxBaseAddr = 0x00
REG_FIFO_RX_CURRENT_ADDR = 0x10
REG_IRQ_FLAGS_MASK = 0x11
REG_IRQ_FLAGS = 0x12
REG_RX_NB_BYTES = 0x13
REG_PKT_RSSI_VALUE = 0x1A
REG_PKT_SNR_VALUE = 0x1B

REG_FEI_MSB = 0x1D
REG_FEI_LSB = 0x1E
REG_MODEM_CONFIG = 0x26

REG_PREAMBLE_DETECT = 0x1F
REG_PREAMBLE_MSB = 0x20
REG_PREAMBLE_LSB = 0x21
REG_PAYLOAD_LENGTH = 0x22
REG_FIFO_RX_BYTE_ADDR = 0x25

REG_RSSI_WIDEBAND = 0x2C
REG_DETECTION_OPTIMIZE = 0x31
REG_DETECTION_THRESHOLD = 0x37
REG_SYNC_WORD = 0x39
REG_DIO_MAPPING_1 = 0x40
REG_VERSION = 0x42

# invert IQ
REG_INVERTIQ = 0x33
RFLR_INVERTIQ_RX_MASK = 0xBF
RFLR_INVERTIQ_RX_OFF = 0x00
RFLR_INVERTIQ_RX_ON = 0x40
RFLR_INVERTIQ_TX_MASK = 0xFE
RFLR_INVERTIQ_TX_OFF = 0x01
RFLR_INVERTIQ_TX_ON = 0x00

REG_INVERTIQ2 = 0x3B
RFLR_INVERTIQ2_ON = 0x19
RFLR_INVERTIQ2_OFF = 0x1D

# modes
MODE_LONG_RANGE_MODE = 0x80  # bit 7: 1 => LoRa mode
MODE_SLEEP = 0x00
MODE_STDBY = 0x01
MODE_TX = 0x03
MODE_RX_CONTINUOUS = 0x05
MODE_RX_SINGLE = 0x06

# PA config
PA_BOOST = 0x80

# IRQ masks
IRQ_TX_DONE_MASK = 0x08
IRQ_PAYLOAD_CRC_ERROR_MASK = 0x20
IRQ_RX_DONE_MASK = 0x40
IRQ_RX_TIME_OUT_MASK = 0x80

# Buffer size
MAX_PKT_LENGTH = 255

__DEBUG__ = False

class TTN:
    """ TTN Class.
    """
    def __init__(self, dev_eui, app_eui, app_key, country="EU"):
        """ Interface for The Things Network.
        """
        self.dev_eui = dev_eui
        self.app_eui = app_eui
        self.app_key = app_key
        self.region = country
        self.dev_addr=bytearray(4)
        self.net_s_key=bytearray(16)
        self.app_s_key=bytearray(16)
        self.join_accept=False
        
        #self.dev_addr = dev_address
        #self.net_key = net_key
        #self.app_key = app_key
        #self.region = country

    @property
    def device_address(self):
        """ Returns the TTN Device Address.
        """
        return self.dev_addr
    
    @property
    def network_key(self):
        """ Returns the TTN Network Key.
        """
        return self.net_s_key

    @property
    def application_key(self):
        """ Returns the TTN Application Key.
        """
        return self.app_s_key
    
    @property
    def country(self):
        """ Returns the TTN Frequency Country.
        """
        return self.region


class SX127x:

    _default_parameters = {
                'tx_power_level': 2, 
                'signal_bandwidth': 'SF7BW125',
                'spreading_factor': 7,    
                'coding_rate': 5, 
                'sync_word': 0x34, 
                'implicit_header': False,
                'preamble_length': 8,
                'enable_CRC': False,
                'invert_IQ': False,
                }

    _data_rates = {
        "SF7BW125":(0x74, 0x72, 0x04), "SF7BW250":(0x74, 0x82, 0x04),
        "SF8BW125":(0x84, 0x72, 0x04), "SF9BW125":(0x94, 0x72, 0x04),
        "SF10BW125":(0xA4, 0x72, 0x04), "SF11BW125":(0xB4, 0x72, 0x0C),
        "SF12BW125":(0xC4, 0x72, 0x0C)
    }
            
    def __init__(self,
#                 spi,
#                 pins,
#                 ttn_config, 
                 channel=0,  # compatibility with Dragino LG02, set to None otherwise
                 fport=1,
#                 lora_parameters=_default_parameters
                 ):
        
#        print("TTNCONFIG=",ttn_config['country'])
#        self.country=ttn_config['country']
        
        self._spi = SPI(baudrate = 10000000, 
        polarity = 0, phase = 0, bits = 8, firstbit = SPI.MSB,
        sck = Pin(device_config['sck'], Pin.OUT, Pin.PULL_DOWN),
        mosi = Pin(device_config['mosi'], Pin.OUT, Pin.PULL_UP),
        miso = Pin(device_config['miso'], Pin.IN, Pin.PULL_UP))
        
        self._pins = device_config
        self._parameters = lora_parameters
        self._lock = False
        self._dev_nonce=b'\x00\x00'
        self._frame_counter=b'\x00\x00'
        ttn=TTN(ttn_config['DevEUI'], ttn_config['AppEUI'], ttn_config['AppKey'], country=ttn_config['country'])
     
        # setting pins
        if "dio_0" in self._pins:
            self._pin_rx_done = Pin(self._pins["dio_0"], Pin.IN)
            self._irq = Pin(self._pins["dio_0"], Pin.IN)
        if "ss" in self._pins:
            self._pin_ss = Pin(self._pins["ss"], Pin.OUT)
        if "led" in self._pins:
            self._led_status = Pin(self._pins["led"], Pin.OUT)

        # check hardware version
        init_try = True
        re_try = 0
        while init_try and re_try < 5:
            version = self.read_register(REG_VERSION)
            re_try = re_try + 1
            
            if __DEBUG__:
                print("SX version: {}".format(version))

            if version == 0x12:
                init_try = False
            else:
                utime.sleep_ms(1000)

        if version != 0x12:
            raise Exception('Invalid version.')

        # Set frequency registers
        self._rfm_msb = None
        self._rfm_mid = None
        self._rfm_lsb = None
        # init framecounter
        self.frame_counter = 0
        self._fport = fport

        # Set datarate registers
        self._sf = None
        self._bw = None
        self._modemcfg = None

        # ttn configuration
        if "US" in ttn.country:
            from ttn.ttn_usa import TTN_FREQS
            self._frequencies = TTN_FREQS
        elif ttn.country == "AS":
            from ttn.ttn_as import TTN_FREQS
            self._frequencies = TTN_FREQS
        elif ttn.country == "AU":
            from ttn.ttn_au import TTN_FREQS
            self._frequencies = TTN_FREQS
        elif ttn.country == "EU":
            from ttn.ttn_eu import TTN_FREQS
            self._frequencies = TTN_FREQS
        else:
            raise TypeError("Country Code Incorrect/Unsupported")
        # Give the uLoRa object ttn configuration
        self._ttn = ttn

        # put in LoRa and sleep mode
        self.sleep()

        # set channel number
        self._channel = channel
        self._actual_channel = channel
        if self._channel is not None: 
            self.set_frequency(self._channel)

        # set data rate and bandwidth
        self.set_bandwidth(self._parameters["signal_bandwidth"])

        # set LNA boost
        self.write_register(REG_LNA, self.read_register(REG_LNA) | 0x03)

        # set auto AGC
        self.write_register(REG_MODEM_CONFIG, 0x04)
        self.implicit_header_mode(self._parameters['implicit_header'])
        self.set_tx_power(self._parameters['tx_power_level'])
        self.set_coding_rate(self._parameters['coding_rate'])
        self.set_sync_word(self._parameters['sync_word'])
        self.enable_CRC(self._parameters['enable_CRC'])
        #self.invert_IQ(self._parameters["invert_IQ"])
        self.set_preamble_length(self._parameters['preamble_length'])
        self.set_spreading_factor(self._parameters['spreading_factor'])

        # set base addresses
        self.write_register(REG_FIFO_TX_BASE_ADDR, FifoTxBaseAddr)
        self.write_register(REG_FIFO_RX_BASE_ADDR, FifoRxBaseAddr)
        
        self.standby()
        
        with open('data.txt','r') as json_file:
           self.data = json.load(json_file)
        

    def begin_packet(self, implicit_header_mode = False):
        self.standby()
        self.implicit_header_mode(implicit_header_mode)
        #self.write_register(REG_DIO_MAPPING_1, 0x40)
        
        # Check for multi-channel configuration
        if self._channel is None:
            self._actual_channel = urandom.getrandbits(3)
            self.set_frequency(self._actual_channel)

        # reset FIFO address and paload length
        self.write_register(REG_FIFO_ADDR_PTR, FifoTxBaseAddr)
        self.write_register(REG_PAYLOAD_LENGTH, 0)

    def end_packet(self, timeout=5):
        # put in TX mode
        self.write_register(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_TX)    # 0x01 0x83


        # PRV - clear IRQ's
        self.write_register(REG_IRQ_FLAGS, IRQ_TX_DONE_MASK)

        
        start = utime.time()
        timed_out = False

        # wait for TX done, standby automatically on TX_DONE
        #self.read_register(REG_IRQ_FLAGS) & IRQ_TX_DONE_MASK == 0 and \
        irq_value = self.read_register(REG_IRQ_FLAGS)
        while not timed_out and \
              irq_value & IRQ_TX_DONE_MASK == 0:
            
            
            
            if utime.time() - start >= timeout:
                timed_out = True
            else:
                irq_value = self.read_register(REG_IRQ_FLAGS)

            if(irq_value!=0):
              print("---->%d %x" % (timeout,irq_value))  #PRV

        if timed_out:
            raise RuntimeError("Timeout during packet send")

        # clear IRQ's
        self.write_register(REG_IRQ_FLAGS, IRQ_TX_DONE_MASK)

        self.collect_garbage()

    def write(self, buffer, buffer_length):
        # update length
        self.write_register(REG_PAYLOAD_LENGTH, buffer_length)
 #       self.write_register(0x0D, 0x80)   # PRV acrescentei

        # write data
        for i in range(buffer_length):
            self.write_register(REG_FIFO, buffer[i])


    def set_lock(self, lock = False):
        self._lock = lock

#    def send_data(self, data, data_length, frame_counter, timeout=5):
    def send_data(self, data, data_length, timeout=5):
        # Data packet
        enc_data = bytearray(data_length)
        lora_pkt = bytearray(64)


        fc=self.data['FrameCounter']+1
        self._frame_counter=fc.to_bytes(2,'little')
        self.data['FrameCounter'] = fc
        with open('data.txt','w') as json_file:
           json.dump(self.data,json_file)

        # Copy bytearray into bytearray for encryption
        enc_data[0:data_length] = data[0:data_length]

        # Encrypt data (enc_data is overwritten in this function)
#        self.frame_counter = frame_counter
        aes = AES(
           self._ttn.dev_addr,
           self._ttn.app_s_key,
           self._ttn.net_s_key,
           self._frame_counter
           
            #self._ttn.device_address,
            #self._ttn.app_key,
            #self._ttn.network_key,
#            self.frame_counter
#            self._frame_counter
        )
        
        print("     enc_data:",''.join('{:02x}'.format(x) for x in enc_data))
        enc_data = aes.encrypt(enc_data)
        print("     enc_data:",''.join('{:02x}'.format(x) for x in enc_data))
        
        # Construct MAC Layer packet (PHYPayload)
        # MHDR (MAC Header) - 1 byte
        
#        lora_pkt[0] = REG_DIO_MAPPING_1 # MType: unconfirmed data up, RFU / Major zeroed
        lora_pkt[0] = 0x40 # MType: unconfirmed data up, RFU / Major zeroed
#        lora_pkt[0] = 0x80 # MType: confirmed data up, RFU / Major zeroed
        
        # MACPayload
        # FHDR (Frame Header): DevAddr (4 bytes) - short device address
#        lora_pkt[1] = self._ttn_config.device_address[3]
#        lora_pkt[2] = self._ttn_config.device_address[2]
#        lora_pkt[3] = self._ttn_config.device_address[1]
#        lora_pkt[4] = self._ttn_config.device_address[0]
        lora_pkt[1] = self._ttn.dev_addr[3]
        lora_pkt[2] = self._ttn.dev_addr[2]
        lora_pkt[3] = self._ttn.dev_addr[1]
        lora_pkt[4] = self._ttn.dev_addr[0]
        # FHDR (Frame Header): FCtrl (1 byte) - frame control
        lora_pkt[5] = 0x00
        # FHDR (Frame Header): FCnt (2 bytes) - frame counter
#        lora_pkt[6] = self.frame_counter & 0x00FF
#        lora_pkt[7] = (self.frame_counter >> 8) & 0x00FF
        
#        fc=self.data['FrameCounter']+1
#        self._frame_counter=fc.to_bytes(2,'little')
#        self.data['FrameCounter'] = fc
#        with open('data.txt','w') as json_file:
#           json.dump(self.data,json_file)
        
        lora_pkt[6] = self._frame_counter[0]
        lora_pkt[7] = self._frame_counter[1]
        
        aes.frame_counter=self._frame_counter
        
        # FPort - port field
        lora_pkt[8] = self._fport
        # Set length of LoRa packet
        lora_pkt_len = 9

        if __DEBUG__:
            print("PHYPayload", ubinascii.hexlify(lora_pkt))
        # load encrypted data into lora_pkt
        lora_pkt[lora_pkt_len : lora_pkt_len + data_length] = enc_data[0:data_length]

        if __DEBUG__:
            print("PHYPayload with FRMPayload", ubinascii.hexlify(lora_pkt))

        # Recalculate packet length
        lora_pkt_len += data_length
        # Calculate Message Integrity Code (MIC)
        # MIC is calculated over: MHDR | FHDR | FPort | FRMPayload
        mic = bytearray(4)
        mic = aes.calculate_mic(lora_pkt, lora_pkt_len, mic)

        # Load MIC in package
        lora_pkt[lora_pkt_len : lora_pkt_len + 4] = mic[0:4]
        # Recalculate packet length (add MIC length)
        lora_pkt_len += 4
        
        if __DEBUG__:
            print("PHYPayload with FRMPayload + MIC", ubinascii.hexlify(lora_pkt))
        print("lora_pkt_len=",lora_pkt_len)
        
        self.send_packet(lora_pkt, lora_pkt_len, timeout)
        
        print("Registo 0x1D = %02X" % self.read_register(0x1d) )

    def send_packet_old(self, lora_packet, packet_length, timeout):
        """ Sends a LoRa packet using the SX1276 module.
        """
        self.set_lock(True)  # wait until RX_Done, lock and begin writing.

        self.begin_packet_1()
        
#        self.write_register(0x0D, self.read_register(0x0E))   # PRV acrescentei
#        self.write_register(0x0D, 0x80)   # PRV acrescentei

        # Fill the FIFO buffer with the LoRa payload
        self.write(lora_packet, packet_length)      
        
        
        # Send the package
        self.end_packet(timeout)

        self.set_lock(False) # unlock when done writing

        self.blink_led()
        self.collect_garbage()

############################### PRV ################################
        
        
    def send_message(self, data, port, timeout=5):
        # Data packet
        data_length=len(data)
        enc_data=bytearray(data)
        lora_pkt = bytearray(64)

        fc=self.data['FrameCounter']+1
        self._frame_counter=fc.to_bytes(2,'little')
        self.data['FrameCounter'] = fc
        self._fport=port
        with open('data.txt','w') as json_file:
           json.dump(self.data,json_file)


#        self._ttn.app_s_key=bytearray(16)
        print("      dev_addr: ",''.join('{:02x}'.format(x) for x in self._ttn.dev_addr))
        print("      app_s_key:",''.join('{:02x}'.format(x) for x in self._ttn.app_s_key))
        print("      net_s_key:",''.join('{:02x}'.format(x) for x in self._ttn.net_s_key))
        print("      frame_counter:",self._frame_counter)


        # Encrypt data (enc_data is overwritten in this function)
#        self.frame_counter = frame_counter
        aes = AES(
           self._ttn.dev_addr,
           self._ttn.app_s_key,
           self._ttn.net_s_key,
           self._frame_counter
           
            #self._ttn.device_address,
            #self._ttn.app_key,
            #self._ttn.network_key,
#            self.frame_counter
#            self._frame_counter
        )
        
        #print("     enc_data:",''.join('{:02x}'.format(x) for x in enc_data))
        enc_data = aes.encrypt(enc_data)
        #print("     enc_data:",''.join('{:02x}'.format(x) for x in enc_data))
        
        # Construct MAC Layer packet (PHYPayload)
        # MHDR (MAC Header) - 1 byte
        
#        lora_pkt[0] = REG_DIO_MAPPING_1 # MType: unconfirmed data up, RFU / Major zeroed
        lora_pkt[0] = 0x40 # MType: unconfirmed data up, RFU / Major zeroed
#        lora_pkt[0] = 0x80 # MType: confirmed data up, RFU / Major zeroed
        
        # MACPayload
        # FHDR (Frame Header): DevAddr (4 bytes) - short device address
#        lora_pkt[1] = self._ttn_config.device_address[3]
#        lora_pkt[2] = self._ttn_config.device_address[2]
#        lora_pkt[3] = self._ttn_config.device_address[1]
#        lora_pkt[4] = self._ttn_config.device_address[0]
        lora_pkt[1] = self._ttn.dev_addr[3]
        lora_pkt[2] = self._ttn.dev_addr[2]
        lora_pkt[3] = self._ttn.dev_addr[1]
        lora_pkt[4] = self._ttn.dev_addr[0]
        # FHDR (Frame Header): FCtrl (1 byte) - frame control
        #lora_pkt[5] = 0x00
        lora_pkt[5] = 0x80    # ADR=1
        
        # FHDR (Frame Header): FCnt (2 bytes) - frame counter
#        lora_pkt[6] = self.frame_counter & 0x00FF
#        lora_pkt[7] = (self.frame_counter >> 8) & 0x00FF
        
#        fc=self.data['FrameCounter']+1
#        self._frame_counter=fc.to_bytes(2,'little')
#        self.data['FrameCounter'] = fc
#        with open('data.txt','w') as json_file:
#           json.dump(self.data,json_file)
        
        lora_pkt[6] = self._frame_counter[0]
        lora_pkt[7] = self._frame_counter[1]
        
        aes.frame_counter=self._frame_counter
        
        # FPort - port field
        lora_pkt[8] = self._fport
        # Set length of LoRa packet
        lora_pkt_len = 9

        #if __DEBUG__:
            #print("PHYPayload", ubinascii.hexlify(lora_pkt))
        
        # load encrypted data into lora_pkt
        lora_pkt[lora_pkt_len : lora_pkt_len + data_length] = enc_data[0:data_length]

        #if __DEBUG__:
            #print("PHYPayload with FRMPayload", ubinascii.hexlify(lora_pkt))

        # Recalculate packet length
        lora_pkt_len += data_length
        # Calculate Message Integrity Code (MIC)
        # MIC is calculated over: MHDR | FHDR | FPort | FRMPayload
        mic = bytearray(4)
        mic = aes.calculate_mic(lora_pkt, lora_pkt_len, mic)
        #print("     mic:",''.join('{:02x}'.format(x) for x in mic))

        # Load MIC in package
        lora_pkt[lora_pkt_len : lora_pkt_len + 4] = mic[0:4]
        # Recalculate packet length (add MIC length)
        lora_pkt_len += 4

        #print("     lora_pkt:",''.join('{:02x}'.format(x) for x in lora_pkt))


        #if __DEBUG__:
            #print("PHYPayload with FRMPayload + MIC", ubinascii.hexlify(lora_pkt))
        #print("lora_pkt_len=",lora_pkt_len)
        
        self.send_packet(lora_pkt, lora_pkt_len, timeout)
        
        #print("Registo 0x1D = %02X" % self.read_register(0x1d) )
        
        print("      Message sent")
        
        
        
        
        
    def send_packet(self, lora_packet, packet_length, timeout):
        """ Sends a LoRa packet using the SX1276 module.
        """
            
        # set channel number
        self.set_frequency(self._channel)

        # set data rate and bandwidth
        self.set_bandwidth(self._parameters["signal_bandwidth"])
        #DEBUG1#print("                                      --> signal_bandwidth=",self._parameters["signal_bandwidth"])

        # set LNA boost
        self.write_register(REG_LNA, self.read_register(REG_LNA) | 0x03)

        # set auto AGC
        self.write_register(REG_MODEM_CONFIG, 0x04)
        self.implicit_header_mode(self._parameters['implicit_header'])
        self.set_tx_power(self._parameters['tx_power_level'])
        self.set_coding_rate(self._parameters['coding_rate'])
        #DEBUG1#print("                                      --> coding_rate=",self._parameters["coding_rate"])
        self.set_sync_word(self._parameters['sync_word'])
        self.enable_CRC(self._parameters['enable_CRC'])
        self.set_preamble_length(self._parameters['preamble_length'])
        self.set_spreading_factor(self._parameters['spreading_factor'])
        #DEBUG1#print("                                      --> spreading_factor=",self._parameters["spreading_factor"])

        # set base addresses
        self.write_register(REG_FIFO_TX_BASE_ADDR, FifoTxBaseAddr)
        self.write_register(REG_FIFO_RX_BASE_ADDR, FifoRxBaseAddr)

        self.standby()
        
        self.write_register(0x0d,0)    # PRV importante pois se não colocar após RX não envia mais mensagens
        
        self.set_lock(True)  # wait until RX_Done, lock and begin writing.

        self.write_register(0x01, 0x81)      # 0x81 (LORA mode)+(STDBY mode)
        self.write_register(0x40, 0x40)      #B   RegDioMapping1 0x00:DIOx=00 => DIO0=RxDone    0x40:DIOx=01 => DIO0=TxDone

        self.write_register(0x33, 0x27)      # InvertIQ     onRX+onTX: 0x47   offRX+onTX: 0x27
        self.write_register(0x3B, 0x1D)      # InvertIQ2    off:0x1D  on:0x19

        self.write_register(0x22, packet_length)      # payload length

        for i in range(packet_length):
            self.write_register(0x00, lora_packet[i])
        self.write_register(0x01, 0x83)    #H      0x83 (LORA mode)+(TX mode)   
        self.write_register(0x12, 0x08)    #I      RegIrqFlags  (clear TxDone IRQ)
       
        self.set_lock(False) # unlock when done writing      
        self.blink_led()
        
        self.write_register(0x40, 0x00)      #       RegDioMapping1 0x00:DIOx=00 => DIO0=RxDone
        self.write_register(0x33, 0x67)      # 0x67 InvertIQ           onRX+onTX: 0x47   offRX+onTX: 0x27    onRx+onTx: 0x67
        #self.write_register(0x1E, 0x74)      # 0x84 RegModemConfig2    SF8: 0x84  SF9: 0x94
        #self.write_register(0x1D, 0x72)      # RegModemConfig1    2: explicit  4/5   7: 125kHz
        #self.write_register(0x26, 0x04)      # RegModemConfig3    4: LNA gain set by internal AGC (AGC auto)
        self.set_bandwidth(self._parameters["signal_bandwidth"])
        
        self.write_register(0x01, 0x85)      # 0x86 (LORA mode)+(RXSINGLE mode)   
        
        self.collect_garbage()


    def send_join_request(self):
        
        nonce=self.data['DevNonceN']+1
        self._dev_nonce=nonce.to_bytes(2,'little')
        self.data['DevNonceN'] = nonce
        with open('data.txt','w') as json_file:
           json.dump(self.data,json_file)
           
        aes = AESnew(self._ttn.dev_eui,self._ttn.app_eui,self._ttn.app_key)
        timeout=5
        
        lora_pkt = bytearray(64)
        lora_pkt[0] = 0x00 # MType: Join Request
        
        for n in range(8):         # APP EUI
            lora_pkt[n+1]=self._ttn.app_eui[7-n]
        for n in range(8):         # DEV EUI
            lora_pkt[n+9]=self._ttn.dev_eui[7-n]
        lora_pkt[17] = self._dev_nonce[0]     # DEVNonce Low  (?)
        lora_pkt[18] = self._dev_nonce[1]     # DEVNonce High (?)
        lora_pkt_len = 19

        mic = bytearray(4)
        aes.calculate_join_mic(lora_pkt, lora_pkt_len, mic)

        print("      send_join_request(): self._dev_nonce=", ''.join('{:02x}'.format(x) for x in self._dev_nonce), "mic=",''.join('{:02x}'.format(x) for x in mic))

        # Load MIC in package
        lora_pkt[lora_pkt_len : lora_pkt_len + 4] = mic[0:4]
        # Recalculate packet length (add MIC length)
        lora_pkt_len += 4
        
        self.send_packet(lora_pkt, lora_pkt_len, timeout)


    def begin_packet_1(self, implicit_header_mode = False):
        self.standby()
        
        self.write_register(0x1E, 0x84)  ############### ??
        
        self.implicit_header_mode(implicit_header_mode)     # registo 1D --> 72
        self.write_register(0x26, 0x04)
        #self.write_register(0x06, 0xD9)  # 868.502MHz
        #self.write_register(0x07, 0x20)  #
        #self.write_register(0x08, 0x24)  #
        self.write_register(0x40, 0x40)    #B
        self.write_register(0x33, 0x27)    # InvertIQ     onRX+onTX: 0x47   offRX+onTX: 0x27
        self.write_register(0x3B, 0x1D)    # InvertIQ2    off:0x1D  on:0x19
        #self.write_register(0x22, 0x16)    #E
        
        
        
        
        
        #self.write_register(REG_DIO_MAPPING_1, 0x40)
        
        # Check for multi-channel configuration
        if self._channel is None:
            self._actual_channel = urandom.getrandbits(3)
            self.set_frequency(self._actual_channel)

        # reset FIFO address and paload length
#        self.write_register(REG_FIFO_ADDR_PTR, FifoTxBaseAddr)   # registo 0D --> 00
        #self.write_register(REG_PAYLOAD_LENGTH, 0)


    def get_irq_flags(self):
        irq_flags = self.read_register(REG_IRQ_FLAGS)

        if __DEBUG__:
            irq_dict = dict(
                rx_timeout     = irq_flags >> 7 & 0x01,
                rx_done        = irq_flags >> 6 & 0x01,
                crc_error      = irq_flags >> 5 & 0x01,
                valid_header   = irq_flags >> 4 & 0x01,
                tx_done        = irq_flags >> 3 & 0x01,
                cad_done       = irq_flags >> 2 & 0x01,
                fhss_change_ch = irq_flags >> 1 & 0x01,
                cad_detected   = irq_flags >> 0 & 0x01,
            )
            print(irq_dict)

        self.write_register(REG_IRQ_FLAGS, irq_flags)
        
        return irq_flags

    def packet_rssi(self):
        # TODO
        rssi = self.read_register(REG_PKT_RSSI_VALUE)
        return rssi
        #return (rssi - (164 if self._frequency < 868E6 else 157))

    def packet_snr(self):
        snr = self.read_register(REG_PKT_SNR_VALUE)
        return snr * 0.25

    def standby(self):
        self.write_register(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_STDBY)
        utime.sleep_ms(10)

    def sleep(self):
        self.write_register(REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_SLEEP)
        utime.sleep_ms(10)

    def set_tx_power(self, level, outputPin=PA_OUTPUT_PA_BOOST_PIN):
        self._tx_power_level = level

        if (outputPin == PA_OUTPUT_RFO_PIN):
            # RFO
            level = min(max(level, 0), 14)
            self.write_register(REG_PA_CONFIG, 0x70 | level)

        else:
            # PA BOOST
            level = min(max(level, 2), 17)
            self.write_register(REG_PA_CONFIG, PA_BOOST | (level - 2))

    def set_frequency(self, channel):
        self.write_register(REG_FRF_MSB, self._frequencies[channel][0])
        self.write_register(REG_FRF_MID, self._frequencies[channel][1])
        self.write_register(REG_FRF_LSB, self._frequencies[channel][2])
    
    def set_coding_rate(self, denominator):
        denominator = min(max(denominator, 5), 8)
        cr = denominator - 4
        self.write_register(
            REG_FEI_MSB, 
            (self.read_register(REG_FEI_MSB) & 0xf1) | (cr << 1)
        )

    def set_preamble_length(self, length):
        self.write_register(REG_PREAMBLE_MSB,  (length >> 8) & 0xff)
        self.write_register(REG_PREAMBLE_LSB,  (length >> 0) & 0xff)

    def set_spreading_factor(self, sf): 
        sf = min(max(sf, 6), 12)
        self.write_register(REG_DETECTION_OPTIMIZE, 0xc5 if sf == 6 else 0xc3)
        self.write_register(REG_DETECTION_THRESHOLD, 0x0c if sf == 6 else 0x0a)
        self.write_register(REG_FEI_LSB, (self.read_register(REG_FEI_LSB) & 0x0f) | ((sf << 4) & 0xf0))
        
    def set_bandwidth(self, datarate):
        try:
            sf, bw, modemcfg = self._data_rates[datarate]
            self.write_register(REG_FEI_LSB, sf)
            self.write_register(REG_FEI_MSB, bw)
            self.write_register(REG_MODEM_CONFIG, modemcfg)
        except KeyError:
            raise KeyError("Invalid or Unsupported Datarate.")

    def enable_CRC(self, enable_CRC = False):
        modem_config_2 = self.read_register(REG_FEI_LSB)
        config = modem_config_2 | 0x04 if enable_CRC else modem_config_2 & 0xfb
        self.write_register(REG_FEI_LSB, config)

    def invert_IQ(self, invert_IQ):
        self._parameters["invertIQ"] = invert_IQ

        if invert_IQ:
            self.write_register(
                REG_INVERTIQ,
                (
                    (
                        self.read_register(REG_INVERTIQ)
                        & RFLR_INVERTIQ_TX_MASK
                        & RFLR_INVERTIQ_RX_MASK
                    )
                    | RFLR_INVERTIQ_RX_ON
                    | RFLR_INVERTIQ_TX_ON
                ),
            )
            self.write_register(REG_INVERTIQ2, RFLR_INVERTIQ2_ON)
        else:
            self.write_register(
                REG_INVERTIQ,
                (
                    (
                        self.read_register(REG_INVERTIQ)
                        & RFLR_INVERTIQ_TX_MASK
                        & RFLR_INVERTIQ_RX_MASK
                    )
                    | RFLR_INVERTIQ_RX_OFF
                    | RFLR_INVERTIQ_TX_OFF
                ),
            )
            self.write_register(REG_INVERTIQ2, RFLR_INVERTIQ2_OFF)
    
    def set_sync_word(self, sw):
        self.write_register(REG_SYNC_WORD, sw)

    def dump_registers(self):
        for i in range(128):
            print("0x{:02X}: {:02X}".format(i, self.read_register(i)), end="")
            if (i + 1) % 4 == 0:
                print()
            else:
                print(" | ", end="")

    def implicit_header_mode(self, implicit_header_mode = False):
        self._implicit_header_mode = implicit_header_mode
        
        modem_config_1 = self.read_register(REG_FEI_MSB)
        config = (modem_config_1 | 0x01 
                if implicit_header_mode else modem_config_1 & 0xfe)

        self.write_register(REG_FEI_MSB, config)

    def receive(self, size = 0):
        
#        print("--------------------> receive() size=",size)
#        print("FIFO_TX_BASE_ADDR,   FIFO_RX_BASE_ADDR    = ",self.read_register(0x0e),self.read_register(0x0f))
#        print("                     FIFO_RX_CURRENT_ADDR = ",self.read_register(0x10))
#        print("FIFO_PAYLOAD_LENGTH, FIFO_RX_BYTES_NB     = ",self.read_register(0x22),self.read_register(0x13))
#        print("FIFO_MAX_PAYLOAD_LENGTH                   = ",self.read_register(0x23))
#        print("FIFO_ADDR_PTR                             = ",self.read_register(0x0d))       
        
        self.implicit_header_mode(size > 0)
 
        if size > 0: 
            self.write_register(REG_PAYLOAD_LENGTH, size & 0xff)
        # The last packet always starts at FIFO_RX_CURRENT_ADDR
        # no need to reset FIFO_ADDR_PTR
        self.write_register(
            REG_OP_MODE, MODE_LONG_RANGE_MODE | MODE_RX_CONTINUOUS
        )

    def on_receive(self, callback):
        self._on_receive = callback

        if self._pin_rx_done:
            if callback:
                print("callback attached")
                self.write_register(REG_DIO_MAPPING_1, 0x00)
                self._pin_rx_done.irq(
                    trigger=Pin.IRQ_RISING, handler = self.handle_on_receive
                )
            else:
                self._pin_rx_done.detach_irq()

####################################################################################################
                
    def MAC_LinkADRAns(self):
        
        fc=self.data['FrameCounter']+1
        self._frame_counter=fc.to_bytes(2,'little')
        self.data['FrameCounter'] = fc
        with open('data.txt','w') as json_file:
          json.dump(self.data,json_file)

        lora_pkt = bytearray(64)
        lora_pkt[0] = 0x40                     # MHDR = unconfirmed data uplink
        lora_pkt[1] = self._ttn.dev_addr[3]    # device address
        lora_pkt[2] = self._ttn.dev_addr[2]
        lora_pkt[3] = self._ttn.dev_addr[1]
        lora_pkt[4] = self._ttn.dev_addr[0]
        lora_pkt[5] = 0x82    # FCtrl:  ADR=1 ACK=1 FOptsLen=1
        
        lora_pkt[6] = self._frame_counter[0]
        lora_pkt[7] = self._frame_counter[1]
        print(self._frame_counter[0],self._frame_counter[1])

        aes = AES(
           self._ttn.dev_addr,
           self._ttn.app_s_key,
           self._ttn.net_s_key,
           self._frame_counter
        )

        aes.frame_counter=self._frame_counter
        
        lora_pkt[8] = 0x03      # LinkADRAns
        lora_pkt[9]=0x07
        # FPort - port field
        #lora_pkt[8] = self._fport
        #lora_pkt[10] = 0      # port=0 pois são apenas comandos MAC
        # Set length of LoRa packet
        
        lora_pkt_len = 10

# MIC is calculated over: MHDR | FHDR | FPort | FRMPayload
        mic = bytearray(4)
        mic = aes.calculate_mic(lora_pkt, lora_pkt_len, mic)
        #print("     mic:",''.join('{:02x}'.format(x) for x in mic))

        # Load MIC in package
        lora_pkt[lora_pkt_len : lora_pkt_len + 4] = mic[0:4]
        # Recalculate packet length (add MIC length)
        lora_pkt_len += 4

        #print("      MAC_LinkADRAns():     lora_pkt:",''.join('{:02x}'.format(x) for x in lora_pkt))
        print("      MAC_LinkADRAns():     len(lora_pkt):",len(lora_pkt))

        self.send_packet(lora_pkt, lora_pkt_len, 5)   # 5 = timeout
                

    def MAC_DevStatusAns(self,snr):
        
        fc=self.data['FrameCounter']+1
        self._frame_counter=fc.to_bytes(2,'little')
        self.data['FrameCounter'] = fc
        with open('data.txt','w') as json_file:
          json.dump(self.data,json_file)

        lora_pkt = bytearray(64)
        lora_pkt[0] = 0x40                     # MHDR = unconfirmed data uplink
        lora_pkt[1] = self._ttn.dev_addr[3]    # device address
        lora_pkt[2] = self._ttn.dev_addr[2]
        lora_pkt[3] = self._ttn.dev_addr[1]
        lora_pkt[4] = self._ttn.dev_addr[0]
        lora_pkt[5] = 0x82    # FCtrl:  ADR=1 ACK=1 FOptsLen=1
        
        lora_pkt[6] = self._frame_counter[0]
        lora_pkt[7] = self._frame_counter[1]
        #print(self._frame_counter[0],self._frame_counter[1])

        aes = AES(
           self._ttn.dev_addr,
           self._ttn.app_s_key,
           self._ttn.net_s_key,
           self._frame_counter
        )

        aes.frame_counter=self._frame_counter
        
        lora_pkt[8] = 0x06      # LinkADRAns
        lora_pkt[9]=0xff
        lora_pkt[10]=snr&0x3f
        
        # FPort - port field
        #lora_pkt[8] = self._fport
        #lora_pkt[10] = 0      # port=0 pois são apenas comandos MAC
        # Set length of LoRa packet
        
        lora_pkt_len = 11

# MIC is calculated over: MHDR | FHDR | FPort | FRMPayload
        mic = bytearray(4)
        mic = aes.calculate_mic(lora_pkt, lora_pkt_len, mic)
        #print("     mic:",''.join('{:02x}'.format(x) for x in mic))

        # Load MIC in package
        lora_pkt[lora_pkt_len : lora_pkt_len + 4] = mic[0:4]
        # Recalculate packet length (add MIC length)
        lora_pkt_len += 4

        #print("      MAC_LinkADRAns():     lora_pkt:",''.join('{:02x}'.format(x) for x in lora_pkt))
        print("      MAC_LinkADRAns():     len(lora_pkt):",len(lora_pkt))

        self.send_packet(lora_pkt, lora_pkt_len, 5)   # 5 = timeout


    def handle_on_receive(self, event_source):
        self.set_lock(True)              # lock until TX_Done
        aes = AESnew(self._ttn.dev_eui,self._ttn.app_eui,self._ttn.app_key)
        dec = None

        irqFlags = self.get_irq_flags() # should be 0x50
        if (irqFlags & IRQ_PAYLOAD_CRC_ERROR_MASK) == 0:
            if self._on_receive:
                payload = self.read_payload()
                self.set_lock(False)     # unlock when done reading
                if (irqFlags & IRQ_RX_DONE_MASK):
                  print("SX127x.handle_on_receive(): RX payload=",''.join('{:02x}'.format(x) for x in payload))
                  #print(payload[1],self._ttn.dev_addr[3])
                  #print(payload[2],self._ttn.dev_addr[2])
                  #print(payload[3],self._ttn.dev_addr[1])
                  #print(payload[4],self._ttn.dev_addr[0])
                  
                  MHDR = payload[0]

                  DevAddr=bytearray(4)
                  DevAddr[0]=payload[4]
                  DevAddr[1]=payload[3]
                  DevAddr[2]=payload[2]
                  DevAddr[3]=payload[1]
                  FCntDown=payload[6]+payload[7]*256  # Assim ou ao contrário
                  
                  FCtrl = payload[5]
                  FOptsLen = FCtrl&0x0f
                  
                  print("      DevAddr =",''.join('{:02x}'.format(x) for x in DevAddr)," FCntDown=%04x"%FCntDown," FCtrl=%02x"%FCtrl)
                  
                  # FOpts[0..15]
                  
                  if MHDR&0xe0==0x20:
                    print("      MType==1  ==>  Join accept")
                    aes.decrypt_join_accept(payload,self._dev_nonce,self._ttn)
                  
                  if MHDR&0xe0==0x60:
                      # A mensagem é para este Device Address?
                      if payload[1]==self._ttn.dev_addr[3] and payload[2]==self._ttn.dev_addr[2] and payload[3]==self._ttn.dev_addr[1] and payload[4]==self._ttn.dev_addr[0]:
                          print("      MType==3  ==>  Unconfirmed data down")
                             #print("Antes  ---","      aes._app_key:",''.join('{:02x}'.format(x) for x in aes._app_key))
                             # PRV: ERRO: Não devia ser neccessário" Por isso é prceso fazer sempre isto
                          aes._app_key=self._ttn.app_s_key
                             #aes._app_key=bytearray([0xB9, 0xB6, 0xB9, 0xA1, 0xAC, 0x2B, 0x4E, 0x1D, 0x06, 0x59, 0x77, 0x00, 0x1C, 0x1C, 0xE9, 0x92])
                             #print("Depois ---","      aes._app_key:",''.join('{:02x}'.format(x) for x in aes._app_key))
                          (dec,port)=aes.decrypt_payload(payload)
                          #print("     Mess:",''.join('{:02x}'.format(x) for x in dec))
                             
                          if(FOptsLen>0):
                              CID=payload[8]
                              print("      FOptsLen= ",FOptsLen," CID =",CID)
                              if(CID==0x06):
                                  snr=self.read_register(0x19)/4
                                  rssi=-159+self.read_register(0x1a)
                                  print("      MAC_DevStatusAns() - (CID,SNR,rssi) =",CID,snr,round(snr),rssi )
                                  self.MAC_DevStatusAns(round(snr))
                                  
                              if(CID==0x03):
                                  print("      MAC_LinkADRAns()   - (CID) =",CID)
                                  self.MAC_LinkADRAns()
                             
                             
                      else:
                             print("      MType==3  ==>  Unconfirmed data down - NOT FOR THIS DEVICE")

                      
                      #DEBUG1#if(payload[5] & 0x80):
                      #DEBUG1#    print("     .......... ADR=1")
                      #DEBUG1#if(payload[5] & 0x40):
                      #DEBUG1#    print("     .......... RFR=1")
                      #DEBUG1#if(payload[5] & 0x20):
                      #DEBUG1#    print("     .......... ACK=1")
                      #DEBUG1#if(payload[5] & 0x10):
                      #DEBUG1#    print("     .......... FPending=1")
                             
                      # Frame control payload[5]: FCtrl   ADR ADRACKreq ACK FPending FOptsLen[3] FOptsLen[2] FOptsLen[1] FOptsLen[0]
                      # ADR=1       - The network control the data rate though appropriate MAC commands
                      # ADRACKreq=0 - ADR acknowledgent request bit
                      # ACK=0       - When receiving a confirmed data message the receiver shall respond with a message with ACK=1
                      # FPending=1  - The gateway has more data pending to be sent                      
                    
        self.set_lock(False)             # unlock in any case.
        self.collect_garbage()
        
        if dec != None:
            self._on_receive(dec,port)
        


    def received_packet(self, size = 0):
        irq_flags = self.get_irq_flags()

        self.implicit_header_mode(size > 0)
        if size > 0: 
            self.write_register(REG_PAYLOAD_LENGTH, size & 0xff)

        #if (irq_flags & IRQ_RX_DONE_MASK) and \
        #    (irq_flags & IRQ_RX_TIME_OUT_MASK == 0) and \
        #    (irq_flags & IRQ_PAYLOAD_CRC_ERROR_MASK == 0):

        if (irq_flags == IRQ_RX_DONE_MASK):  
            # RX_DONE only, irq_flags should be 0x40
            # automatically standby when RX_DONE
            return True
 
        elif self.read_register(REG_OP_MODE) != (MODE_LONG_RANGE_MODE | MODE_RX_SINGLE):
            # no packet received.
            # reset FIFO address / # enter single RX mode
            self.write_register(REG_FIFO_ADDR_PTR, FifoRxBaseAddr)
            self.write_register(
                REG_OP_MODE, 
                MODE_LONG_RANGE_MODE | MODE_RX_SINGLE
            )

    def read_payload(self):
        # set FIFO address to current RX address
        # fifo_rx_current_addr = self.read_register(REG_FIFO_RX_CURRENT_ADDR)
        self.write_register(
            REG_FIFO_ADDR_PTR, 
            self.read_register(REG_FIFO_RX_CURRENT_ADDR)
        )

        # read packet length
        if self._implicit_header_mode:
            packet_length = self.read_register(REG_PAYLOAD_LENGTH)  
        else:
            packet_length = self.read_register(REG_RX_NB_BYTES)

        payload = bytearray()
        for i in range(packet_length):
            payload.append(self.read_register(REG_FIFO))

        # PRV tem que passar a standby   ??? (não percebo após receber deixa de emitir)
        #self.write_register(0x01, 0x81)      # 0x81 (LORA mode)+(STDBY mode)


        self.collect_garbage()
        return bytes(payload)


    def read_register(self, address, byteorder = 'big', signed = False):
        response = self.transfer(address & 0x7f)
        return int.from_bytes(response, byteorder)

    def write_register(self, address, value):
#        print('SPI WRITE: %02x %02x'%(address,value))
        self.transfer(address | 0x80, value)

    def transfer(self, address, value = 0x00):
        response = bytearray(1)

        self._pin_ss.value(0)

        self._spi.write(bytes([address]))
        self._spi.write_readinto(bytes([value]), response)

        self._pin_ss.value(1)

        return response

    def blink_led(self, times = 1, on_seconds = 0.1, off_seconds = 0.1):
        for i in range(times):
            if self._led_status:
                self._led_status.value(True)
                utime.sleep(on_seconds)
                self._led_status.value(False)
                utime.sleep(off_seconds)

    def collect_garbage(self):
        gc.collect()
        #if __DEBUG__:
        #    print('[Memory - free: {}   allocated: {}]'.format(gc.mem_free(), gc.mem_alloc()))
