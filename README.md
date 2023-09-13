# LiveLily_generator
This code creates a GRU RNN that generates LiveLily code.
The first thing that needs to be done, is to create a corpus in the LiveLily format. This can be done with the music21_corpus.py file. Run this file, and provide the name of the composer you want to use their music as an argument. This script saves the .xml files in a subdirectory named "xml_files/", and the LiveLily files in a subdirectory named "livelily_files/", so go ahead and create those first.

##
Once all the LiveLily files have been created, run the create_corpus.py script, and provide the /path/to/the/livelily/files as the first argument, and, optionally, the names of the instruments you want to use. This will help correct any mismatches in the names of the instruments in the saved LiveLily files.

##
After you have created the corpus, you can run the create_livelily_generator.py script, by providing the /path/to/the/corpus.txt file as an argument. Optionally, you can provide the name of the network to be saved, otherwise, the saved network will be named "one_step". This is copied from a [tutorial](https://www.tensorflow.org/text/tutorials/text_generation) provided in the TensorFlow website. The script will train a character-level GRU RNN text generator for 30 epochs. When the training is done, you can invoke the trained model by running the generate_bars.py script, and by providing it the /path/to/the/saved/model as an argument. This script will monitor the keyboard, and when in LiveLily you type "%generate [prompt]" and hit Shift+Return, it will generate LiveLily text based on the prompt. A prompt should either be "\bar", or nothing. In case of no prompt, the network will generate text using its previous output as the prompt. This enables the bars to have some sort of coherence, as far as the composition is concerned. In LiveLily, you must have enabled typing througη OSC, by executing the "\fromosc" command.

## Python modules used
- tensorflow
- pynput
- python-osc
- music21
- numpy
