import re
import sys
from urllib.parse import unquote

import requests
from PyQt5.QtCore import QTimer
from PyQt5.QtGui import QColor, QPalette
from PyQt5.QtWidgets import QApplication, QLabel, QLineEdit, QMainWindow, QPushButton, QTextEdit


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Get Sec UID Scraper')
        self.setGeometry(100, 100, 600, 300)

        self.label = QLabel('Введите ссылку:', self)
        self.label.setGeometry(20, 20, 200, 30)

        self.input_field = QLineEdit(self)
        self.input_field.setGeometry(20, 50, 560, 30)

        self.button = QPushButton('Получить id', self)
        self.button.setGeometry(20, 90, 560, 30)
        self.button.clicked.connect(self.get_sec_uid)

        self.result_label = QTextEdit(self)
        self.result_label.setGeometry(20, 130, 560, 120)
        self.result_label.setReadOnly(True)

        self.copy_button = QPushButton('Копировать', self)
        self.copy_button.setGeometry(20, 260, 100, 30)
        self.copy_button.clicked.connect(self.copy_result)

    def get_sec_uid(self):
        url = self.input_field.text()
        try:
            decoded_url = unquote(url)
        except (ValueError, TypeError):
            self.result_label.setText('Ошибка при декодировании ссылки')
            return

        if not self._validate_link(decoded_url):
            self.result_label.setText('Неправильная ссылка (только на страницы tiktok пользователей)')
            return

        response = requests.get(decoded_url)
        pattern = r'"secUid":"(.*?)"'
        if response.status_code == 200 and (match := re.search(pattern, response.text)):
            sec_uid = match.group(1)
            self.result_label.setText(sec_uid)
        else:
            self.result_label.setText('Ошибка при получении данных')

    def copy_result(self):
        clipboard = QApplication.clipboard()
        clipboard.setText(self.result_label.toPlainText())
        palette = self.copy_button.palette()
        palette.setColor(QPalette.Button, QColor(0, 255, 0))
        self.copy_button.setPalette(palette)
        self.copy_button.setAutoFillBackground(True)

        timer = QTimer(self)
        timer.timeout.connect(self.reset_button_color)
        timer.start(1000)

    def reset_button_color(self):
        palette = self.copy_button.palette()
        palette.setColor(QPalette.Button, QColor(240, 240, 240))
        self.copy_button.setPalette(palette)
        self.copy_button.setAutoFillBackground(True)

    @staticmethod
    def _validate_link(link) -> bool:
        general_pattern = r'^https?://(?:\w+\.)*\w+\.\w+(?:/\S*)?$'
        tiktok_user_pattern = r'^https?://(?:www\.)?tiktok\.com/[^?&]+$'
        return re.match(general_pattern, link) is not None and re.match(tiktok_user_pattern, link) is not None


if __name__ == '__main__':
    app = QApplication(sys.argv)
    window = MainWindow()
    window.show()
    sys.exit(app.exec_())
