from midi import MIDI


# BMS files, when played back, have lots of tracks playing at once.
# To be able to put that data into a midi sequence, we need to 
# keep track of which events we are playing at which point so
# that we can create a linear midi sequence.
class MidiScheduler(object):
    def __init__(self):
        self.tracks = {}

    def add_track(self, track_id, tick):
        self.tracks[track_id] = {"starts_at": tick, "actions": []}

    def add_action(self, track_id, tick, action):
        self.tracks[track_id]["actions"].append((tick, action))

    def note_on(self, track_id, tick, note, volume):
        self.add_action(track_id, tick, ("note_on", note, volume))

    def note_off(self, track_id, tick, note, volume):
        self.add_action(track_id, tick, ("note_off", note, volume))

    def controller_event(self, track_id, tick, controller, value, use_two_bytes=False):
        self.add_action(track_id, tick, ("controller", controller, value, use_two_bytes))

    def program_change(self, track_id, tick, program):
        self.add_action(track_id, tick, ("program", program))

    def pitch_change(self, track_id, tick, pitch):
        self.add_action(track_id, tick, ("pitch", pitch))

    def change_bpm(self, track_id, tick, bpm):
        self.add_action(track_id, tick, ("bpm", bpm))

    def change_ppqn(self, track_id, tick, ppqn):
        self.add_action(track_id, tick, ("ppqn", ppqn))

    def track_iterator(self):
        for trackID in self.tracks:
            yield trackID

    def get_track_start(self, track_id):
        return self.tracks[track_id]["starts_at"]

    def actions_iter(self, track_id):
        for action in self.tracks[track_id]["actions"]:
            yield action

    def compile_midi(self, instrument_bank, bpm):
        track_count = len(self.tracks)
        midi_data = MIDI(track_count, bpm)

        last_bpm = bpm

        instruments = []
        bpm_values = []
        ppqn_values = []

        for track_id in self.track_iterator():
            #midiFileOutput.start_of_track(n_track = trackID)
            #midiFileOutput.tempo(tempo)
            start = self.get_track_start(track_id)

            #myMidi.addTrackName(trackID, start, "Subroutine")
            #myMidi.addTempo(trackID, start, BPM)
            midi_data.start_track()

            # Change the instrument bank for each track in case the default
            # instrument bank sounds odd.

            midi_data.program_event(0, channel=track_id,
                                    program=0x00, value=instrument_bank)
            #myMidi.set_tempo(0, baseTempo)

            #midiFileOutput.update_time(0)
            #midiFileOutput.continuous_controller(channel = trackID,
            #                                     controller = 0x00,
            #                                     value = INSTRUMENT_BANK)


            #midiFileOutput.update_time(start)

            last_time = start
            for action in self.actions_iter(track_id):
                timestamp, data = action

                ticks_passed = timestamp - last_time
                last_time = timestamp

                #midiFileOutput.update_time(ticks_passed)

                command, args = data[0], data[1:]

                if command == "note_on":
                    note, volume = args
                    midi_data.note_on(ticks_passed, channel=track_id, note=note, velocity=volume)

                elif command == "note_off":
                    note, volume = args
                    midi_data.note_off(ticks_passed, channel=track_id, note=note, velocity=volume)

                elif command == "controller":
                    controller, value, use_two_bytes = args
                    midi_data.program_event(ticks_passed, channel=track_id,
                                            program=controller, value=value, twoBytes=use_two_bytes)

                elif command == "program":
                    program_instrument = args[0]
                    instruments.append(program_instrument)
                    #midiFileOutput.patch_change(channel = trackID,
                    #                            patch = program)
                    #myMidi.set_instrument(ticks_passed, channel = 0, instrument = program_instrument)
                    midi_data.set_instrument(ticks_passed, channel=track_id, instrument=program_instrument)

                elif command == "pitch":
                    pitch = args[0]
                    #midiFileOutput.pitch_bend(channel = trackID,
                    #                          value = pitch)

                    midi_data.set_pitch(ticks_passed, channel=track_id, pitch=pitch)

                elif command == "bpm":
                    bpm = args[0]
                    bpm_values.append(bpm)

                    tempo = int(60000000/bpm)

                    last_bpm = bpm

                    midi_data.set_tempo(ticks_passed, tempo)

                elif command == "ppqn":
                    ppqn = args[0]
                    tempo = 60000000 / (last_bpm * ppqn)
                    ppqn_values.append(ppqn)
                    midi_data.set_tempo(ticks_passed, tempo)

            midi_data.end_track()

        return midi_data



