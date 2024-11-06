
device_config = {
    'miso':19,
    'mosi':27,
    'ss':18,
    'sck':5,
    'dio_0':26,
    'reset':23,
    'led':25, 
}

app_config = {
    'loop': 200,
    'sleep': 100,
}

lora_parameters = {
    'tx_power_level': 2, 
    'signal_bandwidth': 'SF7BW125',
    'spreading_factor': 7,    
    'coding_rate': 5,                 # 5
    'sync_word': 0x34, 
    'implicit_header': False,
    'preamble_length': 8,             # 8
    'enable_CRC': True,               # Estava False. Alterei para True
    'invert_IQ': False,
}

wifi_config = {
    'ssid':'',
    'password':''
}


"""
------------------- ttn - The Things Network -----------------------

APPLICATION
General information
   Application ID                           eitt2024
   Accesso MQTT:

      SUBSCRIBE (para obter as mensagens de uplink) - mosquitto_sub -h eu1.cloud.thethings.network -p 1883 -d -t "v3/eitt2024@ttn/devices/eui-70b3d57ed00678df/up" -u "eitt2024" -P "NNSXS.7H4R2QX7P3QPBNJHKO4Y5GZQ7D3M64LW5LLSULA.L3JVZYKVKNYKGVJQPQ75BI2RDFRJXKYPCTCMRA6LY2CXDSQQONEA"

      PUBLISH (para enviar mensagens de downlink "Mensagem de teste!") - mosquitto_pub -h eu1.cloud.thethings.network -p 1883 -d -t "v3/eitt2024@ttn/devices/eui-70b3d57ed00678df/down/replace" -u "eitt2024" -P "NNSXS.7H4R2QX7P3QPBNJHKO4Y5GZQ7D3M64LW5LLSULA.L3JVZYKVKNYKGVJQPQ75BI2RDFRJXKYPCTCMRA6LY2CXDSQQONEA" -m '{ "downlinks": [ { "f_port": 1, "frm_payload": "TWVuc2FnZW0gZGUgdGVzdGUh", "priority": "NORMAL" } ] }'
       
              frm_payload tem de ser a mensagem codificada em BASE64:
              codificar em windows executar o comando: powershell "[convert]::ToBase64String([Text.Encoding]::UTF8.GetBytes(\"Mensagem de teste!\"))"
              codificar em linux   executar o comando: echo -n 'Mensagem de teste!' | base64     --> resultado = TWVuc2FnZW0gZGUgdGVzdGUh
      

DEVICE:
General information
   End device ID                eui-70b3d57ed00678df
   Frequency plan               Europe 863-870 MHz (SF9 for RX2 - recommended)
   LoRaWAN version              LoRaWAN Specification 1.0.4
   Regional Parameters version  RP002 Regional Parameters 1.0.4
Activation information        
   JoinEUI                      0000000000000000
   DevEUI                       70B3D57ED00678DF
   AppKey                       1027C2E6A71A0777E3F2E6545D5716FB
"""

ttn_config = {
  #OTAA
     'DevEUI':  bytearray([0x70, 0xB3, 0xD5, 0x7E, 0xD0, 0x06, 0x78, 0xDF]),
     'AppEUI':  bytearray([0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00]),
     'AppKey':  bytearray([0x10, 0x27, 0xC2, 0xE6, 0xA7, 0x1A, 0x07, 0x77, 0xE3, 0xF2, 0xE6, 0x54, 0x5D, 0x57, 0x16, 0xFB]),

    'DeviceAdress':      bytearray([ 0x26, 0x0B, 0x4b, 0x75 ]),
    'NetworkSessionKey': bytearray([0xCF, 0xA2, 0x86, 0xB3, 0xF7, 0x26, 0x32, 0x23, 0x64, 0xB9, 0x09, 0xFB, 0xD9, 0xCD, 0x0D, 0x2A]),

  #COUNTRY
    'country':           'EU',
    
}

