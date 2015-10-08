
from events import Events


class SubroutineTemplate(object):
    def __init__(self,
                 reader,
                 track_id, unique_track_id, parent_id,
                 offset, bms_parser,
                 options,
                 custom_subroutine_handler=None):

        # reader is an instance of DataReader, found in DataReader.py
        # With it, data reading can be abstracted a little bit so that
        # instead of dealing with reading a specific amount of bytes and then
        # interpreting it, you can just use a method, e.g. byte(), to read that
        # data and parse it accordingly.
        self.reader = reader

        # filehandle represents the file handle used by the current reader instance.
        # Each subroutine has its own reader instance, and every filehandle points to a
        # different spot in the file data of a BMS file
        self.filehandle = reader.filehandle

        # The track ID is a number, normally between 0 and 15, as specified by the BMS file
        # in 0xC1 events.
        self.track_id = track_id

        # The parent ID is the ID of the subroutine that spawned the current subroutine.
        self.parent_id = parent_id

        # The unique_track_id is an unique track id specific to the current subroutine.
        # It is only useful for the later midi conversion due to subroutines sometimes having conflicting IDs
        self.unique_track_id = unique_track_id

        # This is the offset in the file at which the subroutine data starts.
        self.start_offset = offset

        # bmsParser is an instance of VersionSpecificParser found in ParserCreator.py
        # It contains the functions for parsing data from the BMS "version" it has been
        # initiated with.
        self.bms_parser = bms_parser

        # We need to keep track of which notes we have
        # assigned to which IDs so that we can turn off all notes
        # with a specific polyhponic ID when we encounter a note off event.
        self._enabled_poly_ids = {}

        # Once started, a subroutine should be running until it
        # encounters an end of track command.
        self.stopped = False

        self.options = options
        self.pause_ticks_left = 0

        self.subroutine_handler = None
        if custom_subroutine_handler is None:
            self.subroutine_handler = SubroutineEventsTemplate(self)
        else:
            self.subroutine_handler = custom_subroutine_handler(self)

    # Keeping track of enabled polyphonic IDs and their notes
    def add_polyphonic_note(self, id, note):
        if id not in self._enabled_poly_ids:
            self._enabled_poly_ids[id] = [note]
        else:
            self._enabled_poly_ids[id].append(note)

    def get_notes_by_id(self, id):
        if id not in self._enabled_poly_ids:
            return []
        else:
            return self._enabled_poly_ids[id]

    def turn_off_id(self, id):
        if id in self._enabled_poly_ids:
            del self._enabled_poly_ids[id]

    def set_pause(self, length):
        if length < 0:
            raise RuntimeError("Pause is not supposed to be negative!")
        self.pause_ticks_left += length

    def handle_next_command(self, scheduler, tick):
        if self.pause_ticks_left > 0:
            self.pause_ticks_left -= 1

            return None
        else:
            cmd = self.subroutine_handler.handle_next_command(scheduler, tick, False, True)
            return cmd

    def parse_next_command(self, strict = True):
        return self.bms_parser.parse_next_cmd(self.filehandle, self.reader, strict)


class SubroutineEventsTemplate(object):
    def __init__(self, subroutine):
        self.subroutine = subroutine

        self.bms_events = Events()

        self._add_eventhandler_range(0x00, 0x80, self.event_handle_note_on)
        self._add_eventhandler_range(0x81, 0x88, self.event_handle_note_off)

        self._add_eventhandler(0x80, self.event_handle_pause)
        self._add_eventhandler(0x88, self.event_handle_pause)

        self._add_eventhandler(0xFF, self.event_handle_endoftrack)

        self._fill_undefined_events(0x00, 0xFF, self.event_handle_unknown)

    def handle_next_command(self, midi_scheduler, tick, ignore_unknown_cmd=False, strict=True):
        prev_offset = self.subroutine.filehandle.tell()
        cmd_data = self.subroutine.parse_next_command(strict)
        curr_offset = self.subroutine.filehandle.tell()

        cmd_id, args = cmd_data
        #print cmdData
        if cmd_id in self.bms_events:
            # tick refers to the tick at which the main loop signaled the subroutine
            # to parse and handle the next command.
            # Every tick, all subroutines can either parse and handle one command, or sleep.
            self.bms_events.exec_event(cmd_id, prev_offset, curr_offset, tick,
                                       midi_scheduler, cmd_id, args, strict)

        elif not ignore_unknown_cmd:
            raise RuntimeError("Cannot handle Command ID {0} with args {1}"
                               "".format(cmd_id, args))

        return cmd_id

    def _add_eventhandler(self, id, func):
        self.bms_events.add_event(id, func)

    def _add_eventhandler_range(self, start, end, func):
        for i in xrange(start, end):
            self.bms_events.add_event(i, func)

    def _fill_undefined_events(self, start, end, func):
        for i in xrange(start, end):
            if i not in self.bms_events:
                self.bms_events.add_event(i, func)

    def event_handle_note_on(self, prev_offset, curr_offset, tick,
                             midi_scheduler, cmd_id, args, strict):

        poly_id, volume = args

        if poly_id > 0x7 and strict:
            raise RuntimeError("Invalid Polyphonic ID 0x{0:x} at offset 0x{1:x}"
                               "".format(poly_id, prev_offset))
        elif poly_id > 0x7:
            # Well, we will skip this invalid note and hope that
            # everything will go well.
            return

        self.subroutine.add_polyphonic_note(cmd_id, poly_id)
        midi_scheduler.note_on(self.subroutine.unique_track_id,
                               tick,
                               cmd_id, volume)



    def event_handle_note_off(self, prev_offset, curr_offset, tick,
                              midi_scheduler, cmd_id, args, strict):

        poly_id = args[0]
        for note in self.subroutine.get_notes_by_id(poly_id):
            midi_scheduler.note_off(self.subroutine.unique_track_id,
                                    tick,
                                    note, volume=0)
        self.subroutine.turn_off_id(poly_id)


    def event_handle_unknown(self, prev_offset, curr_offset, tick,
                             midi_scheduler, cmd_id, args, strict):
        pass

    def event_handle_endoftrack(self, prev_offset, curr_offset, tick,
                                midi_scheduler, cmd_id, args, strict):
        print "Track end at", curr_offset, ",", tick, "Ticks"
        self.subroutine.stopped = True

    def event_handle_pause(self, prev_offset, curr_offset, tick,
                           midi_scheduler, cmd_id, args, strict):
        delay = args[0]
        # print "Track {0} is paused for {1} ticks".format(current_uniquetrack_id,
        #                                                 delay)
        self.subroutine.set_pause(delay)

