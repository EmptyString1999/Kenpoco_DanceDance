from sys import path as syspath
syspath.append("/Games/DanceDance") #fix imports

import thumby
from os import listdir #os.path.isfile doesn't exist in micropython
import time
import gc

import audio_wav as audio
import sm_parser as sm_parser

DIFFICULTY       = const("Beginner")
NOTE_DROP_TIME   = const(0.9) #const(2.0)
HIT_THRESHOLD    = const(0.18)
MARVELOUS_THRESH = const(16.67) # ms
PERFECT_THRESH   = const(33.33) # ms
GREAT_THRESH     = const(83.33) # ms
GOOD_THRESH      = const(123.33)# ms
BAD_THRESH       = const(163.33)# ms

# BITMAP: width: 48, height: 31
bars = bytearray([255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,
           255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,
           255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,0,0,0,0,255,0,0,0,0,0,0,0,255,
           31,32,64,64,64,64,64,32,31,0,0,0,0,31,32,64,64,64,64,64,32,31,0,0,0,0,31,32,64,64,64,64,64,32,31,0,0,0,0,31,32,64,64,64,64,64,32,31])

# BITMAP: width: 7, height: 7
arrow_vert_empty = bytearray([8,116,66,65,66,116,8])
arrow_vert_full  = bytearray([8,124,126,127,126,124,8])
arrow_hori_empty = bytearray([8,20,34,65,34,34,62])
arrow_hori_full  = bytearray([8,28,62,127,62,62,62])

# BITMAP: width: 5, height: 5
single_note = bytearray([14,17,21,17,14])

# Sprites
bars_sprite        = thumby.Sprite(48, 31, bars, 20, 0)

arrow_left_sprite  = thumby.Sprite(7, 7, arrow_hori_empty+arrow_hori_full, 20, 32)
arrow_down_sprite  = thumby.Sprite(7, 7, arrow_vert_empty+arrow_vert_full, 34, 32, mirrorY=1)
arrow_up_sprite    = thumby.Sprite(7, 7, arrow_vert_empty+arrow_vert_full, 47, 32)
arrow_right_sprite = thumby.Sprite(7, 7, arrow_hori_empty+arrow_hori_full, 60, 32, mirrorX=1)

single_note_sprite = thumby.Sprite(5, 5, single_note)

# Lane Buffers
note_bufsize = 30
left_buffer  = bytearray(note_bufsize)
down_buffer  = bytearray(note_bufsize)
up_buffer    = bytearray(note_bufsize)
right_buffer = bytearray(note_bufsize)

# DPAD Input State
left_held = False
down_held = False
up_held = False
right_held = False

# Thumby Display Config
thumby.DISPLAY_W = 72
thumby.DISPLAY_H = 40
thumby.display.setFPS(30)

# Audio Initalisation
audio_time = 0
audio_file_exists = True
sm_file_exists = True

#TODO: put song select here
song    = "7colors_8bit.wav"
song_sm = "7_colors.sm"
if not song in listdir("/Games/DanceDance"): audio_file_exists = False
if not song_sm in listdir("/Games/DanceDance"): sm_file_exists = False

# Note data stored as a Dict of Strings and floating point values: e.g. 'Beginner' : [('1000', 23.26923076923077)]
note_data = {}

# a list of audio timestamps for when the player should press a key
upcoming_notes = []

player_score = 0

running     = True
frame_count = 0
start_ticks = 0

def get_current_time():
    """
    Returns the difference between the current thread ticks and
    the threads starting time in ticks divided by 1,000,000 and rounded to 2dp
    """
    global start_ticks
    current_ticks = time.ticks_us()
    current_tick_diff = time.ticks_diff(current_ticks, start_ticks)
    return round(float(current_tick_diff / 100_000_0), 1)

def check_input_hit(time_note_tuple, direction_int):
    """
    checks if given a time note tuple and a direction pressed if a score should be given 
    PARAMS:
    time_note_tuple : tuple(float, string) | e.g. (32.18292839, '1001')
    direction_int   : int                  | L=0, D=1, U=2, R=3, 
    """
    global start_ticks, player_score, upcoming_notes
    current_time = get_current_time()
    diff = abs(time_note_tuple[0] - current_time)
    print("current_time: " + str(current_time) + " | upcoming_time: " + str(time_note_tuple[0]) + " | note: " + str(time_note_tuple[1]) + " | diff: " + str(diff))
    time_note_string = time_note_tuple[1]
    if diff <= MARVELOUS_THRESH / 1000 and time_note_string[direction_int] != '0':
        upcoming_notes.pop(0)
        player_score += 100
        print("Marvelous hit | 100 points")
    elif diff <= PERFECT_THRESH / 1000 and time_note_string[direction_int] != '0': 
        upcoming_notes.pop(0)
        player_score += 80
        print("Perfect hit | 80 points")
    elif diff <= GREAT_THRESH / 1000 and time_note_string[direction_int] != '0': 
        upcoming_notes.pop(0)
        player_score += 50
        print("Great hit | 50 points")
    elif diff <= GOOD_THRESH / 1000 and time_note_string[direction_int] != '0': 
        upcoming_notes.pop(0)
        player_score += 20
        print("Good hit | 20 points")
    elif diff <= BAD_THRESH / 1000 and  time_note_string[direction_int] != '0': 
        upcoming_notes.pop(0)
        player_score += 10
        print("Bad hit | 10 points")

