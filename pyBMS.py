import time
import StringIO
import os
from struct import error as struct_error

import logging


import pygame


#from midiutil.MidiFile import MIDIFile
#from midi.MidiOutFile import MidiOutFile
from EventParsers import Pikmin2_parser, WindWaker_parser

from BMSparser import BMS_Track, EndOfTrack
from DataReader import DataReader

from pygameMidi_extended import Output as MIDIOutput

from helperFunctions import scaleDown_number


log = logging.getLogger("BMS")

class notePlay(object):
    def __init__(self, midiOutput):
        self.midiOutput = midiOutput
        
        self.playNotes = []
        self.turnOffNotes = []
        
    def addNote(self, note, volume, channel):
        self.playNotes.append((note, volume, channel))
    
    def turnOffNote(self, note, volume, channel):
        self.turnOffNotes.append((note, volume, channel))
    
    def executeActions(self):
        for note in self.playNotes:
            self.midiOutput.note_on(*note)
        
        for note in self.turnOffNotes:
            self.midiOutput.note_off(*note)
        
        self.playNotes = []
        self.turnOffNotes = []
"""class MyMidi(object):
    def __init__(self, trackNum = 1):
        self.MIDI = MIDIFile(trackNum)
        
    def addTrack(self, trackNum, name, startTime = 0, BPM = 120):
        self.MIDI.addTrackName(trackNum, startTime, "Sample Track")
        self.MIDI.addTempo(trackNum, startTime, BPM)
        
    def addNote(self, *args, **kwargs):
        self.MIDI.addNote(*args, **kwargs)
    
    def programChange(self, track, channel, time, program):
        self.MIDI.addProgramChange(track, channel, time, program)
    
    def writeToFile(self, fileobj):
        self.MIDI.writeFile(fileobj)"""

class Subroutine(object):
    def __init__(self, 
                 bmsHandle, trackID, uniqueTrackID,
                 offset, eventParser):
        
        self.bmsHandle = bmsHandle
        
        self.trackID = trackID
        self.uniqueTrackID = uniqueTrackID
        
        self.offset = offset
        self.read = DataReader(bmsHandle)
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
    
    
    """# A helper function that reads and handles the next 
    # event. It is less flexible than parsing and handling
    # the events separately because you can't simply iterate 
    # over all events in the file.
    def handle_next_event(self):
        commandID, args = self.parse_next_event()
        
        self.handle_command(commandID, args)
    
    
    def handle_command(self, commandID, args):
        pass"""
    def parse_next_command(self, strict = True):
        return self.__parser__(self.read, self.bmsHandle)
        
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
    
    # This function is very long because it
    # contains the code to parse (almost) all the events
    # that can be encountered in a Pikmin 2 BMS file.    
    
    
    
    
