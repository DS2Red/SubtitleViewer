import sys
import logging
from PyQt6.QtWidgets import (QApplication, QMainWindow, QLabel, QWidget, QFileDialog,
                             QPushButton, QGridLayout, QVBoxLayout, QColorDialog, QFontDialog,
                             QDialog, QCheckBox, QListWidget, QListWidgetItem, QSplitter,
                             QSpinBox, QHBoxLayout)
from PyQt6.QtCore import Qt, QTimer, QEvent, QSettings, QElapsedTimer
from PyQt6.QtGui import QColor, QFont, QDragEnterEvent, QDropEvent
import pysrt
import os
import chardet
import ass
import io
import webvtt
import traceback
import re

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

class SubtitleDisplay(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent, Qt.WindowType.FramelessWindowHint)
        self.setStyleSheet("background-color: black;")
        self.layout = QVBoxLayout(self)
        self.subtitle_label = QLabel(self)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.layout.addWidget(self.subtitle_label)
        self.layout.setAlignment(Qt.AlignmentFlag.AlignBottom)
        self.layout.setContentsMargins(0, 0, 0, 50)  # Add bottom margin
        self.installEventFilter(self)
        self.subtitle_color = QColor('white')  # Default subtitle color

    def eventFilter(self, obj, event):
        if event.type() == QEvent.Type.KeyPress and event.key() == Qt.Key.Key_Escape:
            self.parent().exit_fullscreen()
            return True
        return super().eventFilter(obj, event)

    def set_text(self, text):
        self.subtitle_label.setText(text)

    def set_font(self, font):
        self.subtitle_label.setFont(font)
        self.update_subtitle_style()

    def set_background_color(self, color):
        self.setStyleSheet(f"background-color: {color.name()};")
        self.update_subtitle_style()

    def set_subtitle_color(self, color):
        self.subtitle_color = color
        self.update_subtitle_style()

    def update_subtitle_style(self):
        current_font = self.subtitle_label.font()
        self.subtitle_label.setStyleSheet(f"""
            color: {self.subtitle_color.name()};
            font-family: {current_font.family()};
            font-size: {current_font.pointSize()}px;
        """)
        self.subtitle_label.setTextFormat(Qt.TextFormat.RichText)

