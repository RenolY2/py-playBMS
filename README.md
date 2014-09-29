py-playBMS
==========

A project that aims to read and play back BMS files used by some Gamecube games.  
It is in development, though it can already parse and play back some Pikmin 2 BMS files.

Dependencies
==========

At the moment, the project realies on pygame for music/midi playback. 
This can be subject to change as music playback is being worked on.

Usage
==========
Put the Pikmin 2 BMS files (or the BMS files from a different game, if you feel like experimenting),
into the same folder as the pyBMS.py file, or create a new folder for the BMS files 
if you do not want to clog up the root directory. Change the PATH variable at the 
bottom of the pyBMS.py file to point to the file you want to play, then execute pyBMS.py.
The program will parse the file and play the notes on the go. It does not create midi files (yet).

If the tempo feels off, you can attempt to change the BPM and PPQM variables to adjust the playback speed.
