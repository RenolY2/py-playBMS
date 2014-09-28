import time
import StringIO


import pygame

from BMSparser import BMS_Track, EndOfTrack
from DataReader import DataReader


class Subroutine(object):
    def __init__(self, 
                 bmsHandle, trackID, uniqueTrackID,
                 offset):
        
        self.bmsHandle = bmsHandle
        
        self.trackID = trackID
        self.uniqueTrackID = uniqueTrackID
        
        self.offset = offset
        self.read = DataReader(bmsHandle)
        self.read.hdlr.seek(offset)
        
        self.delay_countdown = 0
    
    
    """# A helper function that reads and handles the next 
    # event. It is less flexible than parsing and handling
    # the events separately because you can't simply iterate 
    # over all events in the file.
    def handle_next_event(self):
        commandID, args = self.parse_next_event()
        
        self.handle_command(commandID, args)
    
    
    def handle_command(self, commandID, args):
        pass"""
    
    def parse_iter(self):
        yield self.parse_next_command()
    
    def seek(self, offset):
        self.offset = offset
        self.read.hdlr.seek(offset)
    
    
    def setPause(self, pauseLength):
        self.delay_countdown = pauseLength
    
    # To enforce delays in the subroutine, this
    # method will return False if no delay is set,
    # or True if the subroutine is on pause. When it is,
    # the delay will be counted down until it is 0 again
    # and the subroutine can continue playing notes again.
    def checkIfPaused(self):
        if self.delay_countdown > 0:
            self.delay_countdown -= 1
            return True
        else:
            return False
    
    # This function is very long because it
    # contains the code to parse (almost) all the events
    # that can be encountered in a Pikmin 2 BMS file.    
    def parse_next_command(self):
        read = self.read
        bmsfile = self.bmsHandle
        
        valuePos = int(bmsfile.tell())
        value = read.byte()
        
        # We will store arguments for callback functions
        # in the args variable. Some controller events might
        # not have any arguments, so the variable will be
        # None, but otherwise it will be redefined by
        # the parsers for the controller events.
        args = None
        
        currPos = int(bmsfile.tell())
        
        if value <= 0x7F: 
            # Values below and equal to 127 are note-on events
            # Depending on the value, they turn on specific notes.
            
            note_on_event = value
            polyphonicID = read.byte()
            volume = read.byte()
            
            args = (note_on_event, polyphonicID, volume)
            
            # Generally, polyphonic IDs should range from 1 to 7,
            # but in some special cases it is possible that they range from 0 up to 15,
            # mostly only directly after a 0xB1 controller event.
            # This could be due to malformed data, needs more investigation.
            if polyphonicID > 0xF:
                position = bmsfile.tell()
                raise RuntimeError("Invalid Polyhponic ID ({0}) at offset {1} ({2})".format(hex(polyphonicID),
                                                                                            position,
                                                                                            hex(position))
                                   )
                
            
            #print "Reading note {0} with polyphonic ID {1} ({3}) and volume {2}".format(hex(note_on_event),
            #                                                                      polyphonicID,
            #                                                                      volume, polyphonicID & 0b111)
            return note_on_event, args
        
        else:
            # Values above 127 are controller events.
            # They can change the flow of the music sequence,
            # initiate additional tracks or turn off notes with
            # a specific polyphonic ID.
            controlEventID = value
            
            
            if controlEventID == 0x80: # Delay, up to 0xFF (255) ticks
                delayLength_inTicks = read.byte()
                
                args = (delayLength_inTicks, )
            
            elif controlEventID >= 0x81 and controlEventID <= 0x87: # note-off event
                # Each ID refers to a specific polyphonic ID.
                # 0x81 refers to 1, 0x82 refers to 2, etc.
                #
                # We can retrieve the correct ID by taking
                # the three least significant bits of the byte.
                polyphonicID = controlEventID & 0b111 
                
                args = (polyphonicID, )
                
                #print "Turning off note with polyphonic ID {0}".format(polyphonicID)
                
            elif controlEventID == 0x88: # Delay, up to 0xFFFF (65535) ticks
                delayLength_inTicks = read.short()
                
                args = (delayLength_inTicks, )
            
            elif controlEventID == 0x98: # Unknown
                # The data might either be two seperate
                # bytes or a single short.
                unknown1 = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, unknown2)
            
            elif controlEventID == 0x9A: # Pan Change
                unknown1 = read.byte()
                pan = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, pan, unknown2)
            
            elif controlEventID == 0x9C: # Volume Change
                unknown1 = read.byte()
                volume = read.byte()
                
                args = (unknown1, volume)
            
            elif controlEventID == 0x9E: # Pitch Shift
                unknown1 = read.byte()
                pitch = read.ushort()
                unknown2 = read.byte()
                
                args = (unknown1, pitch, unknown2)
                
            elif controlEventID == 0xA0: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
                
            elif controlEventID == 0xA3: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
                
            elif controlEventID == 0xA4: # Bank Select/Program Select
                unknown1 = read.byte()
                
                if unknown1 == 32:
                    instrument_bank = read.byte()
                    args = (unknown1, instrument_bank)
                    
                elif unknown1 == 33:
                    program = read.byte()
                    args = (unknown1, program)
                    
                else:
                    unknown2 = read.byte()
                    args = (unknown1, unknown2)
                    
            
            elif controlEventID == 0xA5: # Unknown
                unknown1 = read.short()
                args = (unknown1, )
            
            elif controlEventID == 0xA6: # Unknown
                pass
            
            elif controlEventID == 0xA7: # Unknown
                unknown1 = read.short()
                args = (unknown1, )
            
            elif controlEventID == 0xA9: # Unknown
                unknown1 = read.int()
                args = (unknown1, )
            
            elif controlEventID == 0xAA: # Unknown
                unknown1 = read.int()
                args = (unknown1, )
                
            elif controlEventID == 0xAC: # Unknown
                # Could be a single 3 bytes integer,
                # 3 separate bytes, or one byte and one
                # short integer.
                unknown1 = read.byte()
                unknown2 = read.byte()
                unknown3 = read.byte()
                
                args = (unknown1, unknown2, unknown3)
            
            # This controller event seems to be used
            # only by se.bms, though I have not yet
            # figured out whether it has two or three
            # bytes of data.
            #
            #elif controlEventID == 0xAD: # Unknown
            #    #read.byte()
            #    #read.short()
            #"""
            
            elif controlEventID == 0xB1: # Unknown
                #read.int()
                unknown1 = read.byte()
                args = (unknown1, )
            
            elif controlEventID == 0xB8: # Unknown
                unknown1 = read.short()
                args = (unknown1, )
                
            elif controlEventID == 0xC1: # Track List Num + Offset
                newTrackNum = read.byte()
                newTrackOffset = read.tripplet_int()
                
                args = (newTrackNum, newTrackOffset)
            
            elif controlEventID == 0xC2: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xC4: # Goto a specific offset
                goto_offset = read.int()
                
                args = (goto_offset, )
            
            elif controlEventID == 0xC5: # Unknown
                # In JAudio Player this was a 'Jump back
                # to reference' marker
                #read.tripplet_int()
                pass
            
            elif controlEventID == 0xC6: # Return to previous position
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xC7: # Unknown
                # In JAudio Player this was 'loop to offset'
                unknown1 = read.byte()
                unknown2 = read.tripplet_int()
                
                args = (unknown1, unknown2)
            
            elif controlEventID == 0xC8: # Loop to offset
                #read.byte()
                #read.tripplet_int()
                loop_offset = read.int()
                
                args = (loop_offset, )
            
            elif controlEventID == 0xCB: # Unknown
                unknown1 = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, unknown2)
            
            elif controlEventID == 0xCC: # Unknown
                unknown1 = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, unknown2)
                
            elif controlEventID == 0xCF: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
                
            elif controlEventID == 0xD0: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xD1: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
                
            elif controlEventID == 0xD5: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xDA: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xDB: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
                
            elif controlEventID == 0xDF: # Unknown
                unknown1 = read.byte()
                unknown2 = read.tripplet_int()
                
                args = (unknown1, unknown2)
                
            elif controlEventID == 0xE0: # Unknown
                # In JAudio Player this was Tempo with 
                # two bytes of data.
                # In Pikmin 2 it could be three bytes of data.
                unknown1 = read.byte()
                unknown2 = read.short()
                
                args = (unknown1, unknown2)
            
            elif controlEventID == 0xE1: # Unknown
                pass
            
            elif controlEventID == 0xE3: # Unknown 
                # In JAudio Player this was Instrument change with 
                # one byte of data.
                # In the Pikmin 2 bms file it seems to be something
                # else, no data follows it.
                pass
            
            elif controlEventID == 0xE6: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
                
            elif controlEventID == 0xE7: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xEF: # Unknown
                unknown1 = read.byte()
                unknown2 = read.byte()
                unknown3 = read.byte()
                
                args = (unknown1, unknown2, unknown3)
            
            elif controlEventID == 0xF0: # Delay (variable-length quantity)
                start = bmsfile.tell()
                
                value = read.byte()
                
                # The most significant bit in the value
                # tells us that we need to read another byte.
                # We keep doing it until the most significant 
                # bit in the new value stops being 1 (i.e., 0).
                while (value >> 7) == 1:
                    value = read.byte()
                
                dataLen = bmsfile.tell() - start
                bmsfile.seek(start)
                
                data = read.byteArray(dataLen)
                
                args = (data, )
            
            elif controlEventID == 0xF1: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xF9: # Unknown
                unknown1 = read.short()    
                
                args = (unknown1, )
                
            elif controlEventID == 0xFD: # Unknown
                # In JAudio Player, this was a Marker event
                # with variable length.
                # In Pikmin 2 it is just two bytes of data.
                
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xFE: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
                
            elif controlEventID == 0xFF: # End of Track
                pass
            
            else:
                position = bmsfile.tell()
                raise RuntimeError("Unknown controlEventID {0} "
                                   "at offset {1} ({2})".format(hex(controlEventID),
                                                                valuePos, hex(valuePos)))
        return controlEventID, args
    
    
    