class SubtitleReader(QMainWindow):
    def __init__(self):
        super().__init__()
        logging.info("Initializing SubtitleReader")
        self.subtitles = None
        self.current_subtitle_index = 0
        self.subtitle_timer = QTimer(self)
        self.subtitle_timer.timeout.connect(self.update_subtitle)
        self.elapsed_timer = QElapsedTimer()
        self.last_update_time = 0
        self.subtitle_playing = False
        self.subtitle_position = 0
        
        self.subtitle_display = None
        self.start_from_selected_line = False
        
        self.setAcceptDrops(True)
        
        self.subtitle_list = None
        
        self.settings = QSettings("YourCompany", "SubtitleViewer")
        self.load_settings()
        
        self.subtitle_color = QColor('white')  # Default subtitle color
        
        self.current_subtitle_text = ""  # Add this line to store current subtitle text
        
        self.initUI()
        
        logging.info("Finished initializing SubtitleReader")

    def load_settings(self):
        font_family = self.settings.value("font_family", "Arial")
        font_size = int(self.settings.value("font_size", 24))
        self.current_font = QFont(font_family, font_size)
        self.subtitle_color = QColor(self.settings.value("subtitle_color", QColor('white')))

    def save_settings(self):
        self.settings.setValue("font_family", self.current_font.family())
        self.settings.setValue("font_size", self.current_font.pointSize())
        self.settings.setValue("subtitle_color", self.subtitle_color.name())

    def initUI(self):
        logging.info("Starting initUI")
        self.setWindowTitle('Subtitle Reader')
        self.setGeometry(100, 100, 800, 600)

        central_widget = QWidget()
        self.setCentralWidget(central_widget)
        main_layout = QVBoxLayout(central_widget)

        splitter = QSplitter(Qt.Orientation.Vertical)
        main_layout.addWidget(splitter)

        top_widget = QWidget()
        top_layout = QVBoxLayout(top_widget)
        splitter.addWidget(top_widget)

        self.subtitle_label = QLabel('Open a subtitle file to start', self)
        self.subtitle_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.subtitle_label.setFont(self.current_font)
        top_layout.addWidget(self.subtitle_label)
        logging.info("Subtitle label added")

        self.subtitle_list = QListWidget()
        self.subtitle_list.itemDoubleClicked.connect(self.start_from_selected_subtitle)
        splitter.addWidget(self.subtitle_list)

        controls_widget = QWidget()
        controls_layout = QGridLayout(controls_widget)
        main_layout.addWidget(controls_widget)
        logging.info("Controls widget created")

        controls_widget.setStyleSheet("""
            QWidget { background-color: rgba(200, 200, 200, 150); }
            QPushButton { background-color: white; }
        """)

        self.play_pause_button = QPushButton('Play Subtitles')
        self.play_pause_button.clicked.connect(self.play_pause_subtitles)
        controls_layout.addWidget(self.play_pause_button, 0, 0)

        self.open_subtitle_button = QPushButton('Open Subtitle File')
        self.open_subtitle_button.clicked.connect(self.open_subtitle_file)
        controls_layout.addWidget(self.open_subtitle_button, 0, 1)

        self.change_background_color_button = QPushButton('Change Background Color')
        self.change_background_color_button.clicked.connect(self.change_background_color)
        controls_layout.addWidget(self.change_background_color_button, 1, 0)

        self.change_font_button = QPushButton('Change Font')
        self.change_font_button.clicked.connect(self.change_font)
        controls_layout.addWidget(self.change_font_button, 1, 1)

        self.change_subtitle_color_button = QPushButton('Change Subtitle Color')
        self.change_subtitle_color_button.clicked.connect(self.change_subtitle_color)
        controls_layout.addWidget(self.change_subtitle_color_button, 1, 2)

        self.fullscreen_button = QPushButton('Fullscreen Subtitles')
        self.fullscreen_button.clicked.connect(self.toggle_fullscreen_subtitles)
        controls_layout.addWidget(self.fullscreen_button, 0, 2)

        self.start_selected_line_checkbox = QCheckBox('Start from selected line')
        self.start_selected_line_checkbox.setChecked(False)
        self.start_selected_line_checkbox.stateChanged.connect(self.toggle_start_from_selected_line)
        controls_layout.addWidget(self.start_selected_line_checkbox, 1, 3)

        default_font_widget = QWidget()
        default_font_layout = QHBoxLayout(default_font_widget)
        main_layout.addWidget(default_font_widget)

        self.default_font_button = QPushButton('Set Default Font')
        self.default_font_button.clicked.connect(self.set_default_font)
        default_font_layout.addWidget(self.default_font_button)

        self.default_font_size_spinbox = QSpinBox()
        self.default_font_size_spinbox.setRange(8, 72)
        self.default_font_size_spinbox.setValue(self.current_font.pointSize())
        self.default_font_size_spinbox.valueChanged.connect(self.set_default_font_size)
        default_font_layout.addWidget(self.default_font_size_spinbox)

        self.setStyleSheet("background-color: lightgray;")
        logging.info("Style sheet set")

        self.show()
        logging.info("Window shown")

        logging.info("Finished initUI")

    def set_default_font(self):
        font, ok = QFontDialog.getFont(self.current_font, self)
        if ok:
            self.current_font = font
            self.subtitle_label.setFont(self.current_font)
            self.default_font_size_spinbox.setValue(self.current_font.pointSize())
            self.save_settings()
            logging.info(f"Default font set to {font.family()}, {font.pointSize()}pt")

    def set_default_font_size(self, size):
        self.current_font.setPointSize(size)
        self.subtitle_label.setFont(self.current_font)
        self.save_settings()
        logging.info(f"Default font size set to {size}pt")

    def open_subtitle_file(self):
        logging.info("Opening subtitle file")
        file_name, _ = QFileDialog.getOpenFileName(self, "Open Subtitle File", "", "Subtitle Files (*.srt *.vtt *.ass *.ssa)")
        if file_name:
            self.load_subtitles(file_name)

    def load_subtitles(self, file_name):
        logging.info(f"Loading subtitles from file: {file_name}")
        _, file_extension = os.path.splitext(file_name)
        if file_extension.lower() in ['.srt', '.vtt', '.ass', '.ssa']:
            try:
                with open(file_name, 'rb') as f:
                    raw_data = f.read()
                detected_encoding = chardet.detect(raw_data)['encoding']
                logging.info(f"Detected encoding: {detected_encoding}")
                
                if file_extension.lower() == '.srt':
                    self.subtitles = pysrt.open(file_name, encoding=detected_encoding)
                elif file_extension.lower() in ['.ass', '.ssa']:
                    try:
                        with io.open(file_name, 'r', encoding=detected_encoding) as f:
                            content = f.read()
                        
                        # Attempt to fix color format
                        content = content.replace('PrimaryColour', 'PrimaryColour: &H')
                        content = content.replace('SecondaryColour', 'SecondaryColour: &H')
                        content = content.replace('TertiaryColour', 'TertiaryColour: &H')
                        content = content.replace('BackColour', 'BackColour: &H')
                        
                        parsed = ass.parse(io.StringIO(content))
                        self.subtitles = list(parsed.events)  # Convert EventsSection to list
                        logging.info(f"Loaded {len(self.subtitles)} ASS/SSA subtitles")
                        logging.debug(f"First subtitle: {self.subtitles[0] if self.subtitles else 'None'}")
                    except Exception as e:
                        logging.error(f"ASS/SSA parse error: {str(e)}")
                        logging.error(f"Traceback: {traceback.format_exc()}")
                        # If parsing fails, try to load as plain text
                        self.subtitles = self.parse_ssa_as_plain_text(content)
                elif file_extension.lower() == '.vtt':
                    self.subtitles = list(webvtt.read(file_name))
                
                logging.info(f"Loaded {len(self.subtitles)} subtitles")
                logging.debug(f"Subtitle type: {type(self.subtitles)}")
                logging.debug(f"First subtitle: {self.subtitles[0] if self.subtitles else 'None'}")
                
                self.subtitle_label.setText("Subtitles loaded successfully. Press Play to start.")
                self.subtitle_position = 0
                self.play_pause_button.setEnabled(True)
                self.populate_subtitle_list()
            except Exception as e:
                logging.error(f"Error loading subtitles: {str(e)}")
                self.subtitle_label.setText(f"Error loading subtitles: {str(e)}")
                # Log more details about the file
                try:
                    with io.open(file_name, 'r', encoding=detected_encoding) as f:
                        first_lines = ''.join(f.readlines(10))  # Read first 10 lines
                    logging.error(f"First 10 lines of the file:\n{first_lines}")
                except Exception as read_error:
                    logging.error(f"Error reading file content: {str(read_error)}")
        else:
            logging.error(f"Unsupported file format: {file_extension}")
            self.subtitle_label.setText(f"Unsupported file format: {file_extension}")
        self.current_subtitle_index = 0

    def parse_ssa_as_plain_text(self, content):
        lines = content.split('\n')
        subtitles = []
        for line in lines:
            if line.startswith('Dialogue:'):
                parts = line.split(',')
                if len(parts) >= 4:
                    start = parts[1].strip()
                    end = parts[2].strip()
                    text = ','.join(parts[3:]).strip()
                    subtitles.append({'start': start, 'end': end, 'text': text})
        return subtitles

    def populate_subtitle_list(self):
        self.subtitle_list.clear()
        if isinstance(self.subtitles, pysrt.SubRipFile):  # SRT format
            for subtitle in self.subtitles:
                item = QListWidgetItem(f"{subtitle.start} - {subtitle.end}\n{subtitle.text}")
                self.subtitle_list.addItem(item)
        elif isinstance(self.subtitles, list):  # ASS/SSA or VTT format
            for subtitle in self.subtitles:
                if isinstance(subtitle, ass.line.Dialogue):  # ASS/SSA format
                    item = QListWidgetItem(f"{subtitle.start} - {subtitle.end}\n{subtitle.text}")
                elif hasattr(subtitle, 'start') and hasattr(subtitle, 'end') and hasattr(subtitle, 'text'):  # Generic format (including VTT)
                    item = QListWidgetItem(f"{subtitle.start} - {subtitle.end}\n{subtitle.text}")
                elif isinstance(subtitle, dict):  # Plain text parsed SSA
                    item = QListWidgetItem(f"{subtitle['start']} - {subtitle['end']}\n{subtitle['text']}")
                else:
                    item = QListWidgetItem(f"Unknown format: {str(subtitle)}")
                self.subtitle_list.addItem(item)
        else:
            logging.error(f"Unknown subtitle format: {type(self.subtitles)}")
            self.subtitle_list.addItem(QListWidgetItem("Error: Unknown subtitle format"))
        
        logging.info(f"Populated subtitle list with {self.subtitle_list.count()} items")
        if self.subtitle_list.count() == 0:
            logging.warning("No subtitles were added to the list")

    def start_from_selected_subtitle(self, item):
        index = self.subtitle_list.row(item)
        if index >= 0:
            self.subtitle_position = self.get_start_time(self.subtitles[index]) // 50
        
        if self.start_from_selected_line:
            self.update_subtitle()
            if not self.subtitle_playing:
                self.play_pause_subtitles()
        else:
            self.subtitle_list.setCurrentRow(index)

    def change_background_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.setStyleSheet(f"background-color: {color.name()};")
            self.update_subtitle_style()
            if self.subtitle_display:
                self.subtitle_display.set_background_color(color)

    def change_font(self):
        current_font = self.subtitle_label.font()
        font, ok = QFontDialog.getFont(current_font, self)
        if ok:
            self.current_font = font
            self.update_subtitle_style()
            if self.subtitle_display:
                self.subtitle_display.set_font(font)
            logging.info(f"Font changed to {font.family()}, {font.pointSize()}pt")

    def change_subtitle_color(self):
        color = QColorDialog.getColor(self.subtitle_color, self, "Choose Subtitle Color")
        if color.isValid():
            self.subtitle_color = color
            self.update_subtitle_style()
            if self.subtitle_display:
                self.subtitle_display.set_subtitle_color(color)
            logging.info(f"Subtitle color changed to {color.name()}")

    def update_subtitle_style(self):
        self.subtitle_label.setStyleSheet(f"""
            color: {self.subtitle_color.name()};
            font-family: {self.current_font.family()};
            font-size: {self.current_font.pointSize()}px;
        """)
        self.subtitle_label.setTextFormat(Qt.TextFormat.RichText)

    def update_subtitle(self):
        if not self.subtitles or not self.subtitle_playing:
            return

        current_time = self.elapsed_timer.elapsed()
        time_diff = current_time - self.last_update_time
        self.last_update_time = current_time

        # Adjust subtitle_position based on actual elapsed time
        self.subtitle_position += time_diff

        # Find the most relevant subtitle for the current time
        current_subtitle = None
        for subtitle in self.subtitles:
            start_time = self.get_start_time(subtitle)
            end_time = self.get_end_time(subtitle)
            
            if start_time <= self.subtitle_position < end_time:
                current_subtitle = subtitle
                break
            elif self.subtitle_position < start_time:
                break

        # Update the displayed subtitle
        if current_subtitle:
            text = self.get_subtitle_text(current_subtitle)
            if text != self.current_subtitle_text:
                self.subtitle_label.setText(text)
                self.current_subtitle_text = text
                if self.subtitle_display:
                    self.subtitle_display.set_text(text)
                logging.debug(f"Displaying subtitle: {text} (Time: {self.subtitle_position}ms, Start: {start_time}ms, End: {end_time}ms)")
        else:
            if self.current_subtitle_text:
                self.subtitle_label.setText("")
                self.current_subtitle_text = ""
                if self.subtitle_display:
                    self.subtitle_display.set_text("")

        # Loop back to the beginning if we've reached the end
        if self.subtitle_position > self.get_end_time(self.subtitles[-1]):
            self.subtitle_position = 0
            self.elapsed_timer.restart()
            self.last_update_time = 0
            logging.info("Subtitle playback looped to beginning")

        # Schedule the next update
        self.subtitle_timer.setInterval(10)  # Update every 10ms for more precise timing

    def get_start_time(self, subtitle):
        if isinstance(self.subtitles, pysrt.SubRipFile):
            return subtitle.start.ordinal
        else:
            return self.time_to_milliseconds(subtitle.start)

    def get_end_time(self, subtitle):
        if isinstance(self.subtitles, pysrt.SubRipFile):
            return subtitle.end.ordinal
        else:
            return self.time_to_milliseconds(subtitle.end)

    def get_subtitle_text(self, subtitle):
        if isinstance(self.subtitles, pysrt.SubRipFile):
            text = subtitle.text
        elif isinstance(subtitle, ass.line.Dialogue):
            text = subtitle.text
        elif isinstance(subtitle, dict):  # Plain text parsed SSA
            text = subtitle['text']
        elif hasattr(subtitle, 'text'):  # Generic format (including VTT)
            text = subtitle.text
        else:
            text = str(subtitle)
    
        # Replace /N and \N with actual newline
        text = re.sub(r'/N|\\N', '\n', text)
    
        # Handle italics
        text = re.sub(r'{\\i1}(.*?){\\i0}', r'<i>\1</i>', text)  # ASS/SSA italics
        text = re.sub(r'<i>(.*?)</i>', r'<i>\1</i>', text)  # HTML-style italics
    
        # Remove other {...} style tags
        text = re.sub(r'{\\[^}]+}', '', text)
    
        # Remove other <...> style tags except <i> and </i>
        text = re.sub(r'<(?!/?(i|I)>)[^>]+>', '', text)
    
        return text.strip()

    def time_to_milliseconds(self, time_str):
        if isinstance(time_str, str):
            if ':' in time_str:  # SRT or ASS/SSA format
                parts = time_str.replace(',', '.').split(':')
                if len(parts) == 3:
                    h, m, s = parts
                    s, ms = s.split('.')
                return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(ms.ljust(3, '0'))
            elif len(parts) == 4:  # ASS/SSA format with 10ths of second
                h, m, s, cs = parts
                return (int(h) * 3600 + int(m) * 60 + int(s)) * 1000 + int(cs) * 10
            else:  # Assume it's already in milliseconds
                return int(float(time_str))
        else:
            return int(time_str.total_seconds() * 1000)

    def toggle_fullscreen_subtitles(self):
        if not self.subtitle_display:
            self.subtitle_display = SubtitleDisplay(self)
            self.subtitle_display.set_font(self.current_font)
            self.subtitle_display.set_subtitle_color(self.subtitle_color)
            screen = QApplication.primaryScreen().geometry()
            self.subtitle_display.setGeometry(screen)

        if self.subtitle_display.isVisible():
            self.exit_fullscreen()
        else:
            self.subtitle_display.showFullScreen()
            self.fullscreen_button.setText('Exit Fullscreen')

    def exit_fullscreen(self):
        if self.subtitle_display:
            self.subtitle_display.hide()
        self.fullscreen_button.setText('Fullscreen Subtitles')

    def toggle_start_from_selected_line(self, state):
        self.start_from_selected_line = state == Qt.CheckState.Checked.value
        logging.info(f"Start from selected line: {self.start_from_selected_line}")

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.acceptProposedAction()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file in files:
            _, extension = os.path.splitext(file)
            if extension.lower() in ['.srt', '.vtt', '.ass', '.ssa']:
                self.load_subtitles(file)
                break  # Load only the first valid subtitle file
        event.acceptProposedAction()

    def play_pause_subtitles(self):
        if not self.subtitles:
            return
    
        if self.subtitle_playing:
            self.subtitle_timer.stop()
            self.subtitle_playing = False
            self.play_pause_button.setText('Play Subtitles')
        else:
            if self.start_from_selected_line:
                current_index = self.subtitle_list.currentRow()
                if current_index >= 0:
                    self.subtitle_position = self.get_start_time(self.subtitles[current_index])
                else:
                    self.subtitle_position = 0
            else:
                self.subtitle_position = 0

            self.elapsed_timer.start()
            self.last_update_time = 0
            self.subtitle_timer.start(10)  # Update every 10ms for more precise timing
            self.subtitle_playing = True
            self.play_pause_button.setText('Pause Subtitles')
        logging.info(f"Subtitle playback {'paused' if not self.subtitle_playing else 'started'}")
        if self.subtitle_playing:
            self.update_subtitle()  # Immediately update the subtitle after starting playback
        
    def get_next_subtitle(self, current_time):
        for subtitle in self.subtitles:
            if self.get_start_time(subtitle) > current_time:
                return subtitle
        return None
    
    def closeEvent(self, event):
        self.save_settings()
        super().closeEvent(event)

if __name__ == '__main__':
    logging.info("Starting application from subtitle_reader.py")
    app = QApplication(sys.argv)
    ex = SubtitleReader()
    sys.exit(app.exec())