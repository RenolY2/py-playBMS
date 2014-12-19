from StringIO import StringIO

from DataReader import DataReader

from EventParsers import Parsers
from EventParsers.ParserCreator import VersionSpecificParser

PARSERS = {"pikmin1" : Parsers.Pik1_parser,
           "pikmin2" : Parsers.Pik2_parser,
           "zeldawindwaker" : Parsers.Zelda_WW_parser,
           "supermariosunshine" : Parsers.SMSunshine_parser} 

class BmsSubroutines(object):
    def __init__(self, bmsfile, parser):
        self.__subroutines__ = []
        self.__bmsfile__ = bmsfile
        self.__parser__ = parser
    
    def addSubroutine(self, trackID, offset):
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
        
        
        subroutine = Subroutine(self.__bmsfile__, readObj,
                                trackID, uniqueID,
                                offset, self.__parser__)
        
        self.__subroutines__.append(subroutine)
        
        
    def __iter__(self):
        for subroutine in self.__subroutines__:
            if subroutine.checkIfPaused == False:
                yield subroutine


class BmsInterpreter(object):
    def __init__(self, fileobj, parserName = "pikmin2", customParser = None, 
                 baseBPM = 100, basePPQN = 100, *args, **kwargs):
        
        self._bmsfile = fileobj
        self._setOptions(args, kwargs)
        
        if parserName not in PARSERS:
            raise RuntimeError(
                               "Parser '{parserName}' doesn't exist! Parser must be one of the following:"
                               "{parserList}".format(parserName = parserName, parserList = ", ".join(PARSERS.keys()) )
                               )
            
        elif customParser != None:
            if not isinstance(customParser, VersionSpecificParser):
                raise RuntimeError("Custom Parser needs to be an instance of VersionSpecificParser, not %s" % type(customParser))
            else:
                self._parser = customParser
        else:
            self._parser = PARSERS[parserName]
        
        self._subroutines = BmsSubroutines(self._bmsfile, self._parser)
    
    def _setOptions(self, *args, **kwargs):
        pass
    
    def parseFile(self):
        pass
    
    def advanceTick(self):
        pass