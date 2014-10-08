import pygame
import time
from struct import error as struct_error

#from midi.MidiOutFile import MidiOutFile
from pyBMS import BMS
from MidiWriter.midi import MIDI#midi

from EventParsers import (Pikmin2_parser, WindWaker_parser, 
                          SMarioSunshine_parser, Pikmin1_parser)

from helperFunctions import scaleDown_number


# BMS files, when played back, have lots of tracks playing at once.
# To be able to put that data into a midi sequence, we need to 
# keep track of which events we are playing at which point so
# that we can create a linear midi sequence.
class MIDI_sheduler(object):
    def __init__(self):
        self.tracks = {}
        
    def addTrack(self, trackID, tick):
        self.tracks[trackID] = {"startsAt" : tick, "actions" : []}
    
    def addAction(self, trackID, tick, action):
        self.tracks[trackID]["actions"].append((tick, action))
        
        
    
    def note_on(self, trackID, tick, note, volume):
        self.addAction(trackID, tick, ("note_on", note, volume))
    
    def note_off(self, trackID, tick, note, volume):
        self.addAction(trackID, tick, ("note_off", note, volume))
    
    def controller_event(self, trackID, tick, controller, value, useTwoBytes = False):
        self.addAction(trackID, tick, ("controller", controller, value, useTwoBytes))
    
    def program_change(self, trackID, tick, program):
        self.addAction(trackID, tick, ("program", program))
        
    def pitch_change(self, trackID, tick, pitch):
        self.addAction(trackID, tick, ("pitch", pitch))
    
    def change_BPM(self, trackID, tick, bpm):
        self.addAction(trackID, tick, ("bpm", bpm))
        
    def change_PPQN(self, trackID, tick, ppqn):
        self.addAction(trackID, tick, ("ppqn", ppqn))
    
    def track_iter(self):
        for trackID in self.tracks:
            yield trackID
                 
    def get_track_start(self, trackID):
        return self.tracks[trackID]["startsAt"]
    
    def actions_iter(self, trackID):
        for action in self.tracks[trackID]["actions"]:
            yield action
    

