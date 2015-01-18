
from Events import Events


class SubroutineTemplate(object):
    def __init__(self,
                 readData,
                 trackID, uniqueTrackID,
                 offset, bmsParser,
                 customSubroutineHandler = None):

        self.readData = readData
        self.filehandle = readData.hdlr

        self.trackID = trackID
        self.uuTrackID = uniqueTrackID
        self.startOffset = offset


        self.bmsParser = bmsParser



class SubroutineEventsTemplate(object):
    def __init__(self, subroutine):
        self.subroutine = subroutine

        self.BMSevents = Events()


    def handleNextCommand(self, midiSheduler, ignoreUnknownCMDs = False, strict = True):
        prevOffset = self.subroutine.filehandle.tell()
        cmdData = self.subroutine._parse_next_command(strict)
        currOffset = self.subroutine.filehandle.tell()

        cmdID, args = cmdData



        if cmdID in self.BMSevents._events_:
            self.BMSevents.
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


    def event_handleNote(self, prevOffset, currOffset,
                         midiSheduler, cmdID, args, strict):
        pass

    def event_handleUnknown(self, prevOffset, currOffset,
                            midiSheduler, cmdID, args, strict):
        pass # We cannot do anything if we don't know what the piece of data does




