name = "WindWaker"
estimatedVersion = 1.5

def parse_next_command(read, bmsfile, strict = True):
        valuePos = int(bmsfile.tell())
        value = read.byte()
        print hex(value), "HEY"
        # We will store arguments for callback functions
        # in the args variable. Some controller events might
        # not have any arguments, so the variable will be
        # None, but otherwise it will be redefined by
        # the parsers for the controller events.
        args = None
        
        currPos = int(bmsfile.tell())
        
        if value <= 0x7F: 
            # Values below and equal to 127 are note-on events
            # Depending on the value, they turn on specific notes.
            
            note_on_event = value
            polyphonicID = read.byte()
            volume = read.byte()
            
            args = (note_on_event, polyphonicID, volume)
            
            # Generally, polyphonic IDs should range from 1 to 7,
            # but in some special cases it is possible that they range from 0 up to 15,
            # mostly only directly after a 0xB1 controller event.
            # This could be due to malformed data, needs more investigation.
            if strict and polyphonicID > 0xF:
                position = bmsfile.tell()
                raise RuntimeError("Invalid Polyhponic ID ({0}) at offset {1} ({2}) "
                                   "".format(hex(polyphonicID), position, hex(position))
                                   )
                
            
            #print "Reading note {0} with polyphonic ID {1} ({3}) and volume {2}".format(hex(note_on_event),
            #                                                                      polyphonicID,
            #                                                                      volume, polyphonicID & 0b111)
            return note_on_event, args
        
        else:
            # Values above 127 are controller events.
            # They can change the flow of the music sequence,
            # initiate additional tracks or turn off notes with
            # a specific polyphonic ID.
            controlEventID = value
            
            
            if controlEventID == 0x80: # Delay, up to 0xFF (255) ticks
                delayLength_inTicks = read.byte()
                
                args = (delayLength_inTicks, )
            
            elif controlEventID >= 0x81 and controlEventID <= 0x87: # note-off event
                # Each ID refers to a specific polyphonic ID.
                # 0x81 refers to 1, 0x82 refers to 2, etc.
                #
                # We can retrieve the correct ID by taking
                # the three least significant bits of the byte.
                polyphonicID = controlEventID & 0b111 
                
                args = (polyphonicID, )
                
                #print "Turning off note with polyphonic ID {0}".format(polyphonicID)
                
            elif controlEventID == 0x88: # Delay, up to 0xFFFF (65535) ticks
                delayLength_inTicks = read.short()
                
                args = (delayLength_inTicks, )
            
            elif controlEventID == 0x98: # Unknown
                # The data might either be two seperate
                # bytes or a single short.
                unknown1 = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, unknown2)
            
            elif controlEventID == 0x9A: # Pan Change
                unknown1 = read.byte()
                pan = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, pan, unknown2)
            
            elif controlEventID == 0x9C: # Volume Change
                unknown1 = read.byte()
                volume = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, volume)
            
            elif controlEventID == 0x9E: # Pitch Shift
                unknown1 = read.byte()
                pitch = read.ushort()
                unknown2 = read.byte()
                
                args = (unknown1, pitch, unknown2)
                
            elif controlEventID == 0xA0: # Unknown
                #unknown1 = read.short()
                
                #args = (unknown1, )
                pass
            
            elif controlEventID == 0xA2: # Unknown
                pass
            
            elif controlEventID == 0xA3: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
                
            elif controlEventID == 0xA4: # Bank Select/Program Select
                unknown1 = read.byte()
                
                if unknown1 == 32:
                    instrument_bank = read.byte()
                    args = (unknown1, instrument_bank)
                    
                elif unknown1 == 33:
                    program = read.byte()
                    args = (unknown1, program)
                    
                else:
                    unknown2 = read.byte()
                    args = (unknown1, unknown2)
                    
            
            elif controlEventID == 0xA5: # Unknown
                unknown1 = read.short()
                args = (unknown1, )
            
            elif controlEventID == 0xA6: # Unknown
                pass
            
            elif controlEventID == 0xA7: # Unknown
                unknown1 = read.short()
                args = (unknown1, )
            
            elif controlEventID == 0xA9: # Unknown
                unknown1 = read.int()
                args = (unknown1, )
            
            elif controlEventID == 0xAA: # Unknown
                unknown1 = read.int()
                args = (unknown1, )
                
            elif controlEventID == 0xAC: # Unknown
                # Could be a single 3 bytes integer,
                # 3 separate bytes, or one byte and one
                # short integer.
                unknown1 = read.byte()
                unknown2 = read.byte()
                unknown3 = read.byte()
                
                args = (unknown1, unknown2, unknown3)
            
            # This controller event seems to be used
            # only by se.bms, though I have not yet
            # figured out whether it has two or three
            # bytes of data.
            #
            #elif controlEventID == 0xAD: # Unknown
            #    read.byte()
            #    read.short()

            
            elif controlEventID == 0xB1: # Unknown
                #read.int()
                unknown1 = read.byte() # Always 0xC1
                assert unknown1 == 0xC1
                
                unknown2 = read.byte()
                
                if unknown2 == 0x80:
                    unknown3 = read.int()
                elif unknown2 == 0x40:
                    unknown3 = read.short()
                else:
                    raise RuntimeError("Value is neither 0x40 nor 0x80, this requires investigation!")
                
                args = (unknown1, unknown2, unknown3)
            
            elif controlEventID == 0xB8: # Unknown
                unknown1 = read.short()
                args = (unknown1, )
            
            elif controlEventID == 0xBE: # Unknown
                pass
                
            elif controlEventID == 0xC1: # Track List Num + Offset
                newTrackNum = read.byte()
                newTrackOffset = read.tripplet_int()
                
                args = (newTrackNum, newTrackOffset)
            
            elif controlEventID == 0xC2: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xC4: # Goto a specific offset
                goto_offset = read.int()
                
                args = (goto_offset, )
            
            elif controlEventID == 0xC5: # Unknown
                # In JAudio Player this was a 'Jump back
                # to reference' marker
                #read.tripplet_int()
                pass
            
            elif controlEventID == 0xC6: # Return to previous position
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xC7: # Unknown
                # In JAudio Player this was 'loop to offset'
                unknown1 = read.byte()
                unknown2 = read.tripplet_int()
                
                args = (unknown1, unknown2)
            
            elif controlEventID == 0xC8: # Loop to offset
                #read.byte()
                #read.tripplet_int()
                
                # Can be 0, 1 or 5?
                # 0 = absolute, 1 = relative position?
                mode = read.byte() 
                
                loop_offset = read.tripplet_int()
                
                args = (mode, loop_offset)
            
            elif controlEventID == 0xCB: # Unknown
                unknown1 = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, unknown2)
            
            elif controlEventID == 0xCC: # Unknown
                unknown1 = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, unknown2)
                
            elif controlEventID == 0xCF: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
                
            elif controlEventID == 0xD0: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xD1: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xD2: # Unknown
                print "HEY"
                unknown1 = read.byte()
                unknown2 = read.byte()
                
                args = (unknown1, unknown2)
                
            elif controlEventID == 0xD5: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xDA: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xDB: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
                
            elif controlEventID == 0xDF: # Unknown
                unknown1 = read.byte()
                unknown2 = read.tripplet_int()
                
                args = (unknown1, unknown2)
                
            elif controlEventID == 0xE0: # Unknown
                # In JAudio Player this was Tempo with 
                # two bytes of data.
                # In Pikmin 2 it could be three bytes of data.
                unknown1 = read.byte()
                unknown2 = read.short()
                
                args = (unknown1, unknown2)
            
            elif controlEventID == 0xE1: # Unknown
                pass
            
            elif controlEventID == 0xE3: # Unknown 
                # In JAudio Player this was Instrument change with 
                # one byte of data.
                # In the Pikmin 2 bms file it seems to be something
                # else, no data follows it.
                pass
            
            elif controlEventID == 0xE6: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
                
            elif controlEventID == 0xE7: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xEF: # Unknown
                unknown1 = read.byte()
                unknown2 = read.byte()
                unknown3 = read.byte()
                
                args = (unknown1, unknown2, unknown3)
            
            elif controlEventID == 0xF0: # Delay (variable-length quantity)
                start = bmsfile.tell()
                
                value = read.byte()
                
                # The most significant bit in the value
                # tells us that we need to read another byte.
                # We keep doing it until the most significant 
                # bit in the new value stops being 1 (i.e., 0).
                while (value >> 7) == 1:
                    value = read.byte()
                
                dataLen = bmsfile.tell() - start
                bmsfile.seek(start)
                
                data = read.byteArray(dataLen)
                
                args = (data, )
            
            elif controlEventID == 0xF1: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xF4: # Unknown
                unknown1 = read.byte()
                
                args = (unknown1, )
            
            elif controlEventID == 0xF9: # Unknown
                unknown1 = read.short()    
                
                args = (unknown1, )
                
            elif controlEventID == 0xFD: # Unknown
                # In JAudio Player, this was a Marker event
                # with variable length.
                # In Pikmin 2 it is just two bytes of data.
                
                unknown1 = read.short()
                
                args = (unknown1, )
            
            elif controlEventID == 0xFE: # Unknown
                unknown1 = read.short()
                
                args = (unknown1, )
                
            elif controlEventID == 0xFF: # End of Track
                pass
            
            else:
                position = bmsfile.tell()
                raise RuntimeError("Unknown controlEventID {0} "
                                   "at offset {1} ({2})".format(hex(controlEventID),
                                                                valuePos, hex(valuePos)))
        return controlEventID, args