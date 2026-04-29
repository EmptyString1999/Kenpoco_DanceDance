import time
from re import sub
from sys import path as syspath
syspath.append("/Games/DanceDance") #fix imports

def calculate_timing(measure, measure_index, bpm, offset) -> list[str]:
    """
    calculate time in seconds for each line in the measure:
    1. BPM       = beats/minute -> BPS = beats/second = BPM/60
    2. measure   = 4 beats = 4 * 1/4th notes     = 1 note
    3. 1/256    -> 256 * 1/256th notes           = 1 measure
    """
    measure_seconds = 4 * 60/bpm                        # length of measure in seconds
    note_256        = measure_seconds/256               # length of each 1/256th note in the measure in seconds
    measure_timing  = measure_seconds * measure_index   # cumulative time summed from previous measures
    fraction_256    = 256/len(measure)                  # number of 1/256th notes per beat: 1/2nd = 128, 1/4th = 64, etc

    # returns the note/timing pair, if the note exists
    return [(measure[i], (i * note_256 * fraction_256 + measure_timing - offset)) for i, is_set in enumerate(measure) if is_set != None]

def convert_note(line: str) -> str:
    """
    We don't use Mines, Keysounds, Lifts, or Fake Notes at the moment so we are replacing them 
    with 0 meaning 'No Note'.
    M - Mine
    K - Keysound note (plays keysound)
    L - Lift note (release foot)
    F - Fake note (doesn’t judge) 
    """
    return sub('4', '2', sub('[MKLF]', '0', line))    #replaces extra notes: M, K, L, F; replaces 4 note

def parse_sm_file(sm_file: list[str]):
    print("parseing")
    bpm = 0
    offset = 0
    note_data = {} # maps difficulty to the note and the corrasponding time segment
    time_data = []
    measure = []
    measure_index = 0
    current_difficulty = ''

    for i, line in enumerate(sm_file):
        line = line.rstrip() # removes trailing newline '\n' and possible trailing whitespace
        if line.startswith("#OFFSET"):
            offset = float(line.split(':')[-1].split(';')[0])
            #print(offset)
        elif line.startswith("#BPMS"):
            bpm = int(line.split('=')[-1].split(';')[0])
            #print(bpm)
        elif line.startswith('#NOTES:'): # marks the beginning of each difficulty and its notes
            measure_index = 0
            current_difficulty = sm_file[i+3].lstrip(' ').rstrip(':\n') # difficulty always found 3 lines down
            if current_difficulty not in note_data.keys():
                note_data[current_difficulty] = []
            else:
                current_difficulty = "2Player_" + current_difficulty
                note_data[current_difficulty] = []
            #print(current_difficulty)
        elif line and not line.startswith((' ', '#', '/', ',', ';')): # individual notes
            note = convert_note(line)
            if note[0].isdigit():
                note_placed = True if any((c in set('1234')) for c in note) else False
                if note_placed:
                    measure.append(note) # adds note if found
                else:
                    measure.append(None)
        elif line.startswith((',', ';')): # marks the end of each measure
            notes_and_timings = calculate_timing(measure, measure_index, bpm, offset)
            note_data[current_difficulty].extend(notes_and_timings)
            measure.clear()
            measure_index += 1
    return note_data


def main():
    #start_time = time.time()
    sm_file = open("src/DanceDance/7_colors_full.sm", "r")
    note_data = parse_sm_file(sm_file.read().splitlines())
    print(f"Note Data: {note_data}")
    #end_time = time.time()
    #print(end_time - start_time)

if __name__ == "__main__":
    main()
