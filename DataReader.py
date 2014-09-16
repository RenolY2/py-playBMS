import struct
import os

class DataReader():
    def __init__(self, fileobj):
        self.hdlr = fileobj
    
        
    def byte(self):
        data = self.hdlr.read(1)
        return struct.unpack("B", data)[0]
        
    def int(self):
        #Integer is 4 bytes, little endian
        data = self.hdlr.read(4)
        return struct.unpack(">I", data)[0]
    
    def short(self):
        #Short is 2 bytes, little endian
        data = self.hdlr.read(2)
        return struct.unpack(">H", data)[0]
    
    def float(self):
        data = self.hdlr.read(4)
        return struct.unpack(">F", data)[0]
    
    def char(self):
        data = self.hdlr.read(1)
        info = struct.unpack("c", data)[0]
        return info
    
    def charArray(self, len):
        info = []
        for i in range(0,len):
            info.append(self.char())
        return "".join(info)
    

    
    def byteArray(self, len):
        self.index += len
        data = self.hdlr.read(len)
        bytes = struct.unpack(str(len)+"B", data)
        return bytes
    
    # an integer with 3 bytes
    def tripplet_int(self):
        data = chr(0x0) + self.hdlr.read(3)
        return struct.unpack(">I", data)[0]


        
        
   