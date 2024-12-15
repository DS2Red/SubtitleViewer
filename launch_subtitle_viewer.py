import sys
import logging
from PyQt6.QtWidgets import QApplication
from subtitle_reader import SubtitleReader

def main():
    logging.basicConfig(level=logging.INFO, 
                        format='%(asctime)s - %(levelname)s - %(message)s',
                        filename='subtitle_viewer.log',
                        filemode='w')
    logging.info("Starting application from launch_subtitle_viewer.py")
    app = QApplication(sys.argv)
    logging.info("Created QApplication")
    ex = SubtitleReader()
    logging.info("Created SubtitleReader")
    sys.exit(app.exec())

if __name__ == '__main__':
    main()