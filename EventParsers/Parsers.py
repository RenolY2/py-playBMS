from parser_creator import (ParserContainer,
                           VersionSpecificParser)

from parser_creator import create_parser_function as bin_struct


from parser_helper import    (parse_1Byte_1Tripplet,
                            parse_noteOff,
                            parse_VL_delay)

container = ParserContainer()


baseParser = VersionSpecificParser(0, "BMS Base Events")

# Note-on Event
baseParser.set_parser_function_range(   bin_struct("bb"), 
                                        0x00, 0x80)

# Delay event for up to 255 ticks
baseParser.set_parser_function( bin_struct("B"), 
                                0x80)

# Note-off event
baseParser.set_parser_function_range(   parse_noteOff, 
                                        0x81, 0x88)

# Delay event for up to 0xFFFF (65535) ticks
baseParser.set_parser_function( bin_struct(">H"), 
                                0x88)

# Pan change: Unknown, Pan, Unknown
baseParser.set_parser_function( bin_struct(">BBB"), 
                                0x9A)

# Volume Change: Unknown, volume
baseParser.set_parser_function( bin_struct(">BH"), 
                                0x9C)

# Pitch shift: Unknown, Pitch, Unknown
baseParser.set_parser_function( bin_struct(">BHB"), 
                                0x9E) 

# Bank Select/Program Select: Unknown, Value
# If unknown == 32, value is instrument bank
# If unknown == 33, value is program (i.e. an ID of an instrument)
baseParser.set_parser_function( bin_struct(">BB"), 
                                0xA4)



# Create new subroutine: Track ID, Track Offset (3 bytes!)
baseParser.set_parser_function( parse_1Byte_1Tripplet, 
                                0xC1)

# Goto offset: Offset
baseParser.set_parser_function( bin_struct(">I"), 
                                0xC4)

# Go back to last stored position, one byte
baseParser.set_parser_function( bin_struct("B"), 
                                0xC6)

# Loop to offset: Mode, Offset (Three bytes!)
baseParser.set_parser_function( parse_1Byte_1Tripplet, 
                                0xC8)


baseParser.set_parser_function( parse_VL_delay, 
                                0xF0)
# BPM Value
baseParser.set_parser_function( bin_struct(">H"), 
                                0xFD)

# PPQN Value
baseParser.set_parser_function( bin_struct(">H"), 
                                0xFE)

# End of Track
baseParser.set_parser_function( bin_struct(""), 
                                0xFF)


container.add_parser(baseParser)

# Pikmin 1 Parsing stuff
Pik1_parser = VersionSpecificParser(0.5, "Pikmin 1")

# Unknown Values


Pik1_parser.set_many_parser_functions(bin_struct(">H"), 
                                      0xC9, 0xD0,
                                      0xE7)

Pik1_parser.set_many_parser_functions(bin_struct(">BB"),
                                      0x98, 0xCB, 0xD2)

Pik1_parser.set_many_parser_functions(bin_struct(">B"),
                                      0xCD, 0xDE,
                                      0xF1)

Pik1_parser.set_many_parser_functions(  bin_struct(""), #for deletion: 0xA2, 0xB0, 0xC5, 0xCA, 0xA6?
                                        0xE3)
#                                      0xA9, 0xBE, 
#                                      0xE1, 0xE3, 0xF4)
                                      
Pik1_parser.set_parser_function(bin_struct(">HB"), 
                                0x92)
Pik1_parser.set_parser_function(bin_struct(">I"), 
                                0xAA)
Pik1_parser.set_parser_function(bin_struct(">BBB"),
                                0xAC)
Pik1_parser.set_parser_function(bin_struct(">BBB"), 
                                0xAF)
Pik1_parser.set_parser_function(bin_struct(">BH"), 
                                0xDD)
Pik1_parser.set_parser_function(bin_struct(">I"), 
                                0xDF)
Pik1_parser.set_parser_function( bin_struct(">BBB"),
                                 0xEF)

container.add_parser(Pik1_parser)

# Super Mario Sunshine Parsing Stuff
SMSunshine_parser = VersionSpecificParser(1, "Super Mario Sunshine")

SMSunshine_parser.deprecate_parser_function(0xDE, 0xF4, 0xFA)
SMSunshine_parser.deprecate_parser_function(0x92, 0xAA, 0xAF, 0xC9, 0xCB, 0xCD, 
                                            0xD0, 0xD2, 0xDE, 0xDF, 0xE3, 0xF1)
    
    
# Volume Change: Unknown, volume (volume is only 1 byte instead of two bytes
#SMSunshine_parser.set_parser_function( volume_parse, 
#                                       0x9C)


container.add_parser(SMSunshine_parser)

# Zelda: Wind Waker Parsing Stuff
Zelda_WW_parser = VersionSpecificParser(1.5, "Zelda: WW")

# Volume Change: Unknown, volume (volume is 2 bytes again)
# Maybe Nintendo thought that Mario did not need such a precision for SMS,
# or maybe development of the audio engine for SMS was independent of the
# development of the audio engine for Pikmin 1, which was released earlier.
#Zelda_WW_parser.set_parser_function( bin_struct(">BH"), 
#                                     0x9C)

Zelda_WW_parser.set_parser_function( bin_struct(">B"),
                                     0xF4)

# Unknown event, the last two bytes are often 0xFFFF
Zelda_WW_parser.set_parser_function( bin_struct(">BH"),
                                     0xAD)

Zelda_WW_parser.set_parser_function( bin_struct(">BB"),
                                     0xA1)
Zelda_WW_parser.set_parser_function( bin_struct(">BB"),
                                     0xA6)

Zelda_WW_parser.set_parser_function( bin_struct("BB"), 
                                     0xE6)
Zelda_WW_parser.set_parser_function( bin_struct("BB"), 
                                     0xCC)

Zelda_WW_parser.deprecate_parser_function(0x92, 0xAA, 0xAF, 0xC9, 0xCD, 
                                          0xD0, 0xDE, 0xDF, 0xE3)
 

container.add_parser(Zelda_WW_parser)

# Pikmin 2 Parsing Stuff
Pik2_parser = VersionSpecificParser(2, "Pikmin 2")

Pik2_parser.deprecate_parser_function(0xD2, 0xF4)
Pik2_parser.set_parser_function(bin_struct("B"),
                                0xCF)

Pik2_parser.set_parser_function(bin_struct("BB"),
                                0xA3)

# Unknown
Pik2_parser.set_parser_function(bin_struct(">H"),
                                0xA0)

container.add_parser(Pik2_parser)

print "Done!"