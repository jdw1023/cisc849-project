# Final Project for Accessible Computing
# Authors: JD Wang and Manjusree
# Code based on the example code from the Whisper Python API and whisper_streaming 
# uses library from https://github.com/ufal/whisper_streaming/blob/master/whisper_online.py


import sys
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QTextEdit, QPushButton, QFileDialog, QSlider, QFontComboBox, QColorDialog
from PySide6.QtCore import Qt, QObject, Signal
from PySide6.QtGui import QTextCursor
from whisper_online import *
import pyaudio
import webrtcvad
import numpy as np


class AudioRecorder(QObject):
    transcription_ready = Signal(str)

    def __init__(self, parent):
        super().__init__(parent)
        self.chunk = 480 # 480 # 0.03s * 16000 = 480
        self.format = pyaudio.paInt16
        self.channels = 1
        self.rate = 16000
        self.use_vad = True
        self.vad = webrtcvad.Vad(2)
        self.p = pyaudio.PyAudio()
        self.src_lan = "en"
        self.tgt_lan = "en"
        self.tokenizer = create_tokenizer(self.tgt_lan)
        self.asr = FasterWhisperASR(self.src_lan, "large-v3")
        # self.asr.set_translate_task()
        self.online = OnlineASRProcessor(self.asr, self.tokenizer)
        self.processed = False
        self.asr.use_vad()
        self.stream = self.p.open(format=self.format,
                                  channels=self.channels,
                                  rate=self.rate,
                                  input=True,
                                  frames_per_buffer=self.chunk,
                                  stream_callback=self.callback)
        
        # this is needed so that the program doesn't start recording immediately
        self.stream.stop_stream()

    def start_recording(self):
        self.stream.start_stream()
        self.parent().label.setText("Transcription Results (rec): ")

    def stop_recording(self):
        self.stream.stop_stream()
        self.online.init()

        self.parent().label.setText("Transcription Results (stopped): ")

    def close(self):
        self.stream.close()
        self.p.terminate()

    def callback(self, in_data, frame_count, time_info, status):
        audio_chunk = np.frombuffer(in_data, dtype=np.int16)
        if self.use_vad:
            if self.vad.is_speech(audio_chunk.tobytes(), sample_rate=self.rate):
                self.online.insert_audio_chunk(audio_chunk)
                self.processed = False
            elif not self.processed:
                o = self.online.process_iter()
                self.processed = True
                # o[2] = o[2].strip()
                result = o[2].strip()
                if result != "":
                    if "." in o[2]:
                        self.transcription_ready.emit(result+"\n")
                        self.online.init()
                    else:
                        self.transcription_ready.emit(result)
        else:
                self.online.insert_audio_chunk(audio_chunk)
                o = self.online.process_iter()
                result = o[2].strip()
                if result != "":
                    if "." in o[2]:
                        self.transcription_ready.emit(result+"\n")
                        self.online.init()
                    else:
                        self.transcription_ready.emit(result)


        return in_data, pyaudio.paContinue