class BMS2MIDI(BMS):
    
    def bmsEngine_run(self):
        trackStopped = False
        tick = 0
        
        self.midi_sheduler = MIDI_sheduler()
        midi_sheduler = self.midi_sheduler
        
        #note_player = notePlay(self.midiOutput)
        
        while not trackStopped:
            subroutines_to_be_added = []
            #self.midiOutput.update_time(tick, relative = 0)   
            
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
                    countdown = subroutine.checkIfPaused()
                    if countdown == True:
                        continue
                    else:
                        curr = subroutine.read.hdlr.tell()
                        command, args = subroutine.parse_next_command(strict = self.strict)
                        
                        print hex(command), hex(curr)
                    
                    #print hex(command)
                    
                    # Note-on event
                    if command <= 0x7F:
                        note, polyphonicID, volume = args
                        
                        if polyphonicID > 0x7 and self.strict:
                            raise RuntimeError("Invalid Polyphonic ID 0x{x:0} at offset 0x{x:1}"
                                               "".format(polyphonicID, curr))
                        elif polyphonicID > 0x7:
                            # Well, we will skip this invalid note and hope that
                            # everything will go well.
                            continue
                            
                        if enabledNotes[polyphonicID] == None:
                            enabledNotes[polyphonicID] = [note]
                        else:
                            enabledNotes[polyphonicID].append(note)
                            #self.midiOutput.note_on(note, volume, current_uniqueTrackID)
                            #note_player.addNote(note, volume, current_trackID)
                            #self.midiOutput.note_on(channel=current_trackID, note = note, velocity = volume)
                        midi_sheduler.note_on(current_trackID,
                                              tick, 
                                              note, volume)
                            
                    # Note-off event
                    elif command >= 0x81 and command <= 0x87:
                        polyphonicID = args[0]
                        if enabledNotes[polyphonicID] != None:
                            noteList = enabledNotes[polyphonicID]
                           
                            #self.midiOutput.note_on(note, volume, polyphonicID)
                            #self.midiOutput.note_off(note, None, current_uniqueTrackID)   
                            #note_player.turnOffNote(note, None, current_trackID)  
                            #self.midiOutput.note_off(channel=current_trackID, note = note, velocity = volume)   
                            for note in noteList:
                                midi_sheduler.note_off(current_trackID,
                                                      tick, 
                                                      note, volume=0)   
                               
                            enabledNotes[polyphonicID] = None        
                    
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
                        #self.midiOutput.set_pan(pan, current_trackID)
                        #self.midiOutput.continuous_controller(channel = current_trackID,
                        #                                      controller = 0x0A,
                        #                                      value = pan)
                        midi_sheduler.controller_event(current_trackID,
                                                  tick, 
                                                  0x0A, pan)
                        
                    # volume change
                    elif command == 0x9C:
                        unknown1, volume = args
                        
                        #self.midiOutput.set_volume(volume, current_trackID)
                        #self.midiOutput.continuous_controller(channel = current_trackID,
                        #                                      controller = 0x07,
                        #                                      value = volume)
                        if self.estimatedVersion > 1:
                            volume = scaleDown_number(volume, 16, 14)

                            msb_volume = (volume >>7) & 127
                            lsb_volume = volume & 127
                            
                            midi_sheduler.controller_event(current_trackID,
                                                           tick, 
                                                           7, msb_volume)
                            
                            midi_sheduler.controller_event(current_trackID,
                                                           tick, 
                                                           39, lsb_volume)
                        else:
                            volume = scaleDown_number(volume, 8, 7)
                            midi_sheduler.controller_event(current_trackID,
                                                           tick, 
                                                           7, volume)
                        
                    elif command == 0x9E:
                        unknown1, pitch, unknown2 = args
                        
                        # The BMS pitch value is 16 bits, but the MIDI pitch value
                        # is only 14 bits, so we need to scale down the 16 bits to
                        # 14 bits. This results in some loss of quality.
                        fixed_pitch = scaleDown_number(pitch, 16, 14)
                        print "Fixed pitch from {0} to {1}".format(pitch, fixed_pitch)
                        #self.midiOutput.set_pitch(fixed_pitch, current_trackID)
                        #self.midiOutput.pitch_bend(channel = current_trackID,
                        #                           value = fixed_pitch)
                        
                        midi_sheduler.pitch_change(current_trackID,
                                                   tick, 
                                                   fixed_pitch)
                    
                    # Instrument Bank select or Program change
                    elif command == 0xA4:
                        modus = args[0]
                        
                        if modus == 32:
                            # Instrument bank
                            instrumentBank = args[1]
                            print "Changing instrument bank to",instrumentBank
                            
                            midi_sheduler.controller_event(current_trackID,
                                                           tick, 
                                                           0x00, instrumentBank)
                        elif modus == 33:
                            # Program change
                            program = args[1]
                            print "Changing program bank to",program
                            #self.midiOutput.set_instrument(instrumentBank, current_trackID)
                            #self.midiOutput.patch_change(channel = current_trackID,
                            #                             patch = instrumentBank)
                            midi_sheduler.program_change(current_trackID,
                                                         tick, 
                                                         program & 127)
                    
                    # Store current position, go to a specific offset
                    elif command == 0xC4:
                        goto_offset = args[0]
                        print "Offset", goto_offset
                        if self.noJumping: continue
                        
                        subroutine.setPreviousOffset()
                        subroutine.goToOffset(goto_offset)
                        # We set the file position of the subroutine
                        # to this new offset.
                        #subroutine.read.hdlr.seek(goto_offset)
                    
                    # On a 0xC6 event, we have to return to the position previously stored
                    # by a 0xC4 event. 
                    elif command == 0xC6:
                        if not self.noJumping:
                            subroutine.goToPreviousOffset()
                    
                    # A simple event for jumping to a specific position in the file.
                    elif command == 0xC8:
                        mode, offset = args
                        if self.noJumping: continue
                        
                        if mode == 0:
                            subroutine.goToOffset(offset)
                        #elif mode == 1:
                        #    # Probably "relative offset"
                        #    new_offset = subroutine.read.hdlr.tell() + offset
                        #    subroutine.goToOffset(new_offset)
                        else:
                            # Unknown modes
                            pass
                        
                    
                    elif command == 0xC1:
                        trackID, offset = args
                        print trackID, offset
                        
                        if self.singleTrackMode == False:
                            midi_sheduler.addTrack(trackID, tick)
                            subroutines_to_be_added.append((trackID, offset))
                    
                    elif command == 0xFD:
                        bpmValue = args[0]
                        
                        midi_sheduler.change_BPM(trackID, tick, bpmValue)
                    
                    elif command == 0xFE:
                        ppqnValue = args[0]
                        
                        midi_sheduler.change_PPQN(trackID, tick, ppqnValue)
                    
                    elif command == 0xFF:
                        if self.singleTrackMode == False:
                            self.stoppedTracks[current_uniqueTrackID] = True
                            print "Reached end of track", current_uniqueTrackID
                            #raise RuntimeError("End of Track")
                            return True
                        
                            if self.onlyEndWhenAllTracksEnd:
                                if len(self.stoppedTracks) == len(self.BMS_tracks):
                                    return True
                            elif self.onlyMainTrackEndsMusic:
                                if current_trackID == None:
                                    #pass
                                    return True
                                
                except struct_error:
                    print "Error in subroutine {0} at offset {1}".format(subroutine.uniqueTrackID,
                                                                         subroutine.read.hdlr.tell())
                    raise
                
                #self.midiOutput.update_time(0)   
            
            for trackID, offset in subroutines_to_be_added:
                self.addSubroutine(trackID, offset)
            
            
            
            
            #note_player.executeActions()
            #time.sleep(self.waitTime)
            tick += 1    
             

