
from Events import Events


class SubroutineTemplate(object):
    def __init__(self,
                 readData,
                 trackID, uniqueTrackID, parentID,
                 offset, bmsParser,
                 options,
                 customSubroutineHandler = None):

        # readData is an instance of DataReader, found in DataReader.py
        # With it, data reading can be abstracted a little bit so that
        # instead of dealing with reading a specific amount of bytes and then
        # interpreting it, you can just use a method, e.g. byte(), to read that
        # data and parse it accordingly.
        self.readData = readData

        # filehandle represents the file handle used by the current readData instance.
        # Each subroutine has its own readData instance, and every filehandle points to a
        # different spot in the file data of a BMS file
        self.filehandle = readData.hdlr

        # The track ID is a number, normally between 0 and 15, as specified by the BMS file
        # in 0xC1 events.
        self.trackID = trackID

        # The parent ID is the ID of the subroutine that spawned the current subroutine.
        self.parentID = parentID

        # The uuTrackID is an unique track id specific to the current subroutine.
        # It is only useful for the later midi conversion due to subroutines sometimes having conflicting IDs
        self.uuTrackID = uniqueTrackID

        # This is the offset in the file at which the subroutine data starts.
        self.startOffset = offset

        # bmsParser is an instance of VersionSpecificParser found in ParserCreator.py
        # It contains the functions for parsing data from the BMS "version" it has been
        # initiated with.
        self.bmsParser = bmsParser

        # We need to keep track of which notes we have
        # assigned to which IDs so that we can turn off all notes
        # with a specific polyhponic ID when we encounter a note off event.
        self._enabled_PolyphIDs = {}

        # Once started, a subroutine should be running until it
        # encounters an end of track command.
        self.stopped = False

        self.options = options

        self.pause_ticksLeft = 0


        if customSubroutineHandler == None:
            self.subrHandler = SubroutineEventsTemplate(self)
        else:

            self.subrHandler = customSubroutineHandler(self)


    # Keeping track of enabled polyphonic IDs and their notes
    def add_polyphNote(self, ID, note):
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
        if ID in self._enabled_PolyphIDs:
            del self._enabled_PolyphIDs[ID]

    def setPause(self, length):
        if length < 0: raise RuntimeError("Pause is not supposed to be negative!")
        self.pause_ticksLeft += length


    def handleNextCommand(self, sheduler, tick):
        if self.pause_ticksLeft > 0:
            self.pause_ticksLeft -= 1

            return None
        else:
            cmd = self.subrHandler.handleNextCommand(sheduler, tick, False, True)
            return cmd

    def _parse_next_command(self, strict = True):
        return self.bmsParser.parse_next_cmd(self.filehandle, self.readData, strict)



class SubroutineEventsTemplate(object):
    def __init__(self, subroutine):
        self.subroutine = subroutine

        self.BMSevents = Events()


        self._addEventHandlerRange(0x00, 0x80, self.event_handleNote_on)
        self._addEventHandlerRange(0x81, 0x88, self.event_handleNote_off)

        self._addEventHandler(0x80, self.event_handlePause)
        self._addEventHandler(0x88, self.event_handlePause)

        self._addEventHandler(0xFF, self.event_handleEndOfTrack)

        self._fillUndefinedEvents(0x00, 0xFF, self.event_handleUnknown)

    def handleNextCommand(self, midiSheduler, tick, ignoreUnknownCMDs = False, strict = True):
        prevOffset = self.subroutine.filehandle.tell()
        cmdData = self.subroutine._parse_next_command(strict)
        currOffset = self.subroutine.filehandle.tell()

        cmdID, args = cmdData
        #print cmdData
        if cmdID in self.BMSevents._events_:
            # tick refers to the tick at which the main loop signaled the subroutine
            # to parse and handle the next command.
            # Every tick, all subroutines can either parse and handle one command, or sleep.
            self.BMSevents.execEvent(cmdID, prevOffset, currOffset, tick,
                                     midiSheduler, cmdID, args, strict)

        elif not ignoreUnknownCMDs:
            raise RuntimeError("Cannot handle Command ID {0} with args {1}"
                               "".format(cmdID, args))

        return cmdID

    def _addEventHandler(self, ID, func):
        self.BMSevents.addEvent(ID, func)

    def _addEventHandlerRange(self, start, end, func):
        for i in xrange(start, end):
            self.BMSevents.addEvent(i, func)

    def _fillUndefinedEvents(self, start, end, func):
        for i in xrange(start, end):
            if i not in self.BMSevents._events_:
                self.BMSevents.addEvent(i, func)


    def event_handleNote_on(self, prevOffset, currOffset, tick,
                         midiSheduler, cmdID, args, strict):

        polyID, volume = args


        if polyID > 0x7 and strict:
            raise RuntimeError("Invalid Polyphonic ID 0x{x:0} at offset 0x{x:1}"
                               "".format(polyID, prevOffset))
        elif polyID > 0x7:
            # Well, we will skip this invalid note and hope that
            # everything will go well.
            return

        self.subroutine.add_polyphNote(cmdID, polyID)
        midiSheduler.note_on(self.subroutine.uuTrackID,
                             tick,
                             cmdID, volume)



    def event_handleNote_off(self, prevOffset, currOffset, tick,
                            midiSheduler, cmdID, args, strict):

        polyID = args[0]
        for note in self.subroutine.getNotes_byPolyphID(polyID):
            midiSheduler.note_off(  self.subroutine.uuTrackID,
                                    tick,
                                    note, volume=0)
        self.subroutine.turnOff_polyphID(polyID)


    def event_handleUnknown(self, prevOffset, currOffset, tick,
                            midiSheduler, cmdID, args, strict):
        pass # We cannot do anything if we don't know what that piece of data does

    def event_handleEndOfTrack(self, prevOffset, currOffset, tick,
                               midiSheduler, cmdID, args, strict):
        print "Track end at", currOffset, ",", tick, "Ticks"
        self.stopped = True

    def event_handlePause(self, prevOffset, currOffset, tick,
                          midiSheduler, cmdID, args, strict):
        delay = args[0]
        #print "Track {0} is paused for {1} ticks".format(current_uniqueTrackID,
        #                                                 delay)
        self.subroutine.setPause(delay)

