import utime
from sx127x import TTN, SX127x



class loraCOM:

    def __init__(self,rx_handler):
        print("loraCOM.__init__()   [2024-05-28 - LoRaWAN TX.RX_MOONITOR_20240528_1300_V8]")
        self.lora = SX127x()
        self.lora.on_receive(self.on_receive)
        self.lora.receive()
        self.rx_handler=rx_handler


    def on_receive(self, mess, port):
        
        if len(mess)>0:
            self.rx_handler(mess, port)
        
        """
        print('--------> on_receive() <---------')
        payload = lora.read_payload()
        res=""
        for b in payload:
            res += "%02X" % b
        print(res)
        res=""
        for b in outgoing:
            res += "%02X" % b
        print(res)
        """


    def join(self,tentativas=5,delay=10):
        print("loraCOM.join()")
        count=0
        for n in range(tentativas):
            for d in range(delay):
               if(d==0):
                  self.lora.send_join_request()
                  print("      Sending join_request (%d) " % (n+1)) 
               utime.sleep(1)
               if(self.lora._ttn.join_accept):
                  return(True)
        return(False)


    def send_message(self,payload,port):
        print("loraCOM.send_message(\"%s\",%d)"%(payload,port))
        self.lora.send_message(payload,port)
