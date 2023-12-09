# Final Project for Accessible Computing
# Authors: JD Wang and Manjusree
# Code based on the example code from the Whisper Python API and whisper_streaming 
# uses library from https://github.com/ufal/whisper_streaming/blob/master/whisper_online.py



from whisper_online import * # speech to text
import pyaudio # microphone input
import webrtcvad # voice activity detection
import numpy as np
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget



vad = webrtcvad.Vad()
vad.set_mode(1)




# Set the source and target language
src_lan = "en"
tgt_lan = "en"

# Initialize the ASR model
asr = FasterWhisperASR(src_lan, "large-v2")

# Set options (uncomment based on your needs)
# asr.set_translate_task()
asr.use_vad()

# Create a tokenizer for the target language
tokenizer = create_tokenizer(tgt_lan)

# Create an OnlineASRProcessor object
online = OnlineASRProcessor(asr, tokenizer)

processed = False

# Function to receive audio chunks from the microphone
def callback(in_data, frame_count, time_info, status):
	global processed
	audio_chunk = np.frombuffer(in_data, dtype=np.int16)
	if vad.is_speech(audio_chunk.tobytes(), sample_rate=rate):
		online.insert_audio_chunk(audio_chunk)
		# o = online.process_iter()
		processed = False
	elif processed == False:
		o = online.process_iter()
		processed = True
		print(o)
	return in_data, pyaudio.paContinue

# Set the microphone parameters
channels = 1  # mono audio
format = pyaudio.paInt16
rate = 16000  # adjust based on your microphone

# Initialize PyAudio
p = pyaudio.PyAudio()

# Open a stream for microphone input
stream = p.open(format=format,
				channels=channels,
				rate=rate,
				input=True,
				frames_per_buffer=480,
				stream_callback=callback)

# Start streaming audio input from the microphone
stream.start_stream()

print("Speaking into the microphone. Press Ctrl+C to stop.")

try:
	while stream.is_active():
		# You can add a sleep here if needed
		# time.sleep(min_chunk_size)

		# Wait for the user to press Ctrl+C to stop the loop
		pass
except KeyboardInterrupt:
	print("\nRecording stopped.")

# Stop and close the stream
stream.stop_stream()
stream.close()

# Finish processing the last audio chunk
output = online.finish()
print(output)

# Terminate PyAudio
p.terminate()


