import struct
import os

class DataReader():
    def __init__(self, fileobj):
        self.hdlr = fileobj
    
        
    def byte(self):
        data = self.hdlr.read(1)
        return struct.unpack("B", data)[0]
    
    def ubyte(self):
        data = self.hdlr.read(1)
        return struct.unpack("B", data)[0]
        
    def int(self):
        data = self.hdlr.read(4)
        return struct.unpack(">I", data)[0]
    
    def uint(self):
        data = self.hdlr.read(4)
        return struct.unpack(">i", data)[0]
    
    def short(self):
        data = self.hdlr.read(2)
        return struct.unpack(">H", data)[0]
    
    def ushort(self):
        data = self.hdlr.read(2)
        return struct.unpack(">h", data)[0]
    
    def float(self):
        data = self.hdlr.read(4)
        return struct.unpack(">F", data)[0]
    
    def ufloat(self):
        data = self.hdlr.read(4)
        return struct.unpack(">f", data)[0]
    
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
        data = self.hdlr.read(len)
        bytes = struct.unpack(str(len)+"B", data)
        return bytes
    
    # an integer with 3 bytes
    def tripplet_int(self):
        data = chr(0x0) + self.hdlr.read(3)
        return struct.unpack(">I", data)[0]


        
        
   