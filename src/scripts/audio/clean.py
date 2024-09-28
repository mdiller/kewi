# cleans/filters the audio

# THIS DOESNT WORK, LOL

INPUT_FILE = "C:\\dev\\projects\\kewi\\src\\scripts\\audio\\_example.mp3"
OUT_FILE = "C:\\dev\\projects\\kewi\\src\\scripts\\audio\\_out.mp3"

import kewi
from pydub import AudioSegment
import numpy as np
import librosa
import scipy.io.wavfile as wav
import os
import subprocess

# Function to convert MP3 to WAV using ffmpeg subprocess
def mp3_to_wav(mp3_filename, wav_filename):
	# Use ffmpeg to convert MP3 to WAV
	command = ['ffmpeg', '-i', mp3_filename, wav_filename]
	try:
		subprocess.run(command, check=True)
	except subprocess.CalledProcessError as e:
		print(f"Error in ffmpeg conversion: {e}")
		raise

# Function to convert WAV to MP3 using pydub
def wav_to_mp3(wav_filename, mp3_filename):
	# Load the WAV file
	audio = AudioSegment.from_wav(wav_filename)

	# Export the audio to MP3 format
	audio.export(mp3_filename, format="mp3")

# Function to apply noise reduction
def reduce_noise(wav_input, wav_output, threshold_db=-40):
	# Load the audio signal
	sample_rate, data = wav.read(wav_input)

	# If stereo, convert to mono by averaging both channels
	if len(data.shape) == 2:
		data = data.mean(axis=1)

	# Perform Short-Time Fourier Transform (STFT)
	stft = librosa.stft(data.astype(float))

	# Convert amplitude to dB to find the threshold for noise
	magnitude_db = librosa.amplitude_to_db(np.abs(stft))

	# Noise gate: Set a threshold to reduce noise
	magnitude_db[magnitude_db < threshold_db] = threshold_db

	# Convert dB back to amplitude
	magnitude = librosa.db_to_amplitude(magnitude_db)

	# Reconstruct the audio signal
	denoised_signal = librosa.istft(magnitude)

	# Save the denoised audio as WAV
	wav.write(wav_output, sample_rate, denoised_signal.astype(np.int16))

# Main function to handle the full process
def process_mp3(input_mp3, output_mp3, threshold_db=-40):
	# Temporary filenames for WAV conversion
	wav_input = kewi.cache.new("temp:wavfile1", "wav")
	wav_output = kewi.cache.new("temp:wavfile2", "wav")

	# Step 1: Convert MP3 to WAV using ffmpeg
	mp3_to_wav(input_mp3, wav_input)

	# Step 2: Apply noise reduction
	reduce_noise(wav_input, wav_output, threshold_db)

	# Step 3: Convert the denoised WAV back to MP3
	wav_to_mp3(wav_output, output_mp3)


process_mp3(INPUT_FILE, OUT_FILE)

