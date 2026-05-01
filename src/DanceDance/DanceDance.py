from sys import path as syspath
syspath.append("/Games/DanceDance") #fix imports

import thumby
from os import listdir #os.path.isfile doesn't exist in micropython
import time

import audio_wav as audio
import sm_parser as sm_parser

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
arrow_up_sprite    = thumby.Sprite(7, 7, arrow_vert_empty+arrow_vert_full, 34, 32)
arrow_down_sprite  = thumby.Sprite(7, 7, arrow_vert_empty+arrow_vert_full, 60, 32, mirrorY=1)
arrow_left_sprite  = thumby.Sprite(7, 7, arrow_hori_empty+arrow_hori_full, 20, 32)
arrow_right_sprite = thumby.Sprite(7, 7, arrow_hori_empty+arrow_hori_full, 47, 32, mirrorX=1)
single_note_sprite = thumby.Sprite(5, 5, single_note)

"""
34
\/
|    |  |    |  |    |  |    |
|    |  |    |  |    |  |    |
|    |  |    |  |    |  |    |
|    |  |    |  |    |  |    |
|    |  |    |  |    |  |    |
|----|  |----|  |----|  |----|

left_buffer  = 34 + 2 + 00 = 36
down_buffer  = 34 + 2 + 11 = 47
up_buffer    = 34 + 2 + 22 = 58 
right_buffer = 34 + 2 + 33 = 69
"""

note_bufsize = 30
left_buffer  = bytearray(note_bufsize)
down_buffer  = bytearray(note_bufsize)
up_buffer    = bytearray(note_bufsize)
right_buffer = bytearray(note_bufsize)

# Thumby Display Config
thumby.DISPLAY_W = 72
thumby.DISPLAY_H = 40
thumby.display.setFPS(30)

# Audio Initalisation
audio_time = 0
audio_file_exists = True
sm_file_exists = True
#TODO: put song select here
song = "7colors_8bit.wav"
if not song in listdir("/Games/DanceDance"): audio_file_exists = False
song_sm= "7_colors.sm"
if not song_sm in listdir("/Games/DanceDance"): sm_file_exists = False

# Note data stored as '1000 9.230769230769232'
note_data = {}

# a list of audio timestamps for when the player should press a key
upcoming_notes = []

running = True
frame_count = 0
start_time = time.ticks_us()

def time_update_callback(time_step:float):
    global audio_time
    audio_time += time_step

print(f"sm_file_exists: {sm_file_exists}")
if sm_file_exists:
    sm_file = open("/Games/DanceDance/7_colors.sm", "r")
    sm_text = sm_file.read()
    sm_file.close()
    sm_lines = sm_text.splitlines()
    note_data = sm_parser.parse_sm_file(sm_lines)
    del sm_text
    del sm_lines


if audio_file_exists:
    audio_bytes = open("/Games/DanceDance/7colors_8bit.wav", "rb")
    audio.load(audio_bytes)
    audio.play(time_update_callback)

print(note_data)

while(running):
    #print(running)
    current_time = round(float(time.ticks_diff(time.ticks_us(), start_time) / 100_000_0), 1)
    print(current_time)
    print(upcoming_notes)
    # Input
    if thumby.buttonU.pressed():
        arrow_up_sprite.setFrame(1)
    else:
        arrow_up_sprite.setFrame(0)
    if thumby.buttonD.pressed():
        arrow_down_sprite.setFrame(1)
    else:
        arrow_down_sprite.setFrame(0)
    if thumby.buttonL.pressed():
        arrow_left_sprite.setFrame(1)
    else:
        arrow_left_sprite.setFrame(0)
    if thumby.buttonR.pressed():
        arrow_right_sprite.setFrame(1)
    else:
        arrow_right_sprite.setFrame(0)

    # Update logic
    frame = frame_count % 8
    audio.fillbufs()

    # Shift the note by one every frame
    left_buffer[1:]  = left_buffer[:-1]
    down_buffer[1:]  = down_buffer[:-1]
    up_buffer[1:]    = up_buffer[:-1]
    right_buffer[1:] = right_buffer[:-1]
    # set the previous position to 0 to prevent duplication
    left_buffer[0]  = 0
    down_buffer[0]  = 0
    up_buffer[0]    = 0
    right_buffer[0] = 0

    # Get the audio runtime and convert it to a time stamp with 2dp (e.g. 2.25)
    runtime_us = audio.get_runtime()
    audio_runtime = round(float(runtime_us / 100_000_0), 1)
 
    # print("=====================================")
    # print("Runtime: " + str(audio_runtime))
    # print("Note Time: " + str(note_data["Beginner"][0]))
    # print("Note Time + 2: " + str(note_data["Beginner"][0][1]))
 
    # If the audio_runtime plus 2 seconds is the next note segment remove the note 
    # segment from the list and unwrap it into the respective buffers
    if ((audio_runtime + 2) == round(note_data["Beginner"][0][1])):
        note_str, note_time = note_data["Beginner"].pop(0)
        upcoming_notes.append(note_time)
        left_buffer[0]  = int(note_str[0])
        down_buffer[0]  = int(note_str[1])
        up_buffer[0]    = int(note_str[2])
        right_buffer[0] = int(note_str[3])
        print(note_str)

    # Draw
    thumby.display.fill(0)
    thumby.display.drawSprite(bars_sprite)
    thumby.display.drawSprite(arrow_up_sprite)
    thumby.display.drawSprite(arrow_down_sprite)
    thumby.display.drawSprite(arrow_left_sprite)
    thumby.display.drawSprite(arrow_right_sprite)

    for i, buf in enumerate((left_buffer, down_buffer, up_buffer, right_buffer)):
        for pos, note in enumerate(buf):
            if note == 1:
                single_note_sprite.x = 22 + (i * 13)
                single_note_sprite.y = pos
                thumby.display.drawSprite(single_note_sprite)
    
    thumby.display.update()
    frame_count += 1