print(f"sm_file_exists: {sm_file_exists}")
if sm_file_exists:
    sm_file = open("/Games/DanceDance/" + song_sm, "r")
    sm_text = sm_file.read()
    sm_file.close()
    sm_lines = sm_text.splitlines()
    note_data = sm_parser.parse_sm_file(sm_lines)
    del sm_text
    del sm_lines


if audio_file_exists:
    audio_bytes = open("/Games/DanceDance/" + song, "rb")
    audio.load(audio_bytes)
    audio.play()

start_ticks = time.ticks_us()

while(running):
    # ================
    # Input
    # ================
    if thumby.buttonL.pressed():
        arrow_left_sprite.setFrame(1)
        if len(upcoming_notes) > 0:
            check_input_hit(upcoming_notes[0], 0)
    else:
        arrow_left_sprite.setFrame(0)

    if thumby.buttonD.pressed():
        arrow_down_sprite.setFrame(1)
        if len(upcoming_notes) > 0:
            check_input_hit(upcoming_notes[0], 1)
    else:
        arrow_down_sprite.setFrame(0)

    if thumby.buttonU.pressed():
        arrow_up_sprite.setFrame(1)
        if len(upcoming_notes) > 0:
            check_input_hit(upcoming_notes[0], 2)
    else:
        arrow_up_sprite.setFrame(0)

    if thumby.buttonR.pressed():
        arrow_right_sprite.setFrame(1)
        if len(upcoming_notes) > 0:
            check_input_hit(upcoming_notes[0], 3)
    else:
        arrow_right_sprite.setFrame(0)

    # ================
    # Update logic
    # ================
    audio.fillbufs()

    # Shift the note by one every frame
    left_buffer  = left_buffer[-1:]  + left_buffer[:-1]
    down_buffer  = down_buffer[-1:]  + down_buffer[:-1]
    up_buffer    = up_buffer[-1:]    + up_buffer[:-1]
    right_buffer = right_buffer[-1:] + right_buffer[:-1]
    # set the previous position to 0 to prevent duplication
    left_buffer[0]  = 0
    down_buffer[0]  = 0
    up_buffer[0]    = 0
    right_buffer[0] = 0

    # Get the audio runtime and convert it to a time stamp with 2dp (e.g. 2.25)
    runtime_us = audio.get_runtime()
    audio_runtime = round(float(runtime_us / 100_000_0), 1)
    if audio.playing == False:
        running = False

    # TODO: update comments
    # If the audio_runtime + 0.9 seconds is the next note,
    # remove the note from the list and unwrap it into the respective buffers
    print(f"audio_runtime = {audio_runtime}")
    frame_time = get_current_time()
    print(f"frame_time = {frame_time}")
    if len(note_data[DIFFICULTY]) > 0 and (audio_runtime + NOTE_DROP_TIME) == round(note_data[DIFFICULTY][0][1]):
        note_str, note_time = note_data[DIFFICULTY].pop(0)
        upcoming_notes.append((note_time, note_str))
        left_buffer[0]  = int(note_str[0])
        down_buffer[0]  = int(note_str[1])
        up_buffer[0]    = int(note_str[2])
        right_buffer[0] = int(note_str[3])

    if len(upcoming_notes) > 0:
        frame_time = get_current_time()
        print(str(frame_time) + " | " + str(upcoming_notes[0][0]))
        if frame_time > upcoming_notes[0][0] + BAD_THRESH/1000:
            upcoming_notes.pop(0)

    # ================
    # Draw
    # ================
    thumby.display.fill(0)
    thumby.display.drawText(str(player_score), 0, 0, 1)
    thumby.display.drawSprite(bars_sprite)
    thumby.display.drawSprite(arrow_left_sprite)
    thumby.display.drawSprite(arrow_down_sprite)
    thumby.display.drawSprite(arrow_up_sprite)
    thumby.display.drawSprite(arrow_right_sprite)

    for i, buf in enumerate((left_buffer, down_buffer, up_buffer, right_buffer)):
        for pos, note in enumerate(buf):
            if note == 1:
                single_note_sprite.x = 22 + (i * 13)
                single_note_sprite.y = pos
                thumby.display.drawSprite(single_note_sprite)

    thumby.display.update()
    frame_count += 1
