import struct

class TriedToAddDeprecatedCommand(Exception):
	def __init__(self, cmdID, version):
		self.cmd = cmdID
		self.ver = version
	
	def __str__(self):
		return ("Tried to add command {x:cmdID} in parser version {ver}, "
				"but it has been marked as deprecated in the same version."
				"".format(cmdID = self.cmd, ver = self.ver)
				)

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
        
		self.deprecated = []
		
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
    
	# In cases where you are sure that a "version" of the
	# BMS format does not use specific commands anymore, you
	# can mark them as deprecated, causing the parser to
	# raise an exception because of an unknown command ID.
	def deprecate_parser_function(self, *commandIDs):
		for cmd in commandIDs: 
			if cmd in self.command_parsers:
				raise RuntimeError(	"Tried to deprecate command {x:cmd}"
									"but the current parser already defined"
									"that command!".format(cmd = cmd))
									
			self.deprecated.append(cmd)

def create_parser_function(struct_datastructure):
    structObj = struct.Struct(struct_datastructure)
    
    def parser_func(bmsfile, read, strict, commandID == None):
        bin_data = bmsfile.read(structObj.size)
        values = structObj.unpack(bin_data)
        
        return values
    
    return parser_func

if __name__ == "__main__":
    """container = ParserContainer()
    
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
    
    print map(hex, completeParser.command_parsers.keys())
    """
	container = ParserContainer()
	
	
	baseParser = VersionSpecificParser(0, "BMS Base Events")
	
	# Note-on Event
	baseParser.set_parser_function_range(	create_parser_function("bb"), 
											0x00, 0x80)
	
	# Delay event for up to 255 ticks
	baseParser.set_parser_function(	create_parser_function("B"), 
									0x81)
	
	# Note-off event
	def parse_noteOff(bmsfile, read, strict, commandID):
		return (commandID & 0b111, )		
    baseParser.set_parser_function_range(	parse_noteOff, 
											0x81, 0x88)
    
	# Delay event for up to 0xFFFF (65535) ticks
	baseParser.set_parser_function(	create_parser_function(">H"), 
									0x88)
	
	# Pan change: Unknown, Pan, Unknown
	baseParser.set_parser_function(	create_parser_function(">BBB"), 
									0x9A)
    
	# Volume Change: Unknown, volume
    baseParser.set_parser_function(	create_parser_function(">BH"), 
									0x9C)
	
	# Pitch shift: Unknown, Pitch, Unknown
    baseParser.set_parser_function(	create_parser_function(">BHB"), 
									0x9E) 
    
    # Bank Select/Program Select: Unknown, Value
	# If unknown == 32, value is instrument bank
	# If unknown == 33, value is program (i.e. an ID of an instrument
	baseParser.set_parser_function(	create_parser_function(">BB"), 
									0xA4)
	
	# Create new subroutine: Track ID, Track Offset (3 bytes!)
	baseParser.set_parser_function(	create_parser_function(">BBBB"), 
									0xC1)
	
	# Goto offset: Offset
	baseParser.set_parser_function(	create_parser_function(">I"), 
									0xC4)
	
	# Go back to last stored position, no arguments
	baseParser.set_parser_function(	create_parser_function(""), 
									0xC6)
	
	# Loop to offset: Mode, Offset (Three bytes!)
	baseParser.set_parser_function(	create_parser_function(">BBBB"), 
									0xC8)
	
	# Variable-length delay
	def parse_VL_delay(bmsfile, read, strict, commandID):
		start = bmsfile.tell()
		
		value = read.byte()
		
		while (value >> 7) == 1:
			value = read.byte()
		
		dataLen = bmsfile.tell() - start
		bmsfile.seek(start)
		
		data = read.byteArray(dataLen)
		
		return (data, )
	
	baseParser.set_parser_function(	parse_VL_delay, 
									0xF0)
									
	# BPM Value
	baseParser.set_parser_function(	create_parser_function(">H"), 
									0xFD)
	
	# PPQN Value
	baseParser.set_parser_function(	create_parser_function(">H"), 
									0xFE)
	
	# End of Track
	baseParser.set_parser_function(	create_parser_function(""), 
									0xFF)
    
	
	container.add_parser(baseParser)
	
	# Pikmin 1 Parsing stuff
	Pik1_parser = VersionSpecificParser(0.5, "Pikmin 1")
	
	container.add_parser(baseParser)
	
	# Super Mario Sunshine Parsing Stuff
	SMSunshine_parser = VersionSpecificParser(1, "Super Mario Sunshine")
	
	container.add_parser(SMSunshine_parser)
	
	# Zelda: Wind Waker Parsing Stuff
	Zelda_WW_parser = VersionSpecificParser(1.5, "Zelda: WW")
	
	container.add_parser(Zelda_WW_parser)
	
	# Pikmin 2 Parsing Stuff
	Pik2_parser = VersionSpecificParser(2, "Pikmin 2")
	
	# Volume Change: Unknown, Volume (2 bytes instead of 1 byte previously)
	Pik2_parser.set_parser_function(create_parser_function(">BH"),
									0x9C)
	
	container.add_parser(Pik2_parser)