#import pygame.midi.Output
from pygame.midi import Output


class Output(Output):#pygame.midi.Output):
    def set_pan(self, pan, channel):
        assert (0 <= channel <= 15)
        assert pan <= 127
        
        self.write_short(0xB0 + channel, 0x0A, pan)