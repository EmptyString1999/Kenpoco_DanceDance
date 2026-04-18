from sys import path as syspath
syspath.append("/Games/DanceDance") #fix imports

import thumby
from os import listdir #os.path.isfile doesn't exist in micropython

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

thumby.DISPLAY_W = 72
thumby.DISPLAY_H = 40

thumby.display.setFPS(30)
has_audio = True
if not "7colors_8bit.wav" in listdir("/Games/DanceDance"): playaudio = False

#NOTE: in future put song select here
if has_audio:
    import audio_wav as audio
    audio_bytes = open("/Games/DanceDance/7colors_8bit.wav", "rb")
    audio.load(audio_bytes)
    audio.play()

running = True
frame_count = 0
while(running):
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

    # Draw
    thumby.display.fill(0)
    thumby.display.drawSprite(bars_sprite)
    thumby.display.drawSprite(arrow_up_sprite)
    thumby.display.drawSprite(arrow_down_sprite)
    thumby.display.drawSprite(arrow_left_sprite)
    thumby.display.drawSprite(arrow_right_sprite)
    
    
    thumby.display.update()
    frame_count += 1
