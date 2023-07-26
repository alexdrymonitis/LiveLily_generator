import os, sys
import re


# find all occurences of forward slashes if a model name is provided
def find_occurrences(string, ch):
    return [i for i, char in enumerate(string) if char == ch]


if __name__ == "__main__":

    if len(sys.argv) < 2:
        print("Usage: create_corpus.py /path/to/livelily/files [inst1 inst2 ...]")
        exit()

    livelily_files_dir = sys.argv[1]

    if len(sys.argv) > 2:
        inst_names = []
        for i in range(len(sys.argv)-2):
            inst_names.append(sys.argv[i+2])
    
    corpus_file = open("corpus.txt", "w")

    livelily_files =  os.listdir(livelily_files_dir)
    num_files = len(livelily_files)

    for i,file in enumerate(livelily_files):
        numerator = 4
        denominator = 4
        f = open(livelily_files_dir + file, "r")
        lines = f.readlines()
        f.close()
        start_writing = False
        bar_is_consistent = False
        temp_lines = []
        inst_counter = 0
        for j,line in enumerate(lines):
            if start_writing:
                # if the line includes only the closing curly bracket do nothing
                if "}" in line and len(line) <= 2:
                    pass
                else:
                    # first check the instrument name and change it if different than specified through args
                    backslash_ndx = line.find("\\")+1
                    white_space_ndx = line[backslash_ndx:].find(" ")
                    if white_space_ndx == -1:
                        white_space_ndx = len(line) - 1
                    else:
                        white_space_ndx += backslash_ndx
                    if line[backslash_ndx:white_space_ndx] != inst_names[inst_counter]:
                        str_to_write = line[:backslash_ndx] + inst_names[inst_counter] + line[white_space_ndx:]
                        temp_lines.append(str_to_write)
                    else: # if instrument name is correct, just write the line intact
                        temp_lines.append(line)
                    inst_counter += 1
                    total_dur = 0
                    tokens = line.split()
                    for token in tokens:
                        # accumulate durations to make sure the bar is consistent
                        dur = re.findall(r'\d+', token)
                        if len(dur) > 0:
                            int_dur = int(dur[0])
                            if "." in token:
                                int_dur += (int_dur / 2)
                            total_dur += denominator / int(dur[0])
                    if total_dur == numerator:
                        bar_is_consistent = True
                    elif "}" not in line or ("}" in line and len(line) > 2):
                        bar_is_consistent = False
            if "\\time" in line:
                numerator = int(line[6:6+line[6:].find("/")])
                denominator = int(line[line.find("/")+1:-1])
            elif "\\bar" in line:
                # first replace the bar number to 1
                white_space_ndxs = find_occurrences(line, " ")
                line = line[:white_space_ndxs[0]+1] + "1" + line[white_space_ndxs[1]:]
                if len(line) > 9: # if line is more than "\bar {\n"
                    backslash_ndx = line[1:].find("\\") + 1
                    if backslash_ndx > 0: # make sure the backslash is found
                        white_space_ndx = line[backslash_ndx:].find(" ")
                        white_space_ndx += backslash_ndx
                        if line[backslash_ndx:white_space_ndx] != inst_names[inst_counter]:
                            str_to_write = line[:backslash_ndx] + inst_names[inst_counter] + line[:white_space_ndx]
                            temp_lines.append(str_to_write)
                        else:
                            temp_lines.append(line)
                        inst_counter += 1
                    else: # otherwise just write the line
                        temp_lines.append(line)
                else: # if the line has only "\bar {\n" written in it, write it to the corpus
                    temp_lines.append(line)
                start_writing = True
            elif "}" in line:
                start_writing = False
                if bar_is_consistent:
                    for temp_line in temp_lines:
                        corpus_file.write(temp_line)
                    corpus_file.write("}\n\n")
                    bar_is_consistent = False
                inst_counter = 0
                temp_lines = []
        if i == num_files - 1:
            print(f"wrote {i+1} files")
    corpus_file.close()