if __name__ == "__main__":
    #pygame.midi.init()
    #midiOutput = MIDIOutput(0)#pygame.midi.Output(0)
    #midiOutput = MidiOutFile("test.midi")
    

    BaseBPM = 100
    lastBPM = BaseBPM
    
    BPM = BaseBPM
    __tick_modifier__ = BPM / 100
    #PPQN = 100.0
    tempo = int(60000000.0 / BPM)
    baseTempo = tempo
    
    # Microseconds per minute
    #MSPM = 60000000.0
    # Microseconds per quarter note
    #MPQN = MSPM / BPM
    
    #self.tempo = BPM
    #waitTime = int((MPQN/1000000.0)/PPQN)
    #waitTime = int(MPQN/PPQN)
    #waitTime = int(MPQN)*10000
    
    #PARSER = Pikmin2_parser
    #PARSER = WindWaker_parser
    #PARSER = SMarioSunshine_parser
    PARSER = Pikmin1_parser
    
    bpm_values = []
    ppqn_values = []
    instruments = []
    
    # Change this variable if you want to play a different file.
    #PATH = "pikmin2_bms/worldmap.bms"
    PATH = "mario_bms/pikmin_bms/demobgm.jam.bms"
    # Change this path if you want to save the results to a different file
    MIDI_PATH = "test2.midi"
    
    # Does the music sound odd? Try changing the instrument bank.
    INSTRUMENT_BANK = 0

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
        
        #myBMS = BMS2MIDI(f, None, BPM = 90, PPQN = 100, parser = PARSER)
        myBMS = BMS2MIDI(f, None, BPM = 96, PPQN = 100, parser = PARSER, strict = True,
                   singleTrackMode = False, noJumping = False, forceStartAt = 18411,#25283,
                   onlyMainTrackEndsMusic = True, onlyEndWhenAllTracksEnd = True)
        
        try:
            myBMS.bmsEngine_run()
        except KeyboardInterrupt:
            print "We are stopping playback now!"
            pass
    sheduler = myBMS.midi_sheduler
    print sheduler
    
    #midiFileOutput = MidiOutFile(MIDI_PATH)
    
    
    trackNum = len(sheduler.tracks)
    myMidi = MIDI(trackNum, BPM)#midiutil.MidiFile(trackNum)
    
    #midiFileOutput.header(midiformat = 1,
    #                      nTracks = trackNum)
    
    
    
    for trackID in sheduler.track_iter():
        
        #midiFileOutput.start_of_track(n_track = trackID) 
        #midiFileOutput.tempo(tempo)
        start = sheduler.get_track_start(trackID)
        
        #myMidi.addTrackName(trackID, start, "Subroutine")
        #myMidi.addTempo(trackID, start, BPM)
        myMidi.startTrack()
        
        # Change the instrument bank for each track in case the default
        # instrument bank sounds odd.
        
        myMidi.program_event(0, channel = trackID, 
                             program = 0x00, value = INSTRUMENT_BANK)
        #myMidi.set_tempo(0, baseTempo)
        
        #midiFileOutput.update_time(0)
        #midiFileOutput.continuous_controller(channel = trackID,
        #                                     controller = 0x00,
        #                                     value = INSTRUMENT_BANK)
        
        
        #midiFileOutput.update_time(start)
        
        lastTime = start
        
        notes_enabled = {}
        
        for action in sheduler.actions_iter(trackID):
            timestamp, data = action
            
            ticks_passed = timestamp - lastTime
            lastTime = timestamp
            
            #midiFileOutput.update_time(ticks_passed)
            
            command, args = data[0], data[1:]
            
            if command == "note_on":
                note, volume = args
                myMidi.note_on(ticks_passed, channel = trackID, note = note, velocity = volume)
                
            elif command == "note_off":
                note, volume = args
                myMidi.note_off(ticks_passed, channel = trackID, note = note, velocity = volume)

            elif command == "controller":
                controller, value, useTwoBytes = args
                myMidi.program_event(ticks_passed, channel = trackID, 
                                     program = controller, value = value, twoBytes = useTwoBytes)

            elif command == "program":
                program_instrument = args[0]
                instruments.append(program_instrument)
                #midiFileOutput.patch_change(channel = trackID,
                #                            patch = program)
                #myMidi.set_instrument(ticks_passed, channel = 0, instrument = program_instrument)
                myMidi.set_instrument(ticks_passed, channel = trackID, instrument = program_instrument)
                
            elif command == "pitch":
                pitch = args[0]
                #midiFileOutput.pitch_bend(channel = trackID,
                #                          value = pitch)
                
                myMidi.set_pitch(ticks_passed, channel = trackID, pitch = pitch)
            
            elif command == "bpm":
                bpm = args[0]
                bpm_values.append(bpm)
                
                tempo = int(60000000/bpm)
                
                lastBPM = bpm
                
                myMidi.set_tempo(ticks_passed, tempo)
            
            elif command == "ppqn":
                ppqn = args[0]
                tempo = 60000000 / (lastBPM * ppqn) 
                ppqn_values.append(ppqn)
                myMidi.set_tempo(ticks_passed, tempo)
                
                #__tick_modifier__ = BPM/float(bpm)
                
            
        
        
        #midiFileOutput.update_time(0)
        #midiFileOutput.end_of_track()
        myMidi.end_track()
    
    with open(MIDI_PATH, "wb") as f:
        myMidi.write_midi(f)
    #pygame.midi.quit()
    print "done!"
    print "Tempo: ", tempo
    print "BPM values:",bpm_values
    print "PPQN values:",ppqn_values
    print "Instruments:",instruments
    time.sleep(2)