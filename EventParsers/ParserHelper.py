

# The note off event contains no data, except for the least significant bits
# represening the polyphonic ID, so that all notes with that particular
# polyphonic ID can be turned off.
def parse_noteOff(bmsfile, read, strict, commandID):
    return (commandID & 0b111,)

# Several commands use three bytes of data and one byte for
# something else. Because Python's struct module does not have
# a way to parse three bytes at once, we need to do it as follows.
def parse_1Byte_1Tripplet(bmsfile, read, strict, commandID):
    byte = read.byte()
    tripplet = read.tripplet()

    return (byte, tripplet)

# Variable-length delay
def parse_VL_delay(bmsfile, read, strict, commandID):
    start = bmsfile.tell()

    value = read.byte()

    while (value >> 7) == 1:
        value = read.byte()

    dataLen = bmsfile.tell() - start
    bmsfile.seek(start)

    data = read.byteArray(dataLen)

    return (data, )
