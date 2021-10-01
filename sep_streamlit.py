import os
import argparse
import time
import librosa
import soundfile
import streamlit as st
from io import BytesIO

from bytesep.inference import SeparatorWrapper


# separator
separator = SeparatorWrapper(
    source_type='vocals',
    model=None,
    checkpoint_path=None,
    device='cuda',
)


sample_rate = 44100  # Must be 44100 when using the downloaded checkpoints.


st.write('Wav player')


w = st.file_uploader('Upload a wav file', type='wav')


if w:
    t1 = time.time()
    
    # Load audio.
    audio, _ = librosa.load(w, sr=sample_rate, mono=False)

    # Separate.
    sep_wav = separator.separate(audio)

    sep_time = time.time() - t1

    # Write out audio
    buffer = BytesIO()

    with BytesIO() as buffer:
        soundfile.write(buffer, sep_wav.T, samplerate=sample_rate, format='WAV')
        st.write("Time: {:.3f}".format(sep_time))
        st.audio(buffer.getvalue(), format='audio/wav')