from StringIO import StringIO

from OptionsCollector import OptionsCollector
from EventParsers import parsers
from EventParsers.parser_creator import VersionSpecificParser
from bmsmodules.data_reader import DataReader
from bmsmodules.subroutine_template import SubroutineTemplate as Subroutine
from bmsmodules.MidiWriter.midi_scheduler import MidiScheduler

# Estimated BMS versions for each of the game.
# They are not representatives of the actual version of the BMS format used,
# they only serve as a way to discern the BMS commands used in the files found
# in each game.
PARSERS = {"pikmin1": 0.5,
           "pikmin2": 2,
           "zeldawindwaker": 1.5,
           "supermariosunshine": 1}


class BmsSubroutines(object):
    def __init__(self, bmsfile, parser, options):
        self._subroutines = []
        self._bmsfile = bmsfile
        self._parser = parser
        self._options = options
    
    def add_subroutine(self, parent_id, track_id, offset):
        # Every subroutine parses the file independently. Therefore we
        # need to create a different file handle for each subroutine. To avoid
        # copying the data for every subroutine, we will create a "buffer" of the 
        # existing file handle.
        _bmsHandle = StringIO(buffer(self._bmsfile))
        
        reader = DataReader(_bmsHandle)
        
        # Our unique ID will simply consist of the current amount of subroutines.
        # We need an unique ID for every subroutine because the track IDs in BMS files start at 0,
        # but the main subroutine that spawns the subroutine needs a track ID for itself so that
        # the midi conversion works.
        unique_id = len(self._subroutines)

        subroutine = Subroutine(reader,
                                track_id, unique_id, parent_id,
                                offset, self._parser,
                                self._options)

        self._subroutines.append(subroutine)

    # Use this method to retrieve the UID of the last subroutine that has been added.
    # When the subroutine list is empty, this results in a negative ID.
    def get_previous_uid(self):
        return len(self._subroutines) - 1
        
    def __iter__(self):
        for subroutine in self._subroutines:
            yield subroutine

        raise StopIteration()


class BmsInterpreter(object):
    def __init__(self, fileobj, parser_name="pikmin2", custom_parser=None,
                 *args, **kwargs):

        self.options = OptionsCollector(base_bpm=100, base_ppqn=100)
        self._set_options(args, kwargs)

        self._bmsfile = fileobj
        
        if parser_name not in PARSERS:
            raise RuntimeError(
                "Parser '{parser_name}' doesn't exist! Parser must be one of the following:"
                "{parser_list}".format(
                    parser_name=parser_name,
                    parser_list=", ".join(PARSERS.keys())
                )
            )

        elif custom_parser is not None:
            if not isinstance(custom_parser, VersionSpecificParser):
                raise RuntimeError(
                    "Custom Parser needs to be an instance "
                    "of VersionSpecificParser, not {0}".format(
                        type(custom_parser)
                    )
                )
            else:
                self._parser = custom_parser
        else:
            self._parser = parsers.container.get_parser(PARSERS[parser_name])

        self.scheduler = MidiScheduler()
        self._subroutines = BmsSubroutines(self._bmsfile, self._parser,
                                           self.options)

        self._ticks = 0

    def _set_options(self, *args, **kwargs):
        self.options.set_options(**kwargs)
    
    def parse_file(self):
        # We add a main subroutine that starts doing the work.
        # As such, we set its parent id and track id both to None,
        # because it neither has a parent nor a BMS track id.
        self._subroutines.add_subroutine(None, None, 0)
        unique_id = self._subroutines.get_previous_uid()
        self.scheduler.add_track(unique_id, self._ticks)

        while True:
            # TODO: Add new subroutines when they are encountered.
            self._advance_tick()

        #return self.scheduler.compile_midi(INSTRUMENT_BANK=0, BPM=100)

    def _advance_tick(self):
        for sub in self._subroutines:
            cmd = sub.handle_next_command(self.scheduler, self._ticks)
            if cmd is None:
                pass
            else:
                #print cmd
                pass
        self._ticks += 1


if __name__ == "__main__":
    import os
    import struct
    #bmsfile = os.path.join("pikmin2_bms","n_tutorial_1stday.bms")



    input_path = os.path.join("pikmin2_bms", "yakushima.bms")
    output_path = "output.midi"
    parser = "pikmin2"


    with open(input_path, "rb") as f:
        #bms_data = StringIO(f.read())

        bms_parser = BmsInterpreter(f.read(), parser_name=parser)#bms_data)

    try:
        bms_parser.parse_file()
    except struct.error as e:
        print e
        print "reached end of file, most likely"

    midi = bms_parser.scheduler.compile_midi(instrument_bank=0, bpm=100)

    # This is the output file to which the result is written.
    with open(output_path, "wb") as f:
        midi.write_midi(f)