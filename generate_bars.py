"""
This script loads a GRU RNN created and trained based on the tutorial found here
https://www.tensorflow.org/text/tutorials/text_generation
"""

import tensorflow as tf
from pynput import keyboard
from pynput.keyboard import Key #, Controller
from pythonosc.udp_client import SimpleUDPClient
from time import sleep
import sys
from difflib import SequenceMatcher

if len(sys.argv) < 2:
    print("Usage generate_music.py /path/to/model [inst1 [inst2] [inst3]...]")
    exit()

model_name = sys.argv[1]

gru_rnn = tf.saved_model.load(model_name)

insts = []
if len(sys.argv) > 2:
    for i in range(len(sys.argv)-2):
        insts.append(sys.argv[i+2])
print(f"instruments: {insts}")

numerator = 4
denominator = 4


# find all occurences of forward slashes if a model name is provided
def find_occurrences(string, ch):
    return [i for i, char in enumerate(string) if char == ch]


def similarity(a, b):
    # get similarity of strings
    return SequenceMatcher(None, a, b).ratio()


def get_durs_in_string(string):
    int_ndxs = []
    ints = []
    is_dotted = []
    found_int = False
    for i,char in enumerate(string):
        if char.isdigit():
            if not found_int:
                int_ndxs.append([])
                is_dotted.append(False)
            int_ndxs[-1].append(i)
            found_int = True
        elif char == ".":
            is_dotted[-1] = True
        else:
            if found_int:
                int_ndxs[-1].append(i)
            found_int = False
    # the last pair of indexes might not be filled, if the line ends with a duration
    if len(int_ndxs[-1]) == 1:
        int_ndxs[-1].append(len(string))
    # if there is more than one digit in the duration, more than two indexes are saved
    # so we strip the index in the middle
    for i in range(len(int_ndxs)):
        int_ndxs[i] = [int_ndxs[i][0], int_ndxs[i][-1]]
    for i,int_ndx in enumerate(int_ndxs):
        if is_dotted[i]:
            second_ndx_offset = 1
        else:
            second_ndx_offset = 0
        ints.append(int(string[int_ndx[0]:int_ndx[1]-second_ndx_offset]))
    return ints, is_dotted


def generate_text(seed, num_iter):
    states = None
    next_char = tf.constant([seed])
    result = [next_char]

    for n in range(num_iter):
        next_char, states = gru_rnn.generate_one_step(next_char, states=states)
        result.append(next_char)

    text = tf.strings.join(result)[0].numpy().decode("utf-8")
    return text


def generate_music(seed):
    global prev_gen, bar_count

    string_to_prepend = ""
    update_bar_nr = True
    if seed == "\\bar":
        if len(insts) > 0:
            text = generate_text("\t\\" + insts[0], 200)
            string_to_prepend = "\\bar " + str(bar_count) + " {\n\t"
            bar_count += 1
            update_bar_nr = False
        else:
            text = generate_text(seed, 200)
    elif seed == "":
        text = generate_text(prev_gen, 300)
        curly_ndx = text.find("}")
        text = text[curly_ndx:]
    else:
        text = generate_text(seed, 200)

    # extract one bar only
    backslash_ndxs = find_occurrences(text, "\\")
    curly_bracket_ndxs = find_occurrences(text[backslash_ndxs[0]:], "}")

    text_to_print = text[backslash_ndxs[0]:backslash_ndxs[0]+curly_bracket_ndxs[0]+1]
    text_to_print = string_to_prepend + text_to_print
    # check the durations and make sure they are correct, otherwise correct them
    lines = text_to_print.split("\n")
    # remove first and last lines as we don't need to check these
    lines.pop(0)
    lines.pop(-1)
    regenerate = False
    for line in lines:
        total_dur = 0
        durations, is_dotted = get_durs_in_string(line)
        for i in range(len(durations)):
            durations[i] = denominator / durations[i]
            if is_dotted[i]:
                durations[i] += (durations[i] / 2)
            total_dur += durations[i]
        if total_dur != numerator:
            regenerate = True
    if not regenerate:
        if len(insts) > 0:
            stored_insts = []
            lines_to_ignore = []
            # correct possible mistakes in instrument names
            lines = text_to_print.split("\n")
            for i in range(len(lines)):
                if i > 0 and i < len(lines)-1:
                    if i-1 < len(insts):
                        slash = lines[i].find("\\")
                        white_space = lines[i].find(" ")
                        inst_name = lines[i][slash+1:white_space]
                        for inst in stored_insts:
                            if similarity(inst, inst_name) > .5:
                                lines_to_ignore.append(i)
                        if inst_name != insts[i-1]:
                            lines[i] = lines[i][:slash+1] + insts[i-1] + lines[i][white_space:]
                        if i not in lines_to_ignore:
                            stored_insts.append(insts[i-1])
            text_to_print = ""
            for i,line in enumerate(lines):
                if i not in lines_to_ignore:
                    text_to_print += line
                    text_to_print += "\n"
            # remove extra newline at the end
            text_to_print = text_to_print[:-1]
        prev_gen = text_to_print
        if update_bar_nr:
            white_space_ndxs = find_occurrences(text_to_print, " ")
            text_to_print = text_to_print[:white_space_ndxs[0]+1] + str(bar_count) + text_to_print[white_space_ndxs[1]:]
            bar_count += 1
        return text_to_print
    else:
        return None


def type_key(key):
    if key == 10:
        key_to_send = 13
    else:
        key_to_send = key
    client.send_message("/livelily1/press", key_to_send)
    sleep(0.015)
    client.send_message("/livelily1/release", key_to_send)


def type_music(music):
    global typing
    typing = True
    for char in music:
        # don't type tabs as these are inserted automatically in LiveLily
        if char != "\t":
            type_key(ord(char))
            sleep(0.03)
    typing = False


def on_press(key):
    global captured_str, shift_pressed, typing
    if not typing:
        if isinstance(key, keyboard._xorg.KeyCode):
            if key.char is not None:
                captured_str += key.char
        else:
            if key == keyboard.Key.enter:
                if shift_pressed:
                    if captured_str.startswith("%generate"):
                        end_of_seed = captured_str.find(" ")
                        if end_of_seed == -1:
                            seed = ""
                        else:
                            end_of_seed += 1
                            seed = captured_str[end_of_seed:]
                        music = generate_music(seed)
                        while music is None:
                            music = generate_music(seed)
                        try:
                            type_music(music[:-2]) # don't type the closing bracket and the last return
                        except TypeError:
                            type_music("an error occured")
                captured_str = ""
            elif key == Key.space:
                captured_str += " "
            elif key == Key.backspace:
                captured_str = captured_str[:-1]
            elif key == Key.shift or key == Key.shift_r or key == Key.shift_l:
                shift_pressed = True


def on_release(key):
    global shift_pressed
    if isinstance(key, keyboard._xorg.KeyCode):
        if key.vk == 65032:
            shift_pressed = False


if __name__ == "__main__":
    prev_gen = ""
    bar_count = 1

    captured_str = ""
    shift_pressed = False
    typing = False

    client = SimpleUDPClient("127.0.0.1", 9050)

    print("Monitoring the keyboard...")

    with keyboard.Listener(
        on_press=on_press,
        on_release=on_release) as listener:
        listener.join()
