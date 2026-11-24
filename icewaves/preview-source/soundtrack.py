"""Original 120 BPM soundtrack + synthesized foley for the ICEWAVES preview.
usage: python3 soundtrack.py out.wav
"""
import sys
import numpy as np
from scipy.signal import butter, sosfilt
from scipy.io import wavfile

SR = 44100
DUR = 23.5
N = int(SR * DUR)
rng = np.random.default_rng(2026)
L = np.zeros(N); R = np.zeros(N)
BEAT = 0.5


def filt(x, kind, f):
    sos = butter(2, f, btype=kind, fs=SR, output='sos')
    return sosfilt(sos, x)


def add(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[: max(0, N - i)] * gain
    lg = np.cos((pan + 1) * np.pi / 4); rg = np.sin((pan + 1) * np.pi / 4)
    L[i:i + len(s)] += s * lg * 1.414
    R[i:i + len(s)] += s * rg * 1.414


def tt(d):
    return np.arange(int(d * SR)) / SR


def noise(d):
    return rng.standard_normal(int(d * SR))


# ---------- drums ----------
def kick():
    t = tt(0.35)
    f = 48 + 120 * np.exp(-t * 32)
    ph = 2 * np.pi * np.cumsum(f) / SR
    return np.sin(ph) * np.exp(-t * 8) + 0.3 * np.sin(ph * 2) * np.exp(-t * 20)


def clap():
    out = np.zeros(int(0.25 * SR))
    for k, off in enumerate([0, 0.011, 0.023]):
        n = filt(noise(0.2), 'bandpass', [900, 3200]) * np.exp(-tt(0.2) * (40 if k < 2 else 16))
        i = int(off * SR); out[i:i + len(n)] += n[: len(out) - i]
    return out * 0.5


def hat(open_=False):
    d = 0.18 if open_ else 0.05
    return filt(noise(d), 'highpass', 7000) * np.exp(-tt(d) * (18 if open_ else 70)) * 0.35


def crash():
    d = 1.6
    return filt(noise(d), 'highpass', 4500) * np.exp(-tt(d) * 2.6) * 0.32


# ---------- tonal ----------
def mtof(m):
    return 440.0 * 2 ** ((m - 69) / 12)


CHORDS = [  # F, C/E, Dm, Bb  (midi)
    ([65, 69, 72], 41), ([64, 67, 72], 48), ([62, 65, 69], 50), ([62, 65, 70], 46)]


def pluck(freq, d=0.35, bright=6):
    t = tt(d)
    s = sum(np.sin(2 * np.pi * freq * k * t) / k ** 1.3 for k in range(1, bright + 1))
    return s * np.exp(-t * 9) * np.minimum(1, t / 0.004)


def bass(freq, d=0.24):
    t = tt(d)
    s = np.sin(2 * np.pi * freq * t) + 0.45 * np.sin(2 * np.pi * freq * 2 * t) + 0.2 * np.sin(2 * np.pi * freq * 3 * t)
    return s * np.exp(-t * 5) * np.minimum(1, t / 0.006)


def mallet(freq, d=0.6):
    t = tt(d)
    s = np.sin(2 * np.pi * freq * t) + 0.25 * np.sin(2 * np.pi * freq * 4 * t) * np.exp(-t * 30)
    return s * np.exp(-t * 6) * np.minimum(1, t / 0.002)


def pad(notes, d):
    t = tt(d)
    s = np.zeros(len(t))
    for m in notes:
        f = mtof(m - 12)
        for det in (-0.12, 0.12):
            s += np.sin(2 * np.pi * f * (1 + det / 100) * t) + 0.3 * np.sin(2 * np.pi * 2 * f * t)
    return filt(s, 'lowpass', 1800)


MUSIC_START, MUSIC_END = 1.5, 23.0
music_L = np.zeros(N); music_R = np.zeros(N)


def madd(sig, t0, gain=1.0, pan=0.0):
    i = int(t0 * SR)
    if i >= N:
        return
    s = sig[: max(0, N - i)] * gain
    lg = np.cos((pan + 1) * np.pi / 4); rg = np.sin((pan + 1) * np.pi / 4)
    music_L[i:i + len(s)] += s * lg * 1.414
    music_R[i:i + len(s)] += s * rg * 1.414


# intro: pad swell + riser
p = pad(CHORDS[0][0], 1.6) * np.linspace(0, 1, int(1.6 * SR)) ** 2
madd(p, 0.0, 0.10)
riser = filt(noise(1.5), 'bandpass', [1500, 6000]) * np.linspace(0, 1, int(1.5 * SR)) ** 3
madd(riser, 0.0, 0.12)

beats = np.arange(0, MUSIC_END, BEAT)
for b in beats:
    if b < MUSIC_START:
        continue
    bar = int(b // 2)
    pos = int(round((b % 2) / BEAT))  # 0..3
    chord, root = CHORDS[bar % 4]
    madd(kick(), b, 0.9)
    if pos in (1, 3):
        madd(clap(), b, 0.55, 0.05)
    madd(hat(), b + BEAT / 2, 0.55, 0.25)
    # bass: 8ths
    for e in (0, 0.25):
        madd(bass(mtof(root)), b + e, 0.32 if e == 0 else 0.22)
    # chord plucks on the off-beat
    for m in chord:
        madd(pluck(mtof(m)), b + BEAT / 2, 0.06, -0.3 + 0.3 * chord.index(m))
    # mallet arpeggio, 16ths up the chord
    arp = chord + [chord[0] + 12]
    for k in range(2):
        m = arp[(pos * 2 + k) % 4] + 12
        madd(mallet(mtof(m)), b + k * 0.25, 0.05, 0.35)

for c in (1.5, 11.0, 18.5):
    madd(crash(), c, 0.6, -0.2)

# sidechain pump on music (everything except kick is already summed; gentle duck)
tm = np.arange(N) / SR
since = np.mod(tm - MUSIC_START, BEAT)
pump = 1 - 0.35 * np.exp(-since * 14)
pump[tm < MUSIC_START] = 1
# duck music under hero foley moments
duck = np.ones(N)
for a, b in [(3.5, 5.0), (5.0, 7.0), (13.0, 14.5)]:
    duck[(tm >= a) & (tm < b)] = 0.6
duck = np.convolve(duck, np.ones(2000) / 2000, mode='same')
music_L *= pump * duck; music_R *= pump * duck
cut = tm >= MUSIC_END
music_L[cut] *= np.exp(-(tm[cut] - MUSIC_END) * 40); music_R[cut] *= np.exp(-(tm[cut] - MUSIC_END) * 40)
L += music_L; R += music_R


# ---------- foley ----------
def whoosh(d=0.9):
    n = noise(d)
    lo = filt(n, 'bandpass', [250, 1200]); hi = filt(n, 'bandpass', [1500, 6000])
    x = np.linspace(0, 1, len(n))
    env = np.exp(-((x - 0.5) ** 2) / 0.03)
    return (lo * (1 - x) + hi * x) * env


def add_whoosh(center, d=0.9, gain=0.5):
    w = whoosh(d)
    t0 = center - d / 2
    i = int(t0 * SR)
    pan = np.linspace(-0.9, 0.9, len(w))  # wave travels left to right
    lg = np.cos((pan + 1) * np.pi / 4); rg = np.sin((pan + 1) * np.pi / 4)
    j = min(N, i + len(w)); w = w[: j - i]
    L[i:j] += w * lg[: j - i] * gain * 1.414
    R[i:j] += w * rg[: j - i] * gain * 1.414


for c in (1.0, 11.0, 18.5, 23.0):
    add_whoosh(c, 1.0 if c in (1.0, 23.0) else 0.6, 0.55)


def blender(d):
    t = tt(d)
    whine = sum(np.sin(2 * np.pi * (210 * k) * t + 0.6 * np.sin(2 * np.pi * 5 * t)) / k for k in range(1, 6))
    rum = filt(noise(d), 'lowpass', 1400) * (1 + 0.4 * np.sin(2 * np.pi * 31 * t))
    env = np.minimum(1, t / 0.08) * np.minimum(1, (d - t) / 0.12)
    return (0.25 * whine + 1.2 * rum) * env


def pour(d):
    b = np.cumsum(noise(d)); b -= np.convolve(b, np.ones(800) / 800, mode='same')
    b = filt(b, 'bandpass', [150, 1100]); b /= np.max(np.abs(b)) + 1e-9
    t = tt(d)
    gl = np.zeros(len(t))
    for _ in range(int(d * 22)):
        i = rng.integers(0, len(t) - 2000); f = rng.uniform(300, 900)
        g = np.sin(2 * np.pi * f * (1 + np.linspace(0, 0.6, 1500)) * tt(1500 / SR)) * np.exp(-tt(1500 / SR) * 60)
        gl[i:i + 1500] += g * rng.uniform(0.2, 0.6)
    env = np.minimum(1, t / 0.05) * np.minimum(1, (d - t) / 0.2)
    return (0.8 * b + 0.5 * gl) * env


def crunch(d, n=26):
    out = np.zeros(int(d * SR))
    for _ in range(n):
        ld = rng.uniform(0.006, 0.03)
        g = filt(noise(ld), 'highpass', 1600) * np.exp(-tt(ld) * 120)
        i = rng.integers(0, len(out) - len(g))
        out[i:i + len(g)] += g * rng.uniform(0.3, 1.0)
    return out


def tap():
    t = tt(0.6)
    return (np.sin(2 * np.pi * 2650 * t) + 0.5 * np.sin(2 * np.pi * 3970 * t) + 0.25 * np.sin(2 * np.pi * 5600 * t)) * np.exp(-t * 14) * 0.5


def squeeze(d):
    t = tt(d)
    return filt(noise(d), 'bandpass', [200, 700]) * (0.5 + 0.5 * np.sin(2 * np.pi * 7 * t)) * np.minimum(1, (d - t) / 0.1) * 0.5


def sparkle():
    out = np.zeros(int(0.8 * SR))
    for k, m in enumerate([84, 88, 91, 96]):
        s = mallet(mtof(m), 0.6)
        i = int(k * 0.05 * SR); out[i:i + len(s)] += s[: len(out) - i]
    return out


add(blender(1.5), 3.5, 0.35)
add(pour(2.0), 5.0, 0.45, -0.1)
add(crunch(1.6), 7.2, 0.45, 0.1)
add(tap(), 9.0, 0.35, 0.15)
add(squeeze(1.6), 11.2, 0.4)
add(pour(1.5), 13.0, 0.45, -0.1)
add(crunch(1.6, 30), 14.6, 0.45, 0.1)
add(tap(), 16.5, 0.35, 0.15)
add(sparkle(), 1.5, 0.18, 0.3)
add(sparkle(), 18.75, 0.18, -0.3)

mix = np.stack([L, R], axis=1)
mix = np.tanh(mix * 1.1)
mix /= np.max(np.abs(mix)) / 0.89
wavfile.write(sys.argv[1], SR, (mix * 32767).astype(np.int16))
print('ok', mix.shape)
