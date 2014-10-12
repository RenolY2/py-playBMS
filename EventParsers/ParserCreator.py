import struct


class ParserContainer(object):
    def __init__(self):
        self.parsers = {}
        
        self.versions = []
            
    def add_parser(self, parser):
        # The version number has to be either an integer or a float, any other
        # value makes no sense in this context.
        assert isinstance(parser.estimatedVersion, (int, float)) == True
        
        if parser.estimatedVersion in self.parsers:
            existingParserName = self.parsers[parser.estimatedVersion].gameName
            
            raise RuntimeError("Parser version ({version}) of '{newParserName}' "
                               "already in use by parser '{existingParser}'".format(version = parser.estimatedVersion,
                                                                                    newParserName = parser.gameName,
                                                                                    existingParser = existingParserName))
        self.versions.append(parser.estimatedVersion)
        self.parsers[parser.estimatedVersion] = parser
        self.versions.sort()
    
    def get_parser(self, estimatedVersion):
        baseParser = VersionSpecificParser(estimatedVersion,
                                           "Parser v{0}".format(estimatedVersion))
        
        for version in self.versions:
            if version > estimatedVersion: break
            
            parent_parser = self.parsers[version]
            
            # We apply all changes of the previous parsers to the current parser,
            # otherwise the parser will not be complete.
            baseParser.__takeover_parent_parsers__(parent_parser)
        
        return baseParser
    
    

class VersionSpecificParser(object):
    def __init__(self, estimatedVersion, gameName):
        self.command_parsers = {}
        self.estimatedVersion = estimatedVersion
        self.gameName = gameName
        
        self.parents = []
    
    # the BMS format has evolved over time, but there are
    # similarities between versions of the format.
    # To avoid writing lots of duplicate code, we will copy the parser
    # functions from the parent parser (i.e. a parser with a lower estimated version)
    def __takeover_parent_parsers__(self, parentParser):
        parentVersion = parentParser.estimatedVersion
        gameName = parentParser.gameName
        
        self.parents.append((parentVersion, gameName))
        
        for commandID, function in parentParser.command_parsers.iteritems():
            self.command_parsers[commandID] = function
            
    
    def set_parser_function(self, function, commandID):
        self.command_parsers[commandID] = function
    
    # Helper function to add a parser function to a range of command IDs.
    # Please note that the function will be applied to the command IDs from
    # 'start_commandID' to 'end_commandID - 1'.
    # This is useful for adding parsers for the note-on events, of which there are
    # 128. (command ID 0x00 to 0x7F)
    def set_parser_function_range(self, function, start_commandID, end_commandID):
        for commandID in xrange(start_commandID, end_commandID):
            self.command_parsers[commandID] = function
    
    # Helper function to add a parser function to a specific set of command IDs.
    # Some command IDs might have similar data structures, so this can be used
    # to cut down the amount of code wasted on writing duplicate parsers.
    def set_many_parser_functions(self, function, *commandIDs):
        for commandID in commandIDs:
            self.command_parsers[commandID] = function
    


def create_parser_function(struct_datastructure):
    structObj = struct.Struct(struct_datastructure)
    
    def parser_func(bmsfile, read, strict):
        bin_data = bmsfile.read(structObj.size)
        values = structObj.unpack(bin_data)
        
        return values
    
    return parser_func

if __name__ == "__main__":
    container = ParserContainer()
    
    parser1 = VersionSpecificParser(0, "Basic BMS Stuff")
    parser1.set_parser_function(create_parser_function("bBB"), 0x00)
    parser1.set_parser_function_range(create_parser_function("HHHH"), 0x01, 0x80)
    parser1.set_many_parser_functions(create_parser_function(">II"), 0x81, 0x85, 0xFF)
    
    
    parser2 = VersionSpecificParser(1, "Game 1")
    parser2.set_parser_function(create_parser_function("I"), 0x00)
    parser1.set_parser_function_range(create_parser_function("BB"), 0x70, 0x90)
    
    container.add_parser(parser1)
    container.add_parser(parser2)
    
    
    # Each parser we added so far is only incomplete.
    # Now we will retrieve a parser that is able to parse a specific "version"
    # of a BMS file.
    completeParser = container.get_parser(estimatedVersion = 1)
    
    # output: [(0, 'Basic BMS Stuff'), (1, 'Game 1')]
    print completeParser.parents
    
    
    
    
     
    
    
    
