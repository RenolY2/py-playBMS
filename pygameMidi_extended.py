#import pygame.midi.Output
from pygame.midi import Output


class Output(Output):#pygame.midi.Output):
    
    def set_pan(self, pan, channel):
        assert (0 <= channel <= 15)
        assert pan <= 127
        
        self.write_short(0xB0 + channel, 0x0A, pan)
    
    def set_volume(self, volume, channel):
        assert (0 <= channel <= 15)
        assert volume <= 127
        
        self.write_short(0xB0 + channel, 0x07, volume)
        
    def set_pitch(self, pitch, channel):
        assert (0 <= channel <= 15)
        assert pitch <= (2**14-1)
        
        # the 7 least significant bits come into the first data byte,
        # the 7 most significant bits come into the second data byte
        pitch_lsb = (pitch >> 7) & 127
        pitch_msb = pitch & 127
        
        self.write_short(0xE0 + channel, pitch_lsb, pitch_msb)
    
    def set_instrument_bank(self, bank, channel):
        assert (0 <= channel <= 15)
        assert bank <= 127
        
        self.write_short(0xB0 + channel, 0x00, bank)