class CaptioningApp(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Transcription Results:")
        self.text_edit = QTextEdit()
        self.text_edit.setReadOnly(True)

        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.clear_button = QPushButton("Clear")
        self.save_button = QPushButton("Save/Export")
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_combo_box = QFontComboBox()  # Font type selection
        self.font_color_button = QPushButton("Select Font Color")
        self.line_spacing_slider = QSlider(Qt.Horizontal)
        self.text_alignment_button = QPushButton("Toggle Text Alignment")
        self.transparency_button = QPushButton("Toggle Transparency")
        self.transparency_status = False

        self.layout = QVBoxLayout(self)
        self.layout.addWidget(self.label)
        self.layout.addWidget(self.text_edit)
        self.layout.addWidget(self.start_button)
        self.layout.addWidget(self.stop_button)
        self.layout.addWidget(self.clear_button)
        self.layout.addWidget(self.save_button)
        self.layout.addWidget(self.font_size_slider)
        self.layout.addWidget(self.font_combo_box)
        self.layout.addWidget(self.font_color_button)
        self.layout.addWidget(self.line_spacing_slider)
        self.layout.addWidget(self.text_alignment_button)
        self.layout.addWidget(self.transparency_button)
        

        self.recorder = AudioRecorder(self)
        self.recorder.transcription_ready.connect(self.update_transcription)

        self.start_button.clicked.connect(self.recorder.start_recording)
        self.stop_button.clicked.connect(self.recorder.stop_recording)
        self.clear_button.clicked.connect(self.clear_transcription)
        self.save_button.clicked.connect(self.save_transcription)
        self.font_size_slider.valueChanged.connect(self.update_font_size)
        self.font_combo_box.currentFontChanged.connect(self.update_font_type)
        self.font_color_button.clicked.connect(self.select_font_color)
        self.line_spacing_slider.valueChanged.connect(self.update_line_spacing)
        self.text_alignment_button.clicked.connect(self.toggle_text_alignment)
        self.transparency_button.clicked.connect(self.toggle_transparency)
        

        self.recording_thread = None


    # def toggle_transparency(self):
    #     self.setAttribute(Qt)

    def start_recording(self):
        self.recording_thread = threading.Thread(target=self.recorder.start_recording)
        self.recording_thread.start()

    def update_transcription(self, transcription):
        current_text = self.text_edit.toPlainText()
        self.text_edit.setPlainText(current_text + " " + transcription)
        self.text_edit.moveCursor(QTextCursor.End)

    def clear_transcription(self):
        self.text_edit.clear()

    def save_transcription(self):
        # Placeholder for save/export functionality
        options = QFileDialog.Options()
        file_name, _ = QFileDialog.getSaveFileName(self, "Save Transcription", "", "Text Files (*.txt);;All Files (*)",
                                                   options=options)
        if file_name:
            with open(file_name, 'w') as file:
                file.write(self.text_edit.toPlainText())

    def update_font_size(self):
        font_size = self.font_size_slider.value()
        font = self.text_edit.font()
        font.setPointSize(font_size)
        self.text_edit.setFont(font)

    def update_font_type(self, font):
        current_font = self.text_edit.font()
        current_font.setFamily(font.family())
        self.text_edit.setFont(current_font)

    def select_font_color(self):
        color = self.text_edit.textColor()
        selected_color = QColorDialog.getColor(color, self, "Select Font Color")
        if selected_color.isValid():
            self.text_edit.setTextColor(selected_color)

    def update_line_spacing(self):
        line_spacing = self.line_spacing_slider.value()
        self.text_edit.setStyleSheet(f"QTextEdit {{ line-height: {line_spacing}px; }}")

    def toggle_text_alignment(self):
        alignment = self.text_edit.alignment()
        if alignment == Qt.AlignLeft:
            self.text_edit.setAlignment(Qt.AlignRight)
        else:
            self.text_edit.setAlignment(Qt.AlignLeft)
    
    def toggle_transparency(self):
        if self.transparency_status:
            window.setStyleSheet("background: rgba(255,255,255,100%);")
            self.start_button.setStyleSheet("background: rgba(255,255,255,100%);")
        else:
            window.setStyleSheet("background: rgba(255,255,255,50%);")
        self.transparency_status = not self.transparency_status


def handle_last_window_closed():
    # Stop the recording thread when the GUI is closed
    window.recorder.stop_recording()
    window.recorder.close()
    sys.exit(app.exec_())

if __name__ == "__main__":
    # setup the GUI
    app = QApplication(sys.argv)

    # allow cleanup when the GUI is closed
    app.setQuitOnLastWindowClosed(False)
    app.lastWindowClosed.connect(handle_last_window_closed)

    # create main GUI
    window = CaptioningApp()
    window.setAttribute(Qt.WA_TranslucentBackground)
    window.setStyleSheet("background: rgba(255,255,255,100%)")
    window.setWindowTitle("Real-time Captioning App")
    window.setGeometry(100, 100, 800, 600)

    window.show()

    sys.exit(app.exec_())
