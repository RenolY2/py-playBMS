import struct


class DataReader():
    def __init__(self, fileobj):
        self.filehandle = fileobj
        
    def byte(self):
        data = self.filehandle.read(1)
        return struct.unpack("B", data)[0]
    
    def ubyte(self):
        data = self.filehandle.read(1)
        return struct.unpack("B", data)[0]
        
    def int(self):
        data = self.filehandle.read(4)
        return struct.unpack(">I", data)[0]
    
    def uint(self):
        data = self.filehandle.read(4)
        return struct.unpack(">i", data)[0]
    
    def short(self):
        data = self.filehandle.read(2)
        return struct.unpack(">H", data)[0]
    
    def ushort(self):
        data = self.filehandle.read(2)
        return struct.unpack(">h", data)[0]
    
    def float(self):
        data = self.filehandle.read(4)
        return struct.unpack(">F", data)[0]
    
    def ufloat(self):
        data = self.filehandle.read(4)
        return struct.unpack(">f", data)[0]
    
    def char(self):
        data = self.filehandle.read(1)
        info = struct.unpack("c", data)[0]
        return info
    
    def char_array(self, length):
        info = []

        for i in range(0, length):
            info.append(self.char())

        return "".join(info)
    
    def byte_array(self, length):
        data = self.filehandle.read(length)
        byte_array = struct.unpack(str(length)+"B", data)

        return byte_array
    
    # an integer with 3 bytes
    def tripplet(self):
        data = chr(0x0) + self.filehandle.read(3)
        return struct.unpack(">I", data)[0]
    
    def tripplet_int(self):
        return self.tripplet