import struct
import thumby
import time
import _thread
from micropython import const

DEBUG = False


bufsize = 800 #enough for 6 frames at 30 FPS
buf1 = bytearray(bufsize)
buf2 = bytearray(bufsize)
data = None
playing = False
data_start = 0
data_size = 0
data_pos = 0

#current buffer, pos in buffer, bufsize, current sample, total samples, buf1NeedsFilling, buf2NeedsFilling, startTime, runtime
bufstate = bytearray(struct.pack("<IIIIIIIII", 0, 0, bufsize, 0, 0, 1, 1, 0, 0))
# TODO: check if these are optimised out
_CURRENT_BUFFER = const(0)
_POS_IN_BUFFER = const(1)
_BUFSIZE = const(2)
_CURRENT_SAMPLE = const(3)
_TOTAL_SAMPLES = const(4)
_BUF1_NEEDS_FILLING = const(5)
_BUF2_NEEDS_FILLING = const(6)
_START_TIME = const(7)
_RUNTIME = const(8)

def parse_wav_header(wav_file):
    """
    takes in a wav file and uses it to fill out wav_audio_info.
    wav_file must be an already-open binary file object.
    Example:
        f = open("/Games/DanceDance/song.wav", "rb")
        parse_wav_header(f)
    """
    global data_size, data_start
    wav_file.seek(0)
    riff_header = wav_file.read(12)
    riff_id, riff_size, wave_id = struct.unpack("<4sI4s", riff_header)

    current_pos = 12

    data_found = False
    while True:
        wav_file.seek(current_pos)

        chunk_header = wav_file.read(8)
        if len(chunk_header) < 8:
            # end of file
            break

        chunk_id, chunk_size = struct.unpack("<4sI", chunk_header)

        if chunk_id == b'fmt ':
            wav_file.seek(current_pos + 8) # skip chunk header
            fmt_data = wav_file.read(chunk_size)
            fmt_info = struct.unpack("<HHIIHH", fmt_data)
            audio_format, num_channels, sample_rate, byte_rate, block_align, bits_per_sample = fmt_info

        if chunk_id == b'data':
            #print(f"chunk_id: {chunk_id} chunk_size: {chunk_size}")
            data_start_pos = current_pos + 8
            data_size = chunk_size
            data_start = data_start_pos
            
        # move to the next chunk
        current_pos += 8 + chunk_size
        data_pos = current_pos

        # Handle odd-sized chunks (WAV spec requires word alignment)
        if chunk_size % 2 == 1:
            current_pos += 1

@micropython.viper
def copyfrom(b1, b2): #copy b1 to b2
    """
    Source: https://github.com/transistortester/thumby-bad-apple/blob/main/thumby/BadApple/audio.py
    """
    i:int = 0
    p1:ptr8 = ptr8(b1)
    p2:ptr8 = ptr8(b2)
    for i in range(int(len(b2))):
        p2[i] = p1[i]

def fillbufs():
    global bufstate, data_pos, data_sizes
    data_end = data_start + data_size
    if bufstate[20]: #NOTE: bufstate 20 = buf1NeedsFilling
        if data_pos < data_end:
            data.seek(data_pos)
            buffer_data = data.read(800)
            data_pos += 800
            copyfrom(buffer_data, buf1) #NOTE: copy the data to our buffer
        bufstate[20] = 0
        #print(f"buf1 filled: {buf1}")
    if bufstate[24]: #NOTE: bufstate 24 = buf2NeedsFilling
        if data_pos < data_end:
            data.seek(data_pos)
            buffer_data = data.read(800)
            data_pos += 800
            copyfrom(buffer_data, buf2)
        bufstate[24] = 0
        #print(f"buf2 filled {buf2}")

# CREDIT: Mark Batty
@micropython.viper
def audioloop(callback):
    from machine import PWM, Pin
    swBuzzer = PWM(Pin(28))
    swBuzzer.freq(100000)
    setwidth = swBuzzer.duty_u16 #redefining these rather than using thumby.audio reduces clicking
    curtime = time.ticks_us
    state:ptr32 = ptr32(bufstate)
    b1:ptr8 = ptr8(buf1)
    b2:ptr8 = ptr8(buf2)
    delay:int = 1000000//8000
    state[_START_TIME] = int(curtime())
    state[_RUNTIME] = int(curtime()) + delay
    sample:int = 128

    while state[_CURRENT_SAMPLE] < state[_TOTAL_SAMPLES]: #still playing
        if not state[_CURRENT_BUFFER]: #first buffer
            sample = 0b11111111 & b1[state[_POS_IN_BUFFER]]
        else: # second buffer
            sample = 0b11111111 & b2[state[_POS_IN_BUFFER]]
        state[_CURRENT_SAMPLE] += 1
        state[_POS_IN_BUFFER] += 1
        if state[_POS_IN_BUFFER] >= state[_BUFSIZE]: #end of buffer
            state[_BUF1_NEEDS_FILLING+state[_CURRENT_BUFFER]] = 1 #set flag
            state[_CURRENT_BUFFER] ^= 1 #swap buffers
            state[_POS_IN_BUFFER] = 0
        while int(curtime()) < state[_RUNTIME]: pass
        setwidth(sample << 8)
        state[_RUNTIME] += delay

    print("Thread ended")
    stop()

def get_runtime():
    global bufstate
    _, _, _, _, _, _, _, thread_start_time, thread_runtime, = struct.unpack("<IIIIIIIII", bufstate)
    runtime = thread_runtime - thread_start_time
    return runtime
    
#TODO: probably needs changing is from BadApple github
def play(callback):
    global playing
    playing = True
    print("playing...")
    #thumby.audio.set(80000)
    _thread.start_new_thread(audioloop, (callback, ))

#TODO: remove this its code from BadApple github
def stop():
    global playing
    playing = False
    bufstate[12] = bufstate[16] #set current sample to limit
    bufstate[13] = bufstate[17]
    bufstate[14] = bufstate[18]
    bufstate[15] = bufstate[19] #most significant last in case it's clobbered - should really acquire a lock for this
    #time.sleep_ms(500)
    thumby.audio.set(1000) #make audible to tell if it fails to stop correctly
    thumby.audio.stop()

def load(wav_file):
    """
    - read the wav file header to get the Audio Format, Channels, Byte Rate, Block Align, Bits Per Sample
    - we then know where the audio data starts (after 78 bytes in the example)
    - 
    """
    global data, buf1, buf2, bufstate, data_pos, data_start

    wav_header = wav_file.read(78)
    #print(type(wav_file))
    parse_wav_header(wav_file)
    wav_file.seek(data_start)
    data = wav_file

    buf1 = bytearray(bufsize)
    buf2 = bytearray(bufsize)
    #print(data_size)
    data_pos = data_start
    bufstate = bytearray(struct.pack("<IIIIIIIII", 0, 0, bufsize, 0, data_size, 1, 1, 0, 0))
    fillbufs()
