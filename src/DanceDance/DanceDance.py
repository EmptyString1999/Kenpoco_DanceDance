from sys import path as syspath
syspath.append("/Games/DanceDance") #fix imports

import thumby
from os import listdir #os.path.isfile doesn't exist in micropython

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

# Sprites
bars_sprite        = thumby.Sprite(48, 31, bars, 20, 0)
arrow_up_sprite    = thumby.Sprite(7, 7, arrow_vert_empty+arrow_vert_full, 34, 32)
arrow_down_sprite  = thumby.Sprite(7, 7, arrow_vert_empty+arrow_vert_full, 60, 32, mirrorY=1)
arrow_left_sprite  = thumby.Sprite(7, 7, arrow_hori_empty+arrow_hori_full, 20, 32)
arrow_right_sprite = thumby.Sprite(7, 7, arrow_hori_empty+arrow_hori_full, 47, 32, mirrorX=1)

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

running = True
frame_count = 0

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
    runtime_us = audio.get_runtime()
    runtime = float(runtime_us / 100_000_0)
    print("Runtime" + str(runtime))

    # Draw
    thumby.display.fill(0)
    thumby.display.drawSprite(bars_sprite)
    thumby.display.drawSprite(arrow_up_sprite)
    thumby.display.drawSprite(arrow_down_sprite)
    thumby.display.drawSprite(arrow_left_sprite)
    thumby.display.drawSprite(arrow_right_sprite)
    
    
    thumby.display.update()
    frame_count += 1
