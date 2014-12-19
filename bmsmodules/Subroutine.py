from Events import Events


class Subroutine(object):
    def __init__(self, 
                 bmsHandle, readObj,
                 trackID, uniqueTrackID,
                 offset, eventParser):
        
        self.bmsHandle = bmsHandle
        self.read = readObj
        
        self.trackID = trackID
        self.uniqueTrackID = uniqueTrackID
        
        self.offset = offset
        self.read.hdlr.seek(offset)
        
        self.delay_countdown = 0
        self.last_countdown = 0
        self.wasPaused = False
        
        # It is unknown whether the previous position
        # for the Goto/Return events works as a variable
        # holding a single value, or a list holding several
        # values from which the last one is used.
        #self.previousPositions = []
        self.previousPositions = 0
        
        
        self.__parser__ = eventParser
        
        self.BPM = 100
        self.PPQN = 100
        
        self._enabled_PolyphIDs = {}
    
    
    # Keeping track of enabled polyphonic IDs and their notes
    def set_polyphID(self, ID, note):
        if ID not in self._enabled_PolyphIDs:
            self._enabled_PolyphIDs[ID] = [note]
        else:
            self._enabled_PolyphIDs[ID].append(note)
    
    def getNotes_byPolyphID(self, ID):
        if ID not in self._enabled_PolyphIDs:
            return []
        else:
            return self._enabled_PolyphIDs[ID]
    
    def turnOff_polyphID(self, ID):
        del self._enabled_PolyphIDs[ID]
        
        
        
        
    def parse_next_command(self, strict = True):
        return self.__parser__(self.read, self.bmsHandle, strict)
        
    def parse_iter(self):
        yield self.parse_next_command()
    
    
    def setPause(self, pauseLength):
        self.delay_countdown = pauseLength
        self.last_countdown = pauseLength
        self.wasPaused = True
    
    # To enforce delays in the subroutine, this
    # method will return False if no delay is set,
    # or True if the subroutine is on pause. When it is,
    # the delay will be counted down until it is 0 again
    # and the subroutine can continue playing notes again.
    def checkIfPaused(self):
        if self.delay_countdown > 0:
            self.delay_countdown -= 1
            
            if self.delay_countdown == 0:
                return False
            else:
                return True
        else:
            return False
    
    # The 0xC4 event sets the previous position to
    # the current position in the file. We will
    # return to this position on encountering a 0xC6 event.
    def setPreviousOffset(self):
        #self.previousPositions.append(self.read.hdlr.tell())
        self.previousPosition = self.read.hdlr.tell()
    
    # The 0xC6 event makes us go to the previous position.
    # When the previous position was set, it was already after
    # the 0xC4 event was parsed, so we do not have to worry
    # about hitting the event again.
    def goToPreviousOffset(self):
        #offset = self.previousPositions.pop()
        #self.goToOffset(offset)
        
        self.goToOffset(self.previousPosition)
    
    # A helper method so that we don't have to type so much
    # to make the subroutine go to a specific offset.
    def goToOffset(self, offset):
        self.read.hdlr.seek(offset)
