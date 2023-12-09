import sys
import time
import pyaudio
import socket
import select
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget

# Set your server host and port
SERVER_HOST = "localhost"
SERVER_PORT = 43007

class AudioRecorder:
    def __init__(self, gui_callback):
        self.chunk = 1024
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.p = pyaudio.PyAudio()
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.chunk)
        self.gui_callback = gui_callback

    def start_recording(self):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            s.connect((SERVER_HOST, SERVER_PORT))
            s.setblocking(False)
            try:
                print("Recording...")
                while True:
                    data = self.stream.read(self.chunk)
                    s.sendall(data)
                    
                    # Receive transcription from the server
                    ready = select.select([s], [], [], 0.1)
                    # print(ready)
                    if ready[0]:
                        transcription = s.recv(1024).decode('utf-8')
                        print(len(transcription))
                        # s.
                        self.gui_callback(transcription)
            except KeyboardInterrupt:
                print("Recording stopped.")
            finally:
                self.stream.stop_stream()
                self.stream.close()
                self.p.terminate()

class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Transcription Results:")
        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label)

        self.recorder = AudioRecorder(self.update_transcription)

        # Create a separate thread for recording to avoid blocking the GUI
        import threading
        self.recording_thread = threading.Thread(target=self.recorder.start_recording)

    def start_recording(self):
        self.recording_thread.start()

    def update_transcription(self, transcription):
        # Update the GUI with the received transcription
        self.label.setText(f"Transcription Results: {transcription}")

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
    window.start_recording()

    sys.exit(app.exec_())

if __name__ == "__main__":
    main()
