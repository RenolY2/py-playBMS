import struct

from math import log, ceil

from cStringIO import StringIO

class MIDI(object):
    def __init__(self, trackAmount, BPM):
        self.midi_file = StringIO()
        
        self.magic = "MThd"
        self.headerSize = 6
        
        self.midiFormatVersion = 1
        self.trackAmount = trackAmount
        self.tempo = BPM
        
        self.midi_file.write(self.magic)
        self.midi_file.write(struct.pack(">IHHH", 
                                         self.headerSize, self.midiFormatVersion,
                                         self.trackAmount, self.tempo))
    
        self.__current_track_length = 0
        self.__track_data = None
    
    def writeAction(self, timePassed, data):
        variableLength = VarLen_encode(timePassed)
        
        packedVariableLength = struct.pack("B"*len(variableLength), *variableLength)
        
        self.__track_data.write(packedVariableLength)
        self.__track_data.write(data)#append((packedVariableLength, data))
    
    def startTrack(self):
        if self.__track_data != None:
            raise RuntimeError("You need to end the previous track before starting a new one!")
        
        header = "MTrk"
        self.__current_track_length = 0
        self.__track_data = StringIO()
    
    def note_on(self, timePassed, channel, note, velocity):
        assert channel <= 15
        
        note_data = struct.pack("Bbb", 0x90+channel, note, velocity)
        
        self.writeAction(timePassed, note_data)
    
    def note_off(self, timePassed, channel, note, velocity):
        assert channel <= 15
        
        note_data = struct.pack("Bbb", 0x80+channel, note, velocity)
        
        self.writeAction(timePassed, note_data)
    
    def set_instrument(self, timePassed, channel, instrument):
        assert channel <= 15
        assert instrument >= 0 and instrument <= 127
        
        note_data = struct.pack("BB", 0xC0+channel, instrument)
        
        self.writeAction(timePassed, note_data)
    
    def set_pitch(self, timePassed, channel, pitch):
        assert channel <= 15
        
        # the 7 least significant bits come into the first data byte,
        # the 7 most significant bits come into the second data byte
        pitch_lsb = (pitch >> 7) & 127
        pitch_msb = pitch & 127
        
        #self.write_short(0xE0 + channel, pitch_lsb, pitch_msb)
        pitch_data = struct.pack("Bbb", 0xE0+channel, pitch_lsb, pitch_msb)
        
        self.writeAction(timePassed, pitch_data)
    
    def set_meta_event(self, timePassed, meta_event_type, data):
        dataLen = VarLen_encode(len(data))
        
        meta_event_data = struct.pack("BB" + "B"*len(dataLen), 0xFF, meta_event_type, *dataLen)
        meta_event_data += data
        
        self.writeAction(timePassed, meta_event_data)
    
    def set_tempo(self, timePassed, tempo):
        assert tempo <= 2**24-1
        
        tempo_byte1 = (tempo >> 16) & 0xFF
        tempo_byte2 = (tempo >> 8) & 0xFF
        tempo_byte3 = tempo & 0xFF
        
        data = struct.pack("BBB", tempo_byte1, tempo_byte2, tempo_byte3)
        
        self.set_meta_event(timePassed, 0x51, data)
        
        
        
    def program_event(self, timePassed, channel, program, value, twoBytes = False):
        assert channel <= 15
        
        if not twoBytes: 
            assert value <= 127
            
            program_data = struct.pack("Bbb", 0xB0+channel, program, value)
        else:
            assert value <= 2**14-1
            
            value_msb = (value >> 7) & 127
            value_lsb = value & 127
            print 
            program_data = struct.pack("Bbbb", 0xB0+channel, program,
                                       value_lsb, value_msb)
        
        self.writeAction(timePassed, program_data)
        
        
    
    def end_track(self, timePassed = 0):
        end_of_track = struct.pack("BBB", 0xFF, 0x2F, 0x00)
        self.writeAction(timePassed, end_of_track)
        
        _trackData = self.__track_data.getvalue()
        
        self.midi_file.write("MTrk")
        self.midi_file.write(struct.pack(">I", len(_trackData)))
        self.midi_file.write(_trackData)
        #for action in self.__track_data:
        #    time, data = action
        #    self.midi_file.write(time)
        #    self.midi_file.write(data)
        
       
        
        self.__track_data = None
    
        
        
    def write_midi(self, fileobj):
        fileobj.write(self.midi_file.getvalue())
            
    
    
    
    


def VarLen_encode(number):
    if number == 0:
        bytes_needed = 1
        data = [0b00000000]
        return data#struct.pack("B", 0b10000000)
    else:
        bytes_needed = max(int(ceil(log(number, 128))), 1)
    
    data = []
    for i in reversed(xrange(bytes_needed)):
        byte = (number >> (i*7)) & 127
        data.append(byte | 0b10000000)
    #print data, number, bytes_needed
    lastByte = data[-1]
    data[-1] = lastByte & 127# 0b10000000
    
    return data

if __name__ == "__main__":
    myMidi = MIDI(2, 96)
    
    myMidi.startTrack()
    myMidi.note_on(0, 0, 0x40, 0x40)
    myMidi.note_off(500, 0, 0x40, 0x40)
    
    myMidi.note_on(100, 0, 0x40, 0x40)
    myMidi.note_off(500, 0, 0x40, 0x40)
    myMidi.end_track()
    
    myMidi.startTrack()
    myMidi.note_on(100, 0, 0x50, 0x40)
    myMidi.note_off(400, 0, 0x50, 0x40)
    
    myMidi.note_on(100, 0, 0x20, 0x40)
    myMidi.note_off(500, 0, 0x20, 0x40)
    myMidi.end_track()
    
    with open("myMidi_test.midi", "wb") as f:
        myMidi.write_midi(f)
    
    print "Done!"
    
    
