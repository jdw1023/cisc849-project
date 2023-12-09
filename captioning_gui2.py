# Final Project for Accessible Computing
# Authors: JD Wang and Manjusree
# Code based on the example code from the Whisper Python API and whisper_streaming 
# uses library from https://github.com/ufal/whisper_streaming/blob/master/whisper_online.py



from whisper_online import * # speech to text
import pyaudio # microphone input
import webrtcvad # voice activity detection
import numpy as np
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QTextEdit


class AudioRecorder(QObject):
    transcription_ready = Signal(str)

    def __init__(self):
        super().__init__()
        self.chunk = 480
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.vad = webrtcvad.Vad(2)
        self.p = pyaudio.PyAudio()
        self.src_lan = "en"
        self.tgt_lan = "en"
        self.tokenizer = create_tokenizer(self.tgt_lan)
        self.asr = FasterWhisperASR(self.src_lan, "large-v2")
        self.online = OnlineASRProcessor(self.asr, self.tokenizer)
        self.processed = False
        self.asr.use_vad()
        self.stream = self.p.open(format=self.format,
                    channels=self.channels,
                    rate=self.rate,
                    input=True,
                    frames_per_buffer=self.chunk,
                    stream_callback=self.callback)

    # def start_recording(self):
    #     try:
    #         print("Recording...")
    #         while True:
    #             data = np.frombuffer(self.stream.read(self.chunk), dtype=np.int16)
    #             if self.vad.is_speech(data, sample_rate=self.rate):
    #                 self.online.insert_audio_chunk(data)
    #                 # o = online.process_iter()
    #                 self.processed = False
    #             elif self.processed == False:
    #                 o = self.online.process_iter()
    #                 self.processed = True
    #                 print(o)
    #                 self.gui_callback(o)
      
    #     except Exception as e:
    #         print("Recording stopped.")
    #         print(e)
    #     finally:
    #         self.stream.stop_stream()
    #         self.stream.close()
    #         self.p.terminate()

    def start_recording(self):
        self.stream.start_stream()
            
    def callback(self, in_data, frame_count, time_info, status):
        audio_chunk = np.frombuffer(in_data, dtype=np.int16)
        if self.vad.is_speech(audio_chunk.tobytes(), sample_rate=self.rate):
            self.online.insert_audio_chunk(audio_chunk)
            # o = online.process_iter()
            self.processed = False
        elif self.processed == False:
            o = self.online.process_iter()
            self.processed = True
            # print("DATA!!:",o)
            if o[2] != "":
                # self.gui_callback(o[2])
                self.transcription_ready.emit(o[2])
        return in_data, pyaudio.paContinue

# Start streaming audio input from the microphone



class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Transcription Results:")
        self.text_edit = QTextEdit()
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_edit)

        self.recorder = AudioRecorder()
        self.recorder.transcription_ready.connect(self.update_transcription)

        # Create a separate thread for recording to avoid blocking the GUI
        import threading
        self.recording_thread = threading.Thread(target=self.recorder.start_recording)

    def start_recording(self):
        self.recording_thread.start()

    def update_transcription(self, transcription):
        # Update the GUI with the received transcription
        current_text = self.text_edit.toPlainText()
        self.text_edit.setPlainText(current_text + "\n" + transcription)

    def closeEvent(self, event):
        # Stop the recording thread when the GUI is closed
        self.recording_thread.join()
        event.accept()

def main():
    app = QApplication(sys.argv)
    window = TranscriptionApp()
    window.setWindowTitle("Real-time Transcription App")
    window.setGeometry(100, 100, 400, 200)

    window.show()

    # Start recording when the GUI is ready
    # window.start_recording()
    

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
