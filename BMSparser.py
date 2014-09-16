import pygame
import time
import pygame.midi

from DataReader import DataReader


class BMS_Track(object):
    def __init__(self, fileobj = None):
        self.bmsfile = fileobj
        
        self.tracks = {}
        self.midiOutput = pygame.midi.Output(0)
        
        if fileobj == None:
            self.read = None
        else:
            self.read = DataReader(self.bmsfile)
    
    def load_bms_file(self, fileobj):
        self.bmsfile = fileobj
        self.read = DataReader(self.bmsfile)
    
    def parseTrack(self, offset = 0, callbacks = {}):
        bmsfile = self.bmsfile
        read = self.read
        
        bmsfile.seek(offset)
        
        trackData = []
        
        
        while True:
            command = read.byte()
            
            original_pos = bmsfile.tell()
            if command in callbacks:
                callbacks[command](self, command, bmsfile, read)
                bmsfile.seek(original_pos)
            
            if command == 0xA4: # Unknown
                read.byte()
                read.byte()
            
            if command == 0xAA: # Unknown
                read.int()
                
                
            elif command == 0xAC: # Unknown
                read.byte()
                read.byte()
                read.byte()
            
            elif command == 0xA0: # Unknown
                read.short()
            
            elif command == 0xA6: # Unknown
                pass
            
            elif command == 0xB1: # Unknown
                read.int()
            
            elif command == 0xB8: # Global speakers
                action = read.byte()
                
                if action == 0x1: # Volume change
                    read.byte()
                elif action == 0x2: # Reverb
                    read.byte()
                elif action == 0x3: # Pan
                    read.byte()
                else:
                    read.byte()
            
            elif command == 0xB9: # Pitch bend
                action = read.byte()
                
                if action == 0x1: # Add PitchEvent
                    read.byte()
                else:
                    read.byte()
            
            elif command == 0xB8: # Unknown
                read.short()
                
            elif command == 0xC1: # Track List Num + Offset
                trackNum = read.byte()
                trackOffset = read.tripplet_int()
            
            elif command == 0xC2: # Unknown
                read.byte()
            
            elif command == 0xC3: # Reference
                read.tripplet_int()
            
            elif command == 0xC4: # Loop call
                read.tripplet_int()
            
            elif command == 0xC5: # Jump back to reference marker
                #read.tripplet_int()
                pass
            
            elif command == 0xC6: # Unknown
                read.byte()
            
            elif command == 0xC7: # Loop to offset
                read.byte()
                read.tripplet_int()
            
            elif command == 0xC8: # Unknown
                read.int()
            
            elif command == 0xCC: # Unknown
                read.byte()
                read.byte()
                
            elif command == 0xD0: # Unknown
                read.short()
            
            elif command == 0xD1: # Unknown
                read.short()
            
            elif command == 0xD5: # Unknown
                read.short()
            
            elif command == 0xD8: #Articulation
                action = read.byte()
                value = read.short()
                
                if action == 0x62:
                    pass # change time resolution
                elif action == 0x6E: 
                    pass # Vibrato Event
                
                
            elif command == 0xE0: # Tempo
                read.short()
                
            elif command == 0xE2: # Bank select
                read.byte()
            
            elif command == 0xE3: # Instrument change
                read.byte()
            
            elif command == 0xE7: # Unknown
                read.short()
            
            elif command == 0xF0: # Delay
                start = bmsfile.tell()
                
                value = read.byte()
                while value >= 0x80:
                    value = read.byte()
                
                dataLen = bmsfile.tell() - start
                #bmsfile.seek(dataLen)
                
                #data = read.byteArray(dataLen)
            
            elif command == 0xF9: # Unknown
                read.short()    
            
            elif command == 0xFD: # Marker
                start = bmsfile.tell()
                
                value = read.byte()
                while value != 0x00:
                    value = read.byte()
                
                dataLen = bmsfile.tell() - start
                #bmsfile.seek(dataLen)
                
                #data = read.byteArray(dataLen)
            
            elif command == 0xFE:
                read.short()
            
            elif command == 0xFF: # End of Track
                break
            
            else:
                position = bmsfile.tell()
                raise RuntimeError("Unknown Command {0} at offset {1} ({2})".format(hex(command),
                                                                              position, hex(int(position))))
                   
            print "Parsed track", hex(command), hex(int(bmsfile.tell()))

if __name__ == "__main__":
    pygame.midi.init()
    
    with open("pikmin_bms/ff_treasureget.bms", "rb") as f:
        bms = BMS_Track(f)
        
        bms.parseTracks()
    
    print "done"
    pygame.midi.quit()