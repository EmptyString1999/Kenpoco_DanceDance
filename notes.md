# notes ctypes

## Structs
``` c
struct foo {
  int* foo;
  float baz;
  char* name;
};
```

``` python
class foo(Structure):
  _fields_ = [("foo", c_int),
              ("baz", )]
```

WavAudioInfo(
wav_file=<_io.BufferedReader name='src/DanceDance/7_Colors_10second.wav'>,
num_channels=2,
sam
ple_rate=31999,
bits_per_sample=16,
byte_rate=127996,
block_align=4,
audio_format=1,
samples_total=0,
data_
start=78,
data_size=1286144,
current_pos=78
)


# Meeting notes:


