import music21 as m21
import sys


def parse_xml(xml):
    this_part = 0
    measure = 0
    found_half_measure = False
    has_half_measure = False
    append_new_lists = True
    part_name = ""
    numerator = 4
    denominator = 4
    # measure number must be global within this function
    # because of measures numbered 4a can be safely skipped
    measure = 0
    notes = []
    durations = []
    dots = []
    alter = []
    octaves = []
    dur_dict = {"whole": 1, "half": 2, "quarter": 4, "eighth": 8, "16th": 16, "32nd": 32, "64th": 64}
    for line in xml:
        if "<part-name>" in line:
            part_name_start = line.find("<part-name>") + 11
            part_name_end = line[part_name_start:].find("</part-name>")
            part_name = line[part_name_start:part_name_start+part_name_end]
        elif "</part>" in line:
            this_part += 1
        elif "<measure" in line:
            measure_start_ndx = line.find("number") + 8
            measure_end_ndx = line[measure_start_ndx:].find('"')
            try:
                measure = int(line[measure_start_ndx:measure_start_ndx+measure_end_ndx])
                append_new_lists = True
            except ValueError:
                # some bars are named 4a, and they include notes of the original bar
                append_new_lists = False
            # a measure numbered 0 is a half measure, and we don't want to store it
            if measure == 0:
                found_half_measure = True
                has_half_measure = True
            else:
                found_half_measure = False
            if append_new_lists:
                notes.append([])
                durations.append([])
                dots.append([])
                alter.append([])
                octaves.append([])
        elif "<beats>" in line:
            beats_start = line.find("<beats>") + 7
            beats_end = line[beats_start:].find("</beats>")
            numerator = int(line[beats_start:beats_start+beats_end])
        elif "<beat-type>" in line:
            beat_type_start = line.find("<beat-type>") + 11
            beat_type_end = line[beat_type_start:].find("</beat-type>")
            denominator = int(line[beat_type_start:beat_type_start+beat_type_end])
        elif "<step>" in line:
            if not found_half_measure:
                step_start = line.find("<step>") + 6
                step_end = line[step_start:].find("</step>")
                notes[-1].append(line[step_start:step_start+step_end].lower())
                alter[-1].append(0)
        elif "<alter>" in line:
            if not found_half_measure:
                alter_start = line.find("<alter>") + 7
                alter_end = line[alter_start:].find("</alter>")
                alter[-1][-1] = int(line[alter_start:alter_start+alter_end])
        elif "<octave>" in line:
            if not found_half_measure:
                octave_start = line.find("<octave>") + 8
                octave_end = line[octave_start:].find("</octave>")
                octaves[-1].append(int(line[octave_start:octave_start+octave_end]))
        elif "<rest" in line:
            if not found_half_measure:
                notes[-1].append("r")
                alter[-1].append(0)
                octaves[-1].append(3) # this will be zeroed when written to a LiveLily file
                if "measure" in line:
                    durations[-1].append(dur_dict["whole"])
                    dots[-1].append(0)
        elif "<type>" in line:
            if not found_half_measure:
                type_start = line.find("<type>") + 6
                type_end = line[type_start:].find("</type>")
                durations[-1].append(dur_dict[line[type_start:type_start+type_end]])
                dots[-1].append(0)
        elif "<dot" in line:
            if not found_half_measure:
                dots[-1][-1] += 1
    return part_name, numerator, denominator, notes, alter, octaves, durations, dots, has_half_measure


if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: music21_corpus.py name_of_composer")
        exit()
    composer = sys.argv[1]
    all_compositions = m21.corpus.search(composer)

    for ndx,piece in enumerate(all_compositions):
        bach = piece.parse()
        part_stream = bach.parts.stream()
        parts = []
        num_parts = len(part_stream)
        if num_parts == 4:
            xml_list = []
            for i in range(num_parts):
                GEX = m21.musicxml.m21ToXml.GeneralObjectExporter(part_stream[i])
                out = GEX.parse()
                xml_list.append(out.decode('utf-8').split('\n'))
            
            file_name = "./xml_files/bach" + str(ndx) + ".xml"
            print(f"will write {file_name}")
            f = open(file_name, "w")
            for xml in xml_list:
                for line in xml:
                    f.write(line)
                    f.write('\n')
            f.close()

            parts = []
            times = []
            all_notes = []
            all_alter = []
            all_octaves = []
            all_durations = []
            all_dots = []
            
            for xml in xml_list:
                part_name, numerator, denominator, notes, alter, octaves, durations, dots, found_half_measure = parse_xml(xml)
                parts.append(part_name)
                times.append(str(numerator) + "/" + str(denominator))
                if found_half_measure:
                    try:
                        notes.pop(-1)
                        alter.pop(-1)
                        octaves.pop(-1)
                        durations.pop(-1)
                        dots.pop(-1)
                    except IndexError:
                        pass
                all_notes.append(notes)
                all_alter.append(alter)
                all_octaves.append(octaves)
                all_durations.append(durations)
                all_dots.append(dots)
            
            # assemble bars so each bar holds notes for all instruments
            mixed_notes = {}
            mixed_alter = {}
            mixed_octaves = {}
            mixed_durations = {}
            mixed_dots = {}
            for i,part in enumerate(all_notes):
                mixed_notes[parts[i]] = part
            for i,part in enumerate(all_alter):
                mixed_alter[parts[i]] = part
            for i,part in enumerate(all_octaves):
                mixed_octaves[parts[i]] = part
            for i,part in enumerate(all_durations):
                mixed_durations[parts[i]] = part
            for i,part in enumerate(all_dots):
                mixed_dots[parts[i]] = part            
            
            file_name = "./livelily_files/livelily_bach" + str(ndx) + ".lyv"
            print(f"will write {file_name}")
            f = open(file_name, "w")
            f.write("\\score show\n")
            f.write("\\score animate showbeat\n")
            f.write("\n")
            f.write("\\insts")
            for inst in parts:
                f.write(" " + inst)
            f.write("\n")
            if "Tenor" in parts:
                f.write("\\Tenor \\clef bass\n")
            if "Bass" in parts:
                f.write("\\Bass \\clef bass\n")
            f.write("\n")
            f.write("\\time " + str(numerator) + "/" + str(denominator) +"\n\n")
            for bar_num in range(len(mixed_notes[parts[0]])):
                f.write("\\bar " + str(bar_num+1) + " {\n")
                for part in parts:
                    f.write("\t\\" + part)
                    for ndx,note in enumerate(mixed_notes[part][bar_num]):
                        f.write(" " + note) # + lily_alter[mixed_alter[part][bar_num][ndx]])
                        if mixed_alter[part][bar_num][ndx] > 0:
                            alter_str = "is"
                        elif mixed_alter[part][bar_num][ndx] < 0:
                            alter_str = "es"
                        else:
                            alter_str = ""
                        for i in range(abs(mixed_alter[part][bar_num][ndx])):
                            f.write(alter_str)
                        lily_octave = mixed_octaves[part][bar_num][ndx] - 3
                        if lily_octave > 0:
                            octave_symbol = "'"
                        elif lily_octave < 0:
                            octave_symbol = ","
                        else:
                            octave_symbol = ""
                        for i in range(abs(lily_octave)):
                            f.write(octave_symbol)
                        f.write(str(mixed_durations[part][bar_num][ndx]))
                        for i in range(mixed_dots[part][bar_num][ndx]):
                            f.write(".")
                    f.write("\n")
                f.write("}\n\n")
                bar_num += 1
            f.close()
