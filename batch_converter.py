import os
import struct

from pyBMS import BmsInterpreter



if __name__ == "__main__":
    input_dir = "zelda_bms"#"pikmin2_bms"
    output_dir = os.path.join("output", input_dir)
    parser = "zeldawindwaker"

    instrument_bank = 0
    bpm = 100

    print(os.listdir(input_dir))


    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    for bms_file in os.listdir(input_dir):
        if bms_file.endswith(".bms"):
            input_path = os.path.join(input_dir, bms_file)

            with open(input_path, "rb") as f:
                #bms_data = StringIO(f.read())

                bms_parser = BmsInterpreter(f.read(), parser_name=parser)#bms_data)

            try:
                bms_parser.parse_file()
            except struct.error as e:
                #print e
                print "{input} successully parsed".format(input=input_path)
            except Exception as e:
                print "{input} not parsed".format(input=input_path)
                continue


            midi = bms_parser.scheduler.compile_midi(instrument_bank=instrument_bank, bpm=bpm)

            output_path = os.path.join(output_dir, bms_file+".midi")
            with open(output_path, "wb") as f:
                midi.write_midi(f)



