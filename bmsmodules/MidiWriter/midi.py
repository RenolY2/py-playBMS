import struct

from math import log, ceil
from cStringIO import StringIO


class MIDI(object):
    def __init__(self, track_amount, bpm):
        self.midi_file = StringIO()
        
        self.magic = "MThd"
        self.header_size = 6
        
        self.midi_format_version = 1
        self.track_amount = track_amount
        self.tempo = bpm
        
        self.midi_file.write(self.magic)
        self.midi_file.write(struct.pack(">IHHH", 
                                         self.header_size, self.midi_format_version,
                                         self.track_amount, self.tempo))
    
        self._current_track_length = 0
        self._track_data = None
    
    def write_action(self, time_passed, data):
        varlength_bytes = varlen_encode(time_passed)

        packed_varlength = struct.pack("B"*len(varlength_bytes), *varlength_bytes)
        
        self._track_data.write(packed_varlength)
        self._track_data.write(data)#append((packedVariableLength, data))
    
    def start_track(self):
        if self._track_data is not None:
            raise RuntimeError("You need to end the previous track before starting a new one!")
        
        header = "MTrk"
        self._current_track_length = 0
        self._track_data = StringIO()
    
    def note_on(self, time_passed, channel, note, velocity):
        assert channel <= 15
        
        note_data = struct.pack("Bbb", 0x90+channel, note, velocity)
        
        self.write_action(time_passed, note_data)
    
    def note_off(self, time_passed, channel, note, velocity):
        assert channel <= 15
        
        note_data = struct.pack("Bbb", 0x80+channel, note, velocity)
        
        self.write_action(time_passed, note_data)
    
    def set_instrument(self, time_passed, channel, instrument):
        assert channel <= 15
        assert 0 <= instrument <= 127
        
        note_data = struct.pack("BB", 0xC0+channel, instrument)
        
        self.write_action(time_passed, note_data)
    
    def set_pitch(self, time_passed, channel, pitch):
        assert channel <= 15
        
        # the 7 least significant bits come into the first data byte,
        # the 7 most significant bits come into the second data byte
        pitch_lsb = (pitch >> 7) & 127
        pitch_msb = pitch & 127
        
        #self.write_short(0xE0 + channel, pitch_lsb, pitch_msb)
        pitch_data = struct.pack("Bbb", 0xE0+channel, pitch_lsb, pitch_msb)
        
        self.write_action(time_passed, pitch_data)
    
    def set_meta_event(self, time_passed, meta_event_type, data):
        varlength_bytes = varlen_encode(len(data))
        
        meta_event_data = struct.pack("BB" + "B"*len(varlength_bytes), 0xFF,
                                      meta_event_type, *varlength_bytes)
        meta_event_data += data
        
        self.write_action(time_passed, meta_event_data)
    
    def set_tempo(self, time_passed, tempo):
        assert tempo <= 2**24-1
        
        tempo_byte1 = (tempo >> 16) & 0xFF
        tempo_byte2 = (tempo >> 8) & 0xFF
        tempo_byte3 = tempo & 0xFF
        
        data = struct.pack("BBB", tempo_byte1, tempo_byte2, tempo_byte3)
        
        self.set_meta_event(time_passed, 0x51, data)
        
    def program_event(self, time_passed, channel, program, value, two_bytes=False):
        assert channel <= 15
        
        if not two_bytes:
            assert value <= 127
            
            program_data = struct.pack("Bbb", 0xB0+channel, program, value)
        else:
            assert value <= 2**14-1
            
            value_msb = (value >> 7) & 127
            value_lsb = value & 127

            program_data = struct.pack("Bbbb", 0xB0+channel, program,
                                       value_lsb, value_msb)
        
        self.write_action(time_passed, program_data)

    def end_track(self, time_passed=0):
        end_of_track = struct.pack("BBB", 0xFF, 0x2F, 0x00)
        self.write_action(time_passed, end_of_track)
        
        track_data = self._track_data.getvalue()
        
        self.midi_file.write("MTrk")
        self.midi_file.write(struct.pack(">I", len(track_data)))
        self.midi_file.write(track_data)
        #for action in self.__track_data:
        #    time, data = action
        #    self.midi_file.write(time)
        #    self.midi_file.write(data)
        
        self._track_data = None

    def write_midi(self, fileobj):
        fileobj.write(self.midi_file.getvalue())
            

def varlen_encode(number):
    if number == 0:
        bytes_needed = 1
        data = [0b00000000]
        return data#struct.pack("B", 0b10000000)
    else:
        # The number of bytes we need to encode the variable length
        bytes_needed = max(
            int(ceil(log(number, 128))),
            1)
    
    data = []
    for i in reversed(xrange(bytes_needed)):
        byte = (number >> (i*7)) & 127
        data.append(byte | 0b10000000)
    #print data, number, bytes_needed
    last_byte = data[-1]
    data[-1] = last_byte & 127# 0b10000000
    
    return data

if __name__ == "__main__":
    my_midi = MIDI(2, 96)

    my_midi.start_track()
    my_midi.note_on(0, 0, 0x40, 0x40)
    my_midi.note_off(500, 0, 0x40, 0x40)

    my_midi.note_on(100, 0, 0x40, 0x40)
    my_midi.note_off(500, 0, 0x40, 0x40)
    my_midi.end_track()

    my_midi.start_track()
    my_midi.note_on(100, 0, 0x50, 0x40)
    my_midi.note_off(400, 0, 0x50, 0x40)

    my_midi.note_on(100, 0, 0x20, 0x40)
    my_midi.note_off(500, 0, 0x20, 0x40)
    my_midi.end_track()
    
    with open("myMidi_test.midi", "wb") as f:
        my_midi.write_midi(f)
    
    print "Done!"