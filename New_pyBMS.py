from StringIO import StringIO

from OptionsCollector import OptionsCollector
from EventParsers import Parsers
from EventParsers.ParserCreator import VersionSpecificParser
from bmsmodules import DataReader
from bmsmodules.SubroutineTemplate import SubroutineTemplate as Subroutine
from bmsmodules.MidiWriter.MidiSheduler import MIDI_sheduler

# Estimated BMS versions for each of the game.
# They are not representatives of the actual version of the BMS format used,
# they only serve as a way to discern the BMS commands used in the files found
# in each game.
PARSERS = {"pikmin1" : 0.5,#Parsers.Pik1_parser,
           "pikmin2" : 2,#Parsers.Pik2_parser,
           "zeldawindwaker" : 1.5,#Parsers.Zelda_WW_parser,
           "supermariosunshine" : 1}#Parsers.SMSunshine_parser}

class BmsSubroutines(object):
    def __init__(self, bmsfile, parser, options):
        self.__subroutines__ = []
        self.__bmsfile__ = bmsfile
        self.__parser__ = parser
        self._options = options

    
    def addSubroutine(self, parentID, trackID, offset):
        # Every subroutine parses the file independently. Therefore we
        # need to create a different file handle for each subroutine. To avoid
        # copying the data for every subroutine, we will create a "buffer" of the 
        # existing file handle.
        _bmsHandle = StringIO(buffer(self.__bmsfile__))
        
        readObj = DataReader(_bmsHandle)
        
        # Our unique ID will simply consist of the current amount of subroutines.
        # We need an unique ID for every subroutine because the track IDs in BMS files start at 0,
        # but the main subroutine that spawns the subroutine needs a track ID for itself so that
        # the midi conversion works.
        uniqueID = len(self.__subroutines__)

        subroutine = Subroutine(readObj,
                                trackID, uniqueID, parentID,
                                offset, self.__parser__,
                                self._options)

        self.__subroutines__.append(subroutine)

    # Use this method to retrieve the UID of the last subroutine that has been added.
    # For obvious reasons, do not use this when the list of subroutines is empty,
    # as that results in a negative UID.
    def getPreviousUID(self):
        return len(self.__subroutines__)-1
        
    def __iter__(self):
        for subroutine in self.__subroutines__:
            yield subroutine

        raise StopIteration()


class BmsInterpreter(object):
    def __init__(self, fileobj, parserName = "pikmin2", customParser = None,
                 *args, **kwargs):

        self.options = OptionsCollector(baseBPM=100, basePPQN=100)
        self._setOptions(args, kwargs)

        self._bmsfile = fileobj

        
        if parserName not in PARSERS:
            raise RuntimeError(
                               "Parser '{parserName}' doesn't exist! Parser must be one of the following:"
                               "{parserList}".format(parserName=parserName, parserList=", ".join(PARSERS.keys()) )
                               )



        elif customParser != None:
            if not isinstance(customParser, VersionSpecificParser):
                raise RuntimeError("Custom Parser needs to be an instance of VersionSpecificParser, not %s" % type(customParser))
            else:
                self._parser = customParser
        else:
            self._parser = Parsers.container.get_parser(PARSERS[parserName])

        self.sheduler = MIDI_sheduler()
        self._subroutines = BmsSubroutines(self._bmsfile, self._parser,
                                           self.options)

        self._ticks = 0



    def _setOptions(self, *args, **kwargs):
        self.options.set_options(**kwargs)
    
    def parseFile(self):
        # We add a main subroutine that starts doing the work.
        # As such, we set its parent id and track id both to None,
        # because it neither has a parent nor a BMS track id.
        self._subroutines.addSubroutine(None, None, 0)
        ID = self._subroutines.getPreviousUID()
        self.sheduler.addTrack(ID, self._ticks)


        while True:
            # TODO: Add new subroutines when they are encountered.
            self._advanceTick()

        return self.sheduler.compile_midi(INSTRUMENT_BANK=0, BPM=100)



    def _advanceTick(self):
        for sub in self._subroutines:
            cmd = sub.handleNextCommand(self.sheduler, self._ticks)
            if cmd == None:
                pass #pause
            else:
                print cmd

        self._ticks += 1


if __name__ == "__main__":
    import os
    import struct
    #bmsfile = os.path.join("pikmin2_bms","n_tutorial_1stday.bms")
    bmsfile = os.path.join("pikmin2_bms","new_00.bms")

    with open(bmsfile, "rb") as f:
        #bms_data = StringIO(f.read())

        BMSparse = BmsInterpreter(f.read(), parserName = "pikmin2")#bms_data)

    try:
        BMSparse.parseFile()
    except struct.error as e:
        print e
        print "reached end of file, most likely"


    midi = BMSparse.sheduler.compile_midi(0, 100)
    with open("output.midi", "wb") as f:
        midi.write_midi(f)