class BMS(object):
    # BPM is beats per minute, PPQN is pulses per quarter note,
    # as according to MIDI specs.
    def __init__(self, fileobj, midiOutput, BPM = 120, PPQN = 96):
        self.bmsFile = fileobj
        
        # We will read the entire file into memory
        # so that we can create several file-like objects
        # with different file positions.
        self.bmsData = self.bmsFile.read()
        
        self.midiOutput = midiOutput
        
        self.BMSTrack = BMS_Track(fileobj, midiOutput)
        
        self.BMS_tracks = []
        
        # Microseconds per minute
        MSPM = 60000000.0
        # Microseconds per quarter note
        MPQN = MSPM / BPM
        
        self.tempo = BPM
        self.waitTime = (MPQN/1000000)/PPQN
        
        # The main subroutine does not have a specified
        # track ID in the BMS file, so we initiate the
        # subroutine with None as it's track ID.
        self.addSubroutine(trackID = None, offset = 0)
        
        self.stoppedTracks = {}
        #self.collectTrackInfo()
        
    def addSubroutine(self, trackID, offset):
        print "Added track",trackID
        # Create a buffer instance so that we can avoid
        # copying the same data several times.
        bmsHandle = StringIO.StringIO(buffer(self.bmsData))
        
        uniqueTrackID = len(self.BMS_tracks)
        subroutine = Subroutine(bmsHandle, trackID, uniqueTrackID,
                                offset)
        
        self.BMS_tracks.append(subroutine)
        
        
        
    
    # This function does the main work of iterating over the commands
    # from each subroutine and executing them.
    def bmsEngine_run(self):
        trackStopped = False
        while not trackStopped:
            subroutines_to_be_added = []
            
            for subroutine in self.BMS_tracks:
                current_trackID = subroutine.trackID
                current_uniqueTrackID = subroutine.uniqueTrackID
                
                if current_uniqueTrackID in self.stoppedTracks:
                    # The track already ended, so we do not have to check
                    # it anymore.
                    continue
                
                # We will check if the subroutine is currently paused,
                # to avoid parsing events too early.
                if subroutine.checkIfPaused() == True:
                    continue
                else:
                    command, args = subroutine.parse_next_command()
                
                print hex(command)
                
                # Delay events, the subroutine will be paused for a specific
                # amount of ticks
                if command in (0x80, 0x88):
                    delay = args[0]
                    print "Track {0} is paused for {1} ticks".format(current_uniqueTrackID,
                                                                     delay)
                    subroutine.setPause(delay)
                
                elif command == 0xC1:
                    trackID, offset = args
                    print trackID, offset
                    
                    subroutines_to_be_added.append((trackID, offset))
                    
                elif command == 0xFF:
                    self.stoppedTracks[current_uniqueTrackID] = True
                    print "Reached end of track", current_uniqueTrackID
            
            for trackID, offset in subroutines_to_be_added:
                self.addSubroutine(trackID, offset)
            
            time.sleep(self.waitTime)
                    
                
            
            
        
    """def collectTrackInfo(self):
        try:
            self.BMSTrack.parseTrack(callbacks = {0xC1 : self.event_getTracks},
                                     terminateTrack_callback = self.event_getTrackLength)
        except EndOfTrack:
            pass
        
        for track, trackData in self.BMS_tracks.iteritems():
            offset = trackData["offset"]
            try:
                self.BMSTrack.parseTrack(trackNum = track,
                                         trackOffset = offset,
                                         callbacks = {0xC1 : self.event_getTracks},
                                         terminateTrack_callback = self.event_getTrackLength)
            except EndOfTrack:
                pass
            
    def playBMS(self, trackNum):
        offset = self.BMS_tracks[trackNum]["offset"]
        
        try:
            self.BMSTrack.parseTrack(trackNum = trackNum,
                                     trackOffset = offset,
                                     noteOn_callback = self.event_playNote,
                                     noteOff_callback = self.event_turnOffNote)
        except EndOfTrack:
            pass
    
    def event_playNote(self, bms_object, trackNum, trackOffset, 
                       commandPos, endPosition, bmsfile, 
                       note, polyphonicID, volume):
        
        pass
    
    def event_turnOffNote(self, bms_object, trackNum, trackOffset, 
                          commandPos, endPosition, bmsfile, 
                          polyphonicID):
        
        
        pass
    
    def changeInstrument(self, bms_object, trackNum, trackOffset, 
                          commandPos, endPosition, bmsfile, 
                          polyphonicID):
        pass
        
    
    def event_getTracks(self, bms_object, trackNum, trackOffset, 
                  commandPos, endPosition, bmsfile, 
                  newTrackNum, newTrackOffset):
        
        self.BMS_tracks[newTrackNum] = {"offset" : newTrackOffset,
                                        "length" : None}
    
    def event_getTrackLength(self, bms_object, trackNum, trackOffset, 
                                  commandPos, endPos, bmsfile):
        
        trackLength = commandPos-trackOffset
        
        self.BMS_tracks[trackNum]["length"] = trackLength
        #self.track_metadata.append((trackNum, trackOffset, trackLength))"""
    
if __name__ == "__main__":
    pygame.midi.init()
    midiOutput = pygame.midi.Output(0)
    
    with open("pikmin_bms/ff_treasureget.bms", "rb") as f:
        myBMS = BMS(f, midiOutput)
        
        myBMS.bmsEngine_run()