import sys
import pytest
from PyQt6.QtWidgets import QApplication, QMainWindow, QPushButton, QLineEdit, QMessageBox
from PyQt6.QtCore import Qt
from PyQt6.QtTest import QTest
from unittest.mock import patch


# Пример простого окна
class RegisterWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация")
        self.resize(300, 300)

        self.username_input = QLineEdit(self)
        self.password_input = QLineEdit(self)
        self.password_input.setEchoMode(QLineEdit.EchoMode.Password)
        self.register_button = QPushButton("Зарегистрироваться", self)
        self.register_button.clicked.connect(self.register)

    def register(self):
        # Логика регистрации
        if not self.username_input.text() or not self.password_input.text():
            QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return


@pytest.fixture
def app():
    """Создание экземпляра приложения и окна для каждого теста."""
    app = QApplication(sys.argv)
    window = RegisterWindow()
    window.show()
    yield window
    window.close()


def test_register_empty_fields(app):
    # Мокируем QMessageBox внутри теста
    with patch("PyQt6.QtWidgets.QMessageBox.warning") as mock_warning:
        # Очистить все поля
        app.username_input.clear()
        app.password_input.clear()

        # Нажать на кнопку регистрации
        QTest.mouseClick(app.register_button, Qt.MouseButton.LeftButton)

        # Проверить, что был вызван метод warning с нужными параметрами
        mock_warning.assert_called_once_with(app, "Ошибка", "Заполните все поля.")
