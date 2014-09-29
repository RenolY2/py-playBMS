import time
import StringIO
import os

import logging


import pygame

#from midi.MidiOutFile import MidiOutFile

from BMSparser import BMS_Track, EndOfTrack
from DataReader import DataReader

log = logging.getLogger("BMS")

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
        
        self.previousPosition = None
    
    
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
    
    # The 0xC4 event sets the previous position to
    # the current position in the file. We will
    # return to this position on encountering a 0xC6 event.
    def setPreviousOffset(self):
        self.previousPosition = self.read.hdlr.tell()
    
    # The 0xC6 event makes us go to the previous position.
    # When the previous position was set, it was already after
    # the 0xC4 event was parsed, so we do not have to worry
    # about hitting the event again.
    def goToPreviousOffset(self):
        self.goToOffset(self.previousPosition)
    
    # A helper method so that we don't have to type so much
    # to make the subroutine go to a specific offset.
    def goToOffset(self, offset):
        self.read.hdlr.seek(offset)
    
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
        
        self.enabledNotes = {}
        
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
        
        # Keep track of which notes we play so we
        # can turn them on and off correctly.
        self.enabledNotes[uniqueTrackID] = {}
        
        for i in xrange(8):
            self.enabledNotes[uniqueTrackID][i] = None
        
        
        
    
    # This function does the main work of iterating over the commands
    # from each subroutine and executing them.
    def bmsEngine_run(self):
        trackStopped = False
        tick = 0
        
        while not trackStopped:
            subroutines_to_be_added = []
            
            for subroutine in self.BMS_tracks:
                
                current_trackID = subroutine.trackID
                current_uniqueTrackID = subroutine.uniqueTrackID
                
                #subLog = logging.getLogger("BMS.Sub"+str(current_uniqueTrackID))
                
                enabledNotes = self.enabledNotes[current_uniqueTrackID]
                
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
                
                #print hex(command)
                
                # Note-on event
                if command <= 0x7F:
                    note, polyphonicID, volume = args
                    
                    if enabledNotes[polyphonicID] == None:
                        enabledNotes[polyphonicID] = note
                        self.midiOutput.note_on(note, volume, current_uniqueTrackID)
                # Note-off event
                elif command >= 0x81 and command <= 0x87:
                    polyphonicID = args[0]
                    if enabledNotes[polyphonicID] != None:
                        note = enabledNotes[polyphonicID]
                        enabledNotes[polyphonicID] = None
                        #self.midiOutput.note_on(note, volume, polyphonicID)
                        self.midiOutput.note_off(note, None, current_uniqueTrackID)                      
                
                # Delay events, the subroutine will be paused for a specific
                # amount of ticks
                elif command in (0x80, 0x88):
                    delay = args[0]
                    print "Track {0} is paused for {1} ticks".format(current_uniqueTrackID,
                                                                     delay)
                    subroutine.setPause(delay)
                
                
                    
                # We need to collect examples of variable delay
                # so that we can parse them correctly.
                elif command == 0xF0:
                    delay = args[0]
                    print "####"
                    print delay.encode("hex")
                    
                    with open("VariableDelay.txt", "a") as f:
                        f.write(delay.encode("hex")+"\n")
                    
                # Instrument Bank select or Program change
                elif command == 0xA4:
                    modus = args[0]
                    
                    if modus == 32:
                        # Instrument bank
                        instrumentBank = args[1]
                        print "Changing instrument bank to",instrumentBank
                        
                        self.midiOutput.set_instrument(instrumentBank, current_uniqueTrackID)
                        pass
                    elif modus == 33:
                        # Program change
                        program = args[1]
                        print "Changing program bank to",program
                        pass
                
                # Store current position, go to a specific offset
                elif command == 0xC4:
                    goto_offset = args[0]
                    print "Offset", goto_offset
                    
                    subroutine.setPreviousOffset()
                    subroutine.goToOffset(goto_offset)
                    # We set the file position of the subroutine
                    # to this new offset.
                    #subroutine.read.hdlr.seek(goto_offset)
                
                # On a 0xC6 event, we have to return to the position previously stored
                # by a 0xC4 event. 
                elif command == 0xC6:
                    subroutine.goToPreviousOffset()
                
                # A simple event for jumping to a specific position in the file.
                elif command == 0xC8:
                    offset = args[0]
                    
                    subroutine.goToOffset(offset)
                    
                
                elif command == 0xC1:
                    trackID, offset = args
                    print trackID, offset
                    
                    subroutines_to_be_added.append((trackID, offset))
                
                elif command == 0xFF:
                    self.stoppedTracks[current_uniqueTrackID] = True
                    print "Reached end of track", current_uniqueTrackID
                    raise RuntimeError("End of Track")
                    
            
            for trackID, offset in subroutines_to_be_added:
                self.addSubroutine(trackID, offset)
            
            
            time.sleep(self.waitTime)
            tick += 1        
                
            
            
        
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
    # How to use i
    
    
    pygame.midi.init()
    midiOutput = pygame.midi.Output(0)
    
    #midiOutput = MidiOutFile("test.midi")
    folder = "pikmin_bms"
    #file = "ff_treasureget.bms"
    #file = "2pbattle.bms"
    file = "new_00.bms"
    
    
    with open(os.path.join(folder, file), "rb") as f:
        # At the moment, there is no code to detect how fast the music
        # piece should be played, so you have to put in the values yourself
        # and see what sounds best.
        # Increasing either BPM (beats per minute) or PPQN (pulses per quarter note)
        # or both increases the tempo at which the music piece is being played.
        #
        # As of now, the values have no other significance besides defining the wait time
        # between each "tick" (On a single "tick", one command 
        # from each subroutine is being read).
        myBMS = BMS(f, midiOutput, BPM = 90, PPQN = 96)
        
        myBMS.bmsEngine_run()
    