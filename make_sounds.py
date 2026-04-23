import wave
import struct
import math

def save_wav(filename, samples, sample_rate=44100):
    with wave.open(filename, 'w') as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)

        frames = b''.join(
            struct.pack('<h', int(max(-1, min(1, s)) * 32767))
            for s in samples
        )
        wf.writeframes(frames)

# 🍎 EAT SOUND (short click)
sr = 44100
eat = []
for i in range(int(sr * 0.08)):
    t = i / sr
    s = math.sin(2 * math.pi * 1200 * t)
    env = (t / 0.005 if t < 0.005 else 1) * math.exp(-t * 25)
    eat.append(s * env * 0.5)

save_wav("eat.wav", eat)

# 💀 DIE SOUND (dramatic drop)
die = []
phase = 0
for i in range(int(sr * 0.7)):
    t = i / sr
    freq = 700 - 580 * (t / 0.7)
    phase += 2 * math.pi * freq / sr
    s = math.sin(phase)
    env = (t / 0.01 if t < 0.01 else 1) * math.exp(-t * 4)
    die.append(s * env * 0.6)

save_wav("die.wav", die)

print("✅ Sounds generated: eat.wav & die.wav")