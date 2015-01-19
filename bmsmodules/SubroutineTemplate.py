
from Events import Events


class SubroutineTemplate(object):
    def __init__(self,
                 readData,
                 trackID, uniqueTrackID, parentID,
                 offset, bmsParser,
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



class SubroutineEventsTemplate(object):
    def __init__(self, subroutine):
        self.subroutine = subroutine

        self.BMSevents = Events()


    def handleNextCommand(self, midiSheduler, tick, ignoreUnknownCMDs = False, strict = True):
        prevOffset = self.subroutine.filehandle.tell()
        cmdData = self.subroutine._parse_next_command(strict)
        currOffset = self.subroutine.filehandle.tell()

        cmdID, args = cmdData


        if cmdID in self.BMSevents._events_:
            # tick refers to the tick at which the main loop signaled the subroutine
            # to parse and handle the next command.
            # Every tick, all subroutines can either parse and handle one command, or sleep.
            self.BMSevents.execEvent(cmdID, prevOffset, currOffset, tick)

        elif not ignoreUnknownCMDs:
            raise RuntimeError("Cannot handle Command ID {0} with args {1}"
                               "".format(cmdID, args))

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

        self.subroutine.set_polyphID(cmdID, polyID)
        midiSheduler.note_on(self.subroutine.current_trackIDs,
                             tick,
                             cmdID, volume)


    def event_handleNote_off(self, prevOffset, currOffset, tick,
                            midiSheduler, cmdID, args, strict):
        pass # We cannot do anything if we don't know what that piece of data does


    def event_handleUnknown(self, prevOffset, currOffset, tick,
                            midiSheduler, cmdID, args, strict):
        pass # We cannot do anything if we don't know what that piece of data does




