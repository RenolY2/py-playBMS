from midi import MIDI

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



    def compile_midi(self, INSTRUMENT_BANK, BPM):
        trackCount = len(self.tracks)
        midiData = MIDI(trackCount, BPM)

        instruments = []
        bpm_values = []
        ppqn_values = []

        for trackID in self.track_iter():

            #midiFileOutput.start_of_track(n_track = trackID)
            #midiFileOutput.tempo(tempo)
            start = self.get_track_start(trackID)

            #myMidi.addTrackName(trackID, start, "Subroutine")
            #myMidi.addTempo(trackID, start, BPM)
            midiData.startTrack()

            # Change the instrument bank for each track in case the default
            # instrument bank sounds odd.

            midiData.program_event(0, channel=trackID,
                                    program=0x00, value=INSTRUMENT_BANK)
            #myMidi.set_tempo(0, baseTempo)

            #midiFileOutput.update_time(0)
            #midiFileOutput.continuous_controller(channel = trackID,
            #                                     controller = 0x00,
            #                                     value = INSTRUMENT_BANK)


            #midiFileOutput.update_time(start)

            lastTime = start
            for action in self.actions_iter(trackID):
                timestamp, data = action

                ticks_passed = timestamp - lastTime
                lastTime = timestamp

                #midiFileOutput.update_time(ticks_passed)

                command, args = data[0], data[1:]

                if command == "note_on":
                    note, volume = args
                    midiData.note_on(ticks_passed, channel=trackID, note=note, velocity=volume)

                elif command == "note_off":
                    note, volume = args
                    midiData.note_off(ticks_passed, channel=trackID, note=note, velocity=volume)

                elif command == "controller":
                    controller, value, useTwoBytes = args
                    midiData.program_event(ticks_passed, channel=trackID,
                                           program=controller, value=value, twoBytes=useTwoBytes)

                elif command == "program":
                    program_instrument = args[0]
                    instruments.append(program_instrument)
                    #midiFileOutput.patch_change(channel = trackID,
                    #                            patch = program)
                    #myMidi.set_instrument(ticks_passed, channel = 0, instrument = program_instrument)
                    midiData.set_instrument(ticks_passed, channel=trackID, instrument=program_instrument)

                elif command == "pitch":
                    pitch = args[0]
                    #midiFileOutput.pitch_bend(channel = trackID,
                    #                          value = pitch)

                    midiData.set_pitch(ticks_passed, channel=trackID, pitch=pitch)

                elif command == "bpm":
                    bpm = args[0]
                    bpm_values.append(bpm)

                    tempo = int(60000000/bpm)

                    lastBPM = bpm

                    midiData.set_tempo(ticks_passed, tempo)

                elif command == "ppqn":
                    ppqn = args[0]
                    tempo = 60000000 / (lastBPM * ppqn)
                    ppqn_values.append(ppqn)
                    midiData.set_tempo(ticks_passed, tempo)

            midiData.end_track()

        return midiData