class BMS(object):
    # BPM is beats per minute, PPQN is pulses per quarter note,
    # as according to MIDI specs.
    def __init__(self, fileobj, midiOutput, BPM = 120, PPQN = 96,
                 parser = Pikmin2_parser):
        self.bmsFile = fileobj
        
        # We will read the entire file into memory
        # so that we can create several file-like objects
        # with different file positions.
        self.bmsData = self.bmsFile.read()
        
        self.midiOutput = midiOutput
        
        #self.BMSTrack = BMS_Track(fileobj, midiOutput)
        
        self.BMS_tracks = []
        
        self.enabledNotes = {}
        
        # Microseconds per minute
        MSPM = 60000000.0
        # Microseconds per quarter note
        MPQN = MSPM / BPM
        
        self.tempo = BPM
        self.waitTime = (MPQN/1000000)/PPQN
        
        self.__eventParser__ = parser.parse_next_command#getattr(EventParsers, "Pikmin2"+"_parser").parse_next_command
        
        # The main subroutine does not have a specified
        # track ID in the BMS file, so we initiate the
        # subroutine with None as it's track ID.
        self.addSubroutine(trackID = None, offset = 0)
        
        self.stoppedTracks = {}
        
        #self.collectTrackInfo()
    
    #def setParser(self, parser):
    #    self.__eventParser__ = parser.parse_next_command
    
    def addSubroutine(self, trackID, offset):
        print "Added track",trackID
        # Create a buffer instance so that we can avoid
        # copying the same data several times.
        bmsHandle = StringIO.StringIO(buffer(self.bmsData))
        
        uniqueTrackID = len(self.BMS_tracks)
        subroutine = Subroutine(bmsHandle, trackID, uniqueTrackID,
                                offset, eventParser = self.__eventParser__)
        
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
        
        note_player = notePlay(self.midiOutput)
        
        while not trackStopped:
            subroutines_to_be_added = []
            
            for subroutine in self.BMS_tracks:
                current_trackID = subroutine.trackID
                current_uniqueTrackID = subroutine.uniqueTrackID
                try:
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
                        curr = subroutine.read.hdlr.tell()
                        command, args = subroutine.parse_next_command()
                        
                        print hex(command), hex(curr)
                    
                    #print hex(command)
                    
                    # Note-on event
                    if command <= 0x7F:
                        note, polyphonicID, volume = args
                        
                        
                        if enabledNotes[polyphonicID] == None:
                            enabledNotes[polyphonicID] = note
                            #self.midiOutput.note_on(note, volume, current_uniqueTrackID)
                            note_player.addNote(note, volume, current_trackID)
                    # Note-off event
                    elif command >= 0x81 and command <= 0x87:
                        polyphonicID = args[0]
                        if enabledNotes[polyphonicID] != None:
                            note = enabledNotes[polyphonicID]
                            enabledNotes[polyphonicID] = None
                            #self.midiOutput.note_on(note, volume, polyphonicID)
                            #self.midiOutput.note_off(note, None, current_uniqueTrackID)   
                            note_player.turnOffNote(note, None, current_trackID)                   
                    
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
                    
                    # Pan change. On a stereo speaker, it defines how much of the
                    # track should be played on the right speaker vs. on the left speaker.
                    # 0 plays the music fully on the left speaker, 127 plays the music 
                    # completely on the right speaker.
                    elif command == 0x9A:
                        unknown1, pan, unknown2 = args
                        self.midiOutput.set_pan(pan, current_trackID)
                    
                    # volume change
                    elif command == 0x9C:
                        unknown1, volume = args
                        
                        # Pygame does not support writing midi events with more than two bytes
                        # of data. One byte is occupied by the event ID for the volume change,
                        # leaving us only one byte to play with. Therefore we need to scale the 
                        # volume value from 16 bits down to 7 bits.
                        fixed_volume = scaleDown_number(volume, 16, 7)
                        
                        self.midiOutput.set_volume(fixed_volume, current_trackID)
                    
                    elif command == 0x9E:
                        unknown1, pitch, unknown2 = args
                        
                        # The BMS pitch value is 16 bits, but the MIDI pitch value
                        # is only 14 bits, so we need to scale down the 16 bits to
                        # 14 bits. This results in some loss of quality.
                        fixed_pitch = scaleDown_number(pitch, 16, 14)
                        #pitch_factor = pitch / (2.0**16-1)
                        #fixed_pitch = int((2**14-1) * pitch_factor)
                        #print "Fixed pitch from {0} to {1}".format(pitch, fixed_pitch)
                        #self.midiOutput.set_pitch(fixed_pitch, current_trackID)
                    
                    # Instrument Bank select or Program change
                    elif command == 0xA4:
                        modus = args[0]
                        
                        if modus == 32:
                            # Instrument bank
                            instrumentBank = args[1]
                            print "Changing instrument bank to",instrumentBank
                            
                            #self.midiOutput.set_instrument_bank(instrumentBank, current_trackID)
                            pass
                        elif modus == 33:
                            # Program change
                            program = args[1]
                            print "Changing program bank to",program&127
                            #self.midiOutput.set_instrument(program & 127, current_trackID)
                            self.midiOutput.set_instrument(program & 127, current_trackID)
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
                        mode, offset = args
                        
                        
                        
                        subroutine.goToOffset(offset)
                        
                    
                    elif command == 0xC1:
                        trackID, offset = args
                        print trackID, offset
                        
                        subroutines_to_be_added.append((trackID, offset))
                    
                    elif command == 0xFF:
                        self.stoppedTracks[current_uniqueTrackID] = True
                        print "Reached end of track", current_uniqueTrackID, "TrackID: ",current_trackID
                        #raise RuntimeError("End of Track")
                        return True
                except struct_error:
                    print "Error in subroutine {0} at offset {1}".format(subroutine.uniqueTrackID,
                                                                         subroutine.read.hdlr.tell())
                    raise
                    
            
            for trackID, offset in subroutines_to_be_added:
                self.addSubroutine(trackID, offset)
            
            note_player.executeActions()
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
    pygame.midi.init()
    midiOutput = MIDIOutput(0)#pygame.midi.Output(0)
    #midiOutput = MidiOutFile("test.midi")
    
    # Change this variable if you want to play a different file.
    PATH = "pikmin2_bms/ff_keyget.bms"
    #PATH = "zelda_bms/pirate_5.bms"
    
    PARSER = Pikmin2_parser
    #PARSER = WindWaker_parser
    
    with open(PATH, "rb") as f:
        # At the moment, there is no code to detect how fast the music
        # piece should be played, so you have to put in the values yourself
        # and see what sounds best.
        # Increasing either BPM (beats per minute) or PPQN (pulses per quarter note)
        # or both increases the tempo at which the music piece is being played.
        #
        # As of now, the values have no other significance besides defining the wait time
        # between each "tick" (On a single "tick", one command 
        # from each subroutine is being read).
        myBMS = BMS(f, midiOutput, BPM = 96, PPQN = 100, parser = PARSER)
        #myBMS.setParser(PARSER)
        myBMS.bmsEngine_run()
    
    midiOutput.close()
    pygame.midi.quit()
    