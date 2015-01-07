
from MidiWriter.midi import MIDI


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

class BMStoMIDIconv(object):
    def __init__(self):
        self.midi = MIDI_sheduler()

