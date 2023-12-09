import sys
from PySide6.QtWidgets import QApplication, QLabel, QVBoxLayout, QWidget, QTextEdit, QPushButton, QFileDialog, QSlider, QFontComboBox
from PySide6.QtCore import Qt, QObject, Signal
from whisper_online import *
import pyaudio
import webrtcvad
import numpy as np


class AudioRecorder(QObject):
    transcription_ready = Signal(str)

    def __init__(self):
        super().__init__()
        # ... (unchanged initialization code)

    def start_recording(self):
        self.stream.start_stream()

    def stop_recording(self):
        self.stream.stop_stream()

    def callback(self, in_data, frame_count, time_info, status):
        audio_chunk = np.frombuffer(in_data, dtype=np.int16)
        if self.vad.is_speech(audio_chunk.tobytes(), sample_rate=self.rate):
            self.online.insert_audio_chunk(audio_chunk)
            self.processed = False
        elif not self.processed:
            o = self.online.process_iter()
            self.processed = True
            if o[2] != "":
                self.transcription_ready.emit(o[2])
        return in_data, pyaudio.paContinue


class TranscriptionApp(QWidget):
    def __init__(self):
        super().__init__()

        self.label = QLabel("Transcription Results:")
        self.text_edit = QTextEdit()
        self.start_button = QPushButton("Start")
        self.stop_button = QPushButton("Stop")
        self.clear_button = QPushButton("Clear")
        self.save_button = QPushButton("Save/Export")
        self.font_size_slider = QSlider(Qt.Horizontal)
        self.font_combo_box = QFontComboBox()  # Font type selection
        self.font_color_button = QPushButton("Select Font Color")
        self.line_spacing_slider = QSlider(Qt.Horizontal)
        self.text_alignment_button = QPushButton("Toggle Text Alignment")
        self.text_shadow_button = QPushButton("Toggle Text Shadow")

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
        self.layout.addWidget(self.text_shadow_button)

        self.recorder = AudioRecorder()
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
        self.text_shadow_button.clicked.connect(self.toggle_text_shadow)

        self.recording_thread = None

    def start_recording(self):
        self.recording_thread = threading.Thread(target=self.recorder.start_recording)
        self.recording_thread.start()

    def update_transcription(self, transcription):
        current_text = self.text_edit.toPlainText()
        self.text_edit.setPlainText(current_text + "\n" + transcription)

    def clear_transcription(self):
        self.text_edit.clear()

    def save_transcription(self):
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

    def toggle_text_shadow(self):
        current_effect = self.text_edit.currentCharFormat().textOutline()
        if not current_effect.isVisible():
            shadow = QTextBlockFormat()
            shadow.setTopMargin(1)
            self.text_edit.setCurrentCharFormat(shadow)
        else:
            self.text_edit.clearSelection()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = TranscriptionApp()
    window.setWindowTitle("Real-time Transcription App")
    window.setGeometry(100, 100, 800, 600)

    window.show()

    sys.exit(app.exec_())