import struct


class TriedToAddDeprecatedCommand(Exception):
    def __init__(self, cmd_id, version):
        self.cmd = hex(cmd_id)
        self.ver = version
        
    def __str__(self):
        return (
            "Tried to add command {cmd_id} in parser version {ver}, "
            "but it has been marked as deprecated in the same version."
            "".format(cmd_id=self.cmd, ver=self.ver)
            )
    
    def __repr__(self):
        return str(self)


class DuplicateCommand(Exception):
    def __init__(self, cmd_id, version):
        self.cmd = hex(cmd_id)
        self.version = version 
    
    def __str__(self):
        return ("Tried to add a command ID twice: {cmd_id} in version {ver}"
                "").format(cmd_id=self.cmd, ver=self.version)


class ParserContainer(object):
    def __init__(self):
        self.parsers = {}
        
        self.versions = []
        
    def add_parser(self, parser):
        # The version number has to be either an integer or a float, any other
        # value makes no sense in this context.
        assert isinstance(parser.estimated_version, (int, float)) is True
        
        if parser.estimated_version in self.parsers:
            existing_name = self.parsers[parser.estimated_version].gameName
            
            raise RuntimeError("Parser version ({version}) of '{newParserName}' "
                               "already in use by parser '{existingParser}'".format(version=parser.estimated_version,
                                                                                    newParserName=parser.gameName,
                                                                                    existingParser=existing_name))
        self.versions.append(parser.estimated_version)
        self.parsers[parser.estimated_version] = parser
        self.versions.sort()
    
    def get_parser(self, estimated_version):
        base_parser = VersionSpecificParser(estimated_version,
                                            "Parser v{0}".format(estimated_version))
        
        for version in self.versions:
            if version > estimated_version:
                break
            
            parent = self.parsers[version]

            # We apply all changes of the previous parsers to the current parser,
            base_parser.inherit_parsers(parent)
        
        return base_parser
    
class VersionSpecificParser(object):
    def __init__(self, estimated_version, game_name):
        self.command_parsers = {}
        self.estimated_version = estimated_version
        self.game_name = game_name
        self.deprecated = {}
        self.parents = []

    def inherit_parsers(self, parent):
        child_version = parent.estimated_version
        game_name = parent.game_name
        
        self.parents.append((parent, game_name))
        
        for command_id, function in parent.command_parsers.iteritems():
            if command_id not in parent.deprecated:
                self.command_parsers[command_id] = function
            elif command_id in self.command_parsers:
                del self.command_parsers[command_id]
        
        self.deprecated = parent.deprecated
        
        print parent.game_name, parent.estimated_version
        print self.deprecated
        print parent.deprecated

    def set_parser_function(self, function, command_id):
        if command_id in self.deprecated:
            raise TriedToAddDeprecatedCommand(command_id, self.estimated_version)
        elif command_id in self.command_parsers:
            raise DuplicateCommand(command_id, self.estimated_version)
        
        self.command_parsers[command_id] = function
    
    # Helper function to add a parser function to a range of command IDs.
    # Please note that the function will be applied to the command IDs from
    # 'start_command_id' to 'end_command_id - 1'.
    # This is useful for adding parsers for the note-on events, of which there are
    # 128. (command ID 0x00 to 0x7F)
    def set_parser_function_range(self, function, start_command_id, end_command_id):
        for command_id in xrange(start_command_id, end_command_id):
            if command_id in self.deprecated:
                raise TriedToAddDeprecatedCommand(command_id, self.estimated_version)
            elif command_id in self.command_parsers:
                raise DuplicateCommand(command_id, self.estimated_version)
            
            self.command_parsers[command_id] = function
    
    # Helper function to add a parser function to a specific set of command IDs.
    # Some command IDs might have similar data structures, so this can be used
    # to cut down the amount of code wasted on writing duplicate parsers.
    def set_many_parser_functions(self, function, *command_ids):
        for command_id in command_ids:
            if command_id in self.deprecated:
                raise TriedToAddDeprecatedCommand(command_id, self.estimated_version)
            elif command_id in self.command_parsers:
                raise DuplicateCommand(command_id, self.estimated_version)
            
            self.command_parsers[command_id] = function

    # Command IDs can be "deprecated", that means,
    # the command ID will not be accepted as valid when it
    # is encountered while parsing the file.
    def deprecate_parser_function(self, *command_ids):
        for cmd in command_ids:
            if cmd in self.command_parsers:
                raise RuntimeError("Tried to deprecate command {cmd} "
                                   "but the current parser already defined "
                                   "that command!".format(cmd=hex(cmd)))
            self.deprecated[cmd] = True
    
    def parse_next_cmd(self, bmsfile, reader, strict=False):
        cmd_id = reader.byte()
        
        if cmd_id not in self.command_parsers:
            offset = int(bmsfile.tell() - 1)
            # print type(cmdID), self.command_parsers.keys()
            raise RuntimeError("Unknown Command ID: {cmdID} at offset {offset}"
                               "".format(cmdID=hex(cmd_id), offset=hex(offset)))
        else:
            parser_func = self.command_parsers[cmd_id]
            args = parser_func(bmsfile, reader, strict, cmd_id)
            
            return cmd_id, args


def create_parser_function(struct_string):
    struct_obj = struct.Struct(struct_string)

    def parser_func(bmsfile, reader, strict, command_id=None):
        bin_data = bmsfile.read(struct_obj.size)
        values = struct_obj.unpack(bin_data)
        
        return values
    
    return parser_func