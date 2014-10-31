import struct

class TriedToAddDeprecatedCommand(Exception):
    def __init__(self, cmdID, version):
        self.cmd = hex(cmdID)
        self.ver = version
        
    def __str__(self):
        return (
                "Tried to add command {cmdID} in parser version {ver}, "
                "but it has been marked as deprecated in the same version."
                "".format(cmdID = self.cmd, ver = self.ver)
                )
    
    def __repr__(self):
        return str(self)

class DuplicateCommand(Exception):
    def __init__(self, cmdID, version):
        self.cmd = hex(cmdID)
        self.version = version 
    
    def __str__(self):
        return ("Tried to add a command ID twice: {0} in version {1}"
                "").format(self.cmd, self.version)

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
        self.deprecated = {}
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
            if commandID not in self.deprecated:
                self.command_parsers[commandID] = function
        
        
        
    
    def set_parser_function(self, function, commandID):
        if commandID in self.deprecated:
            raise TriedToAddDeprecatedCommand(commandID, self.estimatedVersion)
        elif commandID in self.command_parsers:
            raise DuplicateCommand(commandID, self.estimatedVersion)
        
        self.command_parsers[commandID] = function
    
    # Helper function to add a parser function to a range of command IDs.
    # Please note that the function will be applied to the command IDs from
    # 'start_commandID' to 'end_commandID - 1'.
    # This is useful for adding parsers for the note-on events, of which there are
    # 128. (command ID 0x00 to 0x7F)
    def set_parser_function_range(self, function, start_commandID, end_commandID):
        for commandID in xrange(start_commandID, end_commandID):
            if commandID in self.deprecated:
                raise TriedToAddDeprecatedCommand(commandID, self.estimatedVersion)
            elif commandID in self.command_parsers:
                raise DuplicateCommand(commandID, self.estimatedVersion)
            
            self.command_parsers[commandID] = function
    
    # Helper function to add a parser function to a specific set of command IDs.
    # Some command IDs might have similar data structures, so this can be used
    # to cut down the amount of code wasted on writing duplicate parsers.
    def set_many_parser_functions(self, function, *commandIDs):
        for commandID in commandIDs:
            if commandID in self.deprecated:
                raise TriedToAddDeprecatedCommand(commandID, self.estimatedVersion)
            elif commandID in self.command_parsers:
                raise DuplicateCommand(commandID, self.estimatedVersion)
            
            self.command_parsers[commandID] = function
    
    # In cases where you are sure that a "version" of the
    # BMS format does not use specific commands anymore, you
    # can mark them as deprecated, causing the parser to
    # raise an exception because of an unknown command ID.
    def deprecate_parser_function(self, *commandIDs):
        for cmd in commandIDs: 
            if cmd in self.command_parsers:
                raise RuntimeError( "Tried to deprecate command {cmd} "
                                    "but the current parser already defined "
                                    "that command!".format(cmd = hex(cmd)))
            self.deprecated[cmd] = True
    
    def parse_next_cmd(self, bmsfile, readObj, strict = False):
        cmdID = readObj.byte()
        
        if cmdID not in self.command_parsers:
            offset = int(bmsfile.tell() - 1)
            
            raise RuntimeError("Unknown Command ID: {cmdID} at offset {offset}"
                               "".format(cmdID = cmdID, offset = hex(offset)))
        else:
            parser_func = self.command_parsers[cmdID]
            args = parser_func(bmsfile, readObj, strict, cmdID)
            
            return args
            
            
            

def create_parser_function(struct_datastructure):
    structObj = struct.Struct(struct_datastructure)
    
    def parser_func(bmsfile, read, strict, commandID = None):
        bin_data = bmsfile.read(structObj.size)
        values = structObj.unpack(bin_data)
        
        return values
    
    return parser_func