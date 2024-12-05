import sys
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

import mysql.connector
from PyQt6 import QtWidgets as qtw
from PyQt6 import QtGui as qtg
from PyQt6 import QtCore as qtc
import smtplib

# Подключение к базе данных MySQL
cnx = mysql.connector.connect(user='root', password='1234', host='localhost', database='calendar')


class EventCalendar(qtw.QCalendarWidget):
    def __init__(self, events, meetings, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.events = events
        self.meetings = meetings
        self.setGridVisible(True)

    def paintCell(self, painter, rect, date):
        """Отрисовка ячеек календаря с мероприятиями и встречами."""
        super().paintCell(painter, rect, date)

        date_str = date.toString('yyyy-MM-dd')

        # Рисуем мероприятия
        if date_str in self.events:
            events = self.events[date_str]
            self._draw_events(painter, rect, events)

        # Рисуем встречи
        if date_str in self.meetings:
            meetings = self.meetings[date_str]
            self._draw_meetings(painter, rect, meetings)

    def _draw_events(self, painter, rect, events):
        """Отображаем события (мероприятия) на календаре."""
        max_events_per_cell = 3
        event_height = 12
        y_offset = 5  # Начальная высота для первого события

        # Сначала рисуем мероприятия
        for idx, event in enumerate(events):
            if idx >= max_events_per_cell:
                break  # Ограничиваем количество событий, чтобы они не выходили за границы
            painter.setFont(qtg.QFont('Arial', 8))  # Меньший шрифт для текста
            painter.setPen(qtg.QPen(qtc.Qt.GlobalColor.blue))  # Устанавливаем цвет для мероприятия

            # Выводим текст внутри ячейки
            painter.drawText(
                rect.adjusted(2, y_offset, -2, -2),  # Смещение текста внутри ячейки
                qtc.Qt.AlignmentFlag.AlignLeft,
                event['event_name']  # Название события
            )

            # Смещаем текст вниз, чтобы следующее событие рисовалось ниже
            y_offset += event_height

        # Если мероприятий больше, чем можем отобразить, показываем "..." внизу
        if len(events) > max_events_per_cell:
            painter.setFont(qtg.QFont('Arial', 8, qtg.QFont.Weight.Bold))
            painter.setPen(qtg.QPen(qtc.Qt.GlobalColor.black))
            painter.drawText(
                rect.adjusted(2, y_offset, -2, -2),
                qtc.Qt.AlignmentFlag.AlignLeft,
                "..."
            )

    def _draw_meetings(self, painter, rect, meetings):
        """Отображаем встречи на календаре."""
        max_meetings_per_cell = 3
        meeting_height = 12
        y_offset = 5 + 3 * 12  # Начинаем рисовать встречи ниже мероприятий, с дополнительным отступом

        # Сначала рисуем встречи
        for idx, meeting in enumerate(meetings):
            if idx >= max_meetings_per_cell:
                break  # Ограничиваем количество встреч, чтобы они не выходили за границы
            painter.setFont(qtg.QFont('Arial', 8))  # Меньший шрифт для текста
            painter.setPen(qtg.QPen(qtc.Qt.GlobalColor.green))  # Устанавливаем цвет для встречи

            # Выводим текст внутри ячейки
            painter.drawText(
                rect.adjusted(2, y_offset, -2, -2),  # Смещение текста внутри ячейки
                qtc.Qt.AlignmentFlag.AlignLeft,
                meeting['event_name']  # Название встречи
            )

            # Смещаем текст вниз, чтобы следующее событие рисовалось ниже
            y_offset += meeting_height

        # Если встреч больше, чем можем отобразить, показываем "..." внизу
        if len(meetings) > max_meetings_per_cell:
            painter.setFont(qtg.QFont('Arial', 8, qtg.QFont.Weight.Bold))
            painter.setPen(qtg.QPen(qtc.Qt.GlobalColor.black))
            painter.drawText(
                rect.adjusted(2, y_offset, -2, -2),
                qtc.Qt.AlignmentFlag.AlignLeft,
                "..."
            )


class CalendarWindow(qtw.QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.setWindowTitle("Календарь событий")
        self.resize(900, 600)

        self.user_id = user_id

        try:
            self.conn = mysql.connector.connect(
                host="localhost",
                user="root",
                password="1234",  # Замените на ваш пароль
                database="calendar"
            )
            self.cursor = self.conn.cursor(dictionary=True)
            print("Подключение к базе данных успешно.")
        except mysql.connector.Error as e:
            qtw.QMessageBox.critical(self, "Ошибка", f"Не удалось подключиться к базе данных: {e}")
            sys.exit(1)

        self.events = {}  # Мероприятия
        self.meetings = {}  # Встречи
        self.load_events_from_db()
        self.load_meetings_from_db()

        # Календарь
        self.calendar = EventCalendar(self.events, self.meetings)

        # Боковая панель управления
        self.event_list = qtw.QListWidget()

        control_layout = qtw.QVBoxLayout()
        control_layout.addWidget(qtw.QLabel("События на выбранную дату:"))
        control_layout.addWidget(self.event_list)

        # Добавляем кнопки
        self.add_event_button = qtw.QPushButton("Добавить мероприятие")
        self.add_meeting_button = qtw.QPushButton("Добавить встречу")
        self.delete_button = qtw.QPushButton("Удалить")
        self.view_button = qtw.QPushButton("Просмотреть")
        control_layout.addWidget(self.view_button)

        # Обработчики событий для кнопок
        self.add_event_button.clicked.connect(self.add_event)
        self.add_meeting_button.clicked.connect(self.add_meeting)
        self.delete_button.clicked.connect(self.delete_item)  # Обработчик для удаления

        # Добавляем кнопки в макет
        control_layout.addWidget(self.add_event_button)
        control_layout.addWidget(self.add_meeting_button)
        self.view_button.clicked.connect(self.view_item)
        control_layout.addWidget(self.delete_button)  # Добавляем кнопку удаления

        control_widget = qtw.QWidget()
        control_widget.setLayout(control_layout)

        splitter = qtw.QSplitter()
        splitter.setOrientation(qtc.Qt.Orientation.Horizontal)
        splitter.addWidget(self.calendar)
        splitter.addWidget(control_widget)
        splitter.setStretchFactor(0, 3)
        splitter.setStretchFactor(1, 1)

        main_layout = qtw.QHBoxLayout(self)
        main_layout.addWidget(splitter)

        # Подключаем обработчик клика по календарю
        self.calendar.clicked.connect(self.handle_date_click)

    def load_events_from_db(self):
        """Загрузка мероприятий из базы данных для конкретного пользователя."""
        try:
            query = "SELECT * FROM events WHERE idusers = %s"
            self.cursor.execute(query, (self.user_id,))
            rows = self.cursor.fetchall()
            for row in rows:
                date = row['event_date'].strftime('%Y-%m-%d')  # Преобразуем дату в строку
                if date not in self.events:
                    self.events[date] = []
                self.events[date].append(
                    {'event_name': row['event_name'], 'description': row['description'], 'location': row['location'],
                     'type': 'event', 'idevents': row['idevents']})
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить мероприятия: {e}")

    def load_meetings_from_db(self):
        """Загрузка встреч из базы данных для конкретного пользователя."""
        try:
            query = "SELECT * FROM meetings WHERE idusers = %s"
            self.cursor.execute(query, (self.user_id,))
            rows = self.cursor.fetchall()
            for row in rows:
                date = row['meeting_date'].strftime('%Y-%m-%d')  # Преобразуем datetime в строку
                if date not in self.meetings:
                    self.meetings[date] = []
                self.meetings[date].append(
                    {'event_name': row['meeting_name'], 'description': row['description'], 'location': row['location'],
                     'type': 'meeting', 'idmeetings': row['idmeetings']})
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить встречи: {e}")

    def handle_date_click(self, date):
        """Обработчик клика по дате на календаре."""
        selected_date = date.toString('yyyy-MM-dd')
        self.event_list.clear()

        # Отображаем мероприятия и встречи для выбранной даты
        if selected_date in self.events:
            for event in self.events[selected_date]:
                self.event_list.addItem(f"Мероприятие: {event['event_name']}")

        if selected_date in self.meetings:
            for meeting in self.meetings[selected_date]:
                self.event_list.addItem(f"Встреча: {meeting['event_name']}")

    def add_event(self):
        """Окно для добавления мероприятия без ввода даты."""
        dialog = qtw.QDialog(self)
        dialog.setWindowTitle("Добавить мероприятие")
        layout = qtw.QFormLayout()

        event_name_input = qtw.QLineEdit(dialog)
        event_description_input = qtw.QLineEdit(dialog)
        event_location_input = qtw.QLineEdit(dialog)

        layout.addRow("Название мероприятия:", event_name_input)
        layout.addRow("Описание мероприятия:", event_description_input)
        layout.addRow("Место проведения:", event_location_input)

        save_button = qtw.QPushButton("Сохранить", dialog)
        layout.addWidget(save_button)
        dialog.setLayout(layout)

        # Сохраняем с выбранной датой из календаря
        save_button.clicked.connect(lambda: self.save_event(
            event_name_input.text(),
            self.calendar.selectedDate().toString('yyyy-MM-dd'),  # Получаем дату из выбранной ячейки календаря
            event_description_input.text(),
            event_location_input.text(),
            dialog
        ))

        dialog.exec()

    def save_event(self, name, date, description, location, dialog):
        """Сохранение мероприятия в базе данных"""
        try:
            query = "INSERT INTO events (idusers, event_name, event_date, description, location) VALUES (%s, %s, %s, %s, %s)"
            self.cursor.execute(query, (self.user_id, name, date, description, location))
            self.conn.commit()
            dialog.accept()
            self.events.clear()
            self.load_events_from_db()  # Перезагружаем мероприятия
            self.calendar.update()  # Обновляем календарь
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить мероприятие: {e}")

    def add_meeting(self):
        """Окно для добавления встречи без ввода даты."""
        dialog = qtw.QDialog(self)
        dialog.setWindowTitle("Добавить встречу")
        layout = qtw.QFormLayout()

        meeting_name_input = qtw.QLineEdit(dialog)
        meeting_description_input = qtw.QLineEdit(dialog)
        meeting_location_input = qtw.QLineEdit(dialog)

        layout.addRow("Название встречи:", meeting_name_input)
        layout.addRow("Описание встречи:", meeting_description_input)
        layout.addRow("Место встречи:", meeting_location_input)

        save_button = qtw.QPushButton("Сохранить", dialog)
        layout.addWidget(save_button)
        dialog.setLayout(layout)

        # Сохраняем с выбранной датой из календаря
        save_button.clicked.connect(lambda: self.save_meeting(
            meeting_name_input.text(),
            self.calendar.selectedDate().toString('yyyy-MM-dd 00:00:00'),  # Получаем дату из выбранной ячейки календаря
            meeting_description_input.text(),
            meeting_location_input.text(),
            dialog
        ))

        dialog.exec()

    def save_meeting(self, name, date, description, location, dialog):
        """Сохранение встречи в базе данных"""
        try:
            query = "INSERT INTO meetings (idusers, meeting_name, meeting_date, description, location) VALUES (%s, %s, %s, %s, %s)"
            self.cursor.execute(query, (self.user_id, name, date, description, location))
            self.conn.commit()
            dialog.accept()
            self.meetings.clear()
            self.load_meetings_from_db()  # Перезагружаем встречи
            self.calendar.update()  # Обновляем календарь
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить встречу: {e}")

    def delete_item(self):
        """Удалить выбранное событие или встречу."""
        selected_item = self.event_list.currentItem()

        if not selected_item:
            qtw.QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите элемент для удаления.")
            return

        # Извлекаем текст из выбранного элемента списка
        item_text = selected_item.text()

        # Проверяем, является ли элемент мероприятием или встречей
        if item_text.startswith("Мероприятие:"):
            item_type = 'event'
        elif item_text.startswith("Встреча:"):
            item_type = 'meeting'
        else:
            qtw.QMessageBox.warning(self, "Ошибка", "Неверный формат элемента.")
            return

        # Получаем ID события из текста
        item_name = item_text.split(":")[1].strip().split(" - ")[0]
        try:
            if item_type == 'event':
                query = "DELETE FROM events WHERE event_name = %s AND idusers = %s"
            else:
                query = "DELETE FROM meetings WHERE meeting_name = %s AND idusers = %s"

            self.cursor.execute(query, (item_name, self.user_id))
            self.conn.commit()

            # Успешное удаление
            qtw.QMessageBox.information(self, "Удаление", f"{item_type.capitalize()} успешно удалено.")
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить {item_type}: {e}")
            return

        # Обновляем данные
        self.events.clear()
        self.meetings.clear()
        self.load_events_from_db()
        self.load_meetings_from_db()
        self.calendar.update()  # Обновляем календарь
        self.handle_date_click(self.calendar.selectedDate())  # Обновляем список событий

    def delete_event(self, event_name):
        """Удалить мероприятие из базы данных"""
        try:
            query = "DELETE FROM events WHERE event_name = %s AND idusers = %s"
            self.cursor.execute(query, (event_name, self.user_id))
            self.conn.commit()
            qtw.QMessageBox.information(self, "Успех", f"Мероприятие '{event_name}' удалено.")
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить мероприятие: {e}")

    def delete_meeting(self, meeting_name):
        """Удалить встречу из базы данных"""
        try:
            query = "DELETE FROM meetings WHERE meeting_name = %s AND idusers = %s"
            self.cursor.execute(query, (meeting_name, self.user_id))
            self.conn.commit()
            qtw.QMessageBox.information(self, "Успех", f"Встреча '{meeting_name}' удалена.")
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось удалить встречу: {e}")

    def view_item(self):
        """Просмотр выбранного события или встречи."""
        selected_item = self.event_list.currentItem()

        if not selected_item:
            qtw.QMessageBox.warning(self, "Ошибка", "Пожалуйста, выберите элемент для просмотра.")
            return

        # Извлекаем текст из выбранного элемента списка
        item_text = selected_item.text()

        # Проверяем, является ли элемент мероприятием или встречей
        if "Мероприятие:" in item_text:
            item_type = 'event'
        elif "Встреча:" in item_text:
            item_type = 'meeting'
        else:
            qtw.QMessageBox.warning(self, "Ошибка", "Неизвестный тип элемента.")
            return

        # Получаем имя события из текста
        item_name = item_text.split(":")[1].strip().split(" - ")[0]

        # Загружаем данные о событии из базы данных
        try:
            if item_type == 'event':
                query = "SELECT * FROM events WHERE event_name = %s AND idusers = %s"
            else:
                query = "SELECT * FROM meetings WHERE meeting_name = %s AND idusers = %s"

            self.cursor.execute(query, (item_name, self.user_id))
            item_data = self.cursor.fetchone()

            if not item_data:
                qtw.QMessageBox.warning(self, "Ошибка", f"{item_type.capitalize()} не найдено.")
                return

        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить {item_type}: {e}")
            return

        # Открываем окно для просмотра и редактирования
        self.open_view_dialog(item_data, item_type)

    def open_view_dialog(self, item_data, item_type):
        """Открыть окно для просмотра и редактирования события без редактирования даты."""
        dialog = qtw.QDialog(self)
        dialog.setWindowTitle(f"Просмотр {item_type.capitalize()}")
        layout = qtw.QFormLayout(dialog)

        name_input = qtw.QLineEdit(item_data['event_name' if item_type == 'event' else 'meeting_name'])
        description_input = qtw.QLineEdit(item_data['description'])
        location_input = qtw.QLineEdit(item_data['location'])

        layout.addRow("Название:", name_input)
        layout.addRow("Описание:", description_input)
        layout.addRow("Место проведения:", location_input)

        # Кнопки сохранения и отмены
        save_button = qtw.QPushButton("Сохранить")
        cancel_button = qtw.QPushButton("Отмена")

        buttons_layout = qtw.QHBoxLayout()
        buttons_layout.addWidget(save_button)
        buttons_layout.addWidget(cancel_button)
        layout.addRow(buttons_layout)

        dialog.setLayout(layout)

        # Обработчик для кнопки сохранения
        save_button.clicked.connect(lambda: self.save_changes(item_data, item_type, name_input.text(),
                                                              item_data[
                                                                  'event_date' if item_type == 'event' else 'meeting_date'],
                                                              description_input.text(), location_input.text(), dialog))

        # Обработчик для кнопки отмены
        cancel_button.clicked.connect(dialog.reject)

        dialog.exec()

    def save_changes(self, item_data, item_type, name, date, description, location, dialog):
        """Сохранить изменения в событии или встрече."""
        try:
            if item_type == 'event':
                query = """
                    UPDATE events
                    SET event_name = %s, event_date = %s, description = %s, location = %s
                    WHERE idevents = %s AND idusers = %s
                """
                self.cursor.execute(query, (name, date, description, location, item_data['idevents'], self.user_id))
            else:
                query = """
                    UPDATE meetings
                    SET meeting_name = %s, meeting_date = %s, description = %s, location = %s
                    WHERE idmeetings = %s AND idusers = %s
                """
                self.cursor.execute(query, (name, date, description, location, item_data['idmeetings'], self.user_id))

            self.conn.commit()
            qtw.QMessageBox.information(self, "Успех", f"{item_type.capitalize()} успешно обновлено.")
            dialog.accept()

            # Перезагрузка данных
            self.events.clear()
            self.meetings.clear()
            self.load_events_from_db()
            self.load_meetings_from_db()
            self.calendar.update()
            self.handle_date_click(self.calendar.selectedDate())
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось сохранить изменения: {e}")


class ProfileWindow(qtw.QWidget):
    def __init__(self, user_id):
        super().__init__()
        self.setWindowTitle("Профиль пользователя")
        self.resize(600, 400)
        self.user_id = user_id
        self.layout = qtw.QVBoxLayout(self)

        # Загрузка данных пользователя
        self.load_user_data()

        # Кнопка для перехода к календарю
        open_calendar_button = qtw.QPushButton("Открыть календарь событий", self)
        open_calendar_button.clicked.connect(self.open_calendar_window)
        self.layout.addWidget(open_calendar_button)

        # Кнопка для отправки email
        send_email_button = qtw.QPushButton("Отправить email", self)
        send_email_button.clicked.connect(self.open_email_window)
        self.layout.addWidget(send_email_button)

    def load_user_data(self):
        """Загрузка и отображение данных пользователя."""
        try:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE idusers = %s", (self.user_id,))
            user = cursor.fetchone()
            if user:
                self.layout.addWidget(qtw.QLabel(f"Имя пользователя: {user['login']}"))
                self.layout.addWidget(qtw.QLabel(f"Имя: {user['firstname']}"))
                self.layout.addWidget(qtw.QLabel(f"Фамилия: {user['lastname']}"))
                self.layout.addWidget(qtw.QLabel(f"Email: {user['email']}"))
                self.layout.addWidget(qtw.QPushButton("Изменить данные", self))
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось загрузить данные профиля: {e}")

    def open_calendar_window(self):
        """Открытие окна календаря с событиями."""
        self.calendar_window = CalendarWindow(self.user_id)
        self.calendar_window.show()

    def open_email_window(self):
        """Открытие окна отправки email."""
        self.email_window = EmailWindow()
        self.email_window.show()


class RegisterWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Регистрация")
        self.resize(300, 300)

        layout = qtw.QVBoxLayout(self)

        self.username_input = qtw.QLineEdit(self)
        self.username_input.setPlaceholderText("Введите имя пользователя")

        self.firstname_input = qtw.QLineEdit(self)
        self.firstname_input.setPlaceholderText("Введите ваше имя")

        self.lastname_input = qtw.QLineEdit(self)
        self.lastname_input.setPlaceholderText("Введите вашу фамилию")

        self.password_input = qtw.QLineEdit(self)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(qtw.QLineEdit.EchoMode.Password)

        self.confirm_password_input = qtw.QLineEdit(self)
        self.confirm_password_input.setPlaceholderText("Подтвердите пароль")
        self.confirm_password_input.setEchoMode(qtw.QLineEdit.EchoMode.Password)

        self.email_input = qtw.QLineEdit(self)
        self.email_input.setPlaceholderText("Введите ваш email")

        register_button = qtw.QPushButton("Зарегистрироваться", self)
        register_button.clicked.connect(self.register)

        layout.addWidget(self.username_input)
        layout.addWidget(self.firstname_input)
        layout.addWidget(self.lastname_input)
        layout.addWidget(self.password_input)
        layout.addWidget(self.confirm_password_input)
        layout.addWidget(self.email_input)
        layout.addWidget(register_button)

    def register(self):
        """Логика регистрации нового пользователя."""
        username = self.username_input.text()
        firstname = self.firstname_input.text()
        lastname = self.lastname_input.text()
        password = self.password_input.text()
        confirm_password = self.confirm_password_input.text()
        email = self.email_input.text()

        # Проверка на пустые поля
        if not username or not password or not confirm_password or not email or not firstname or not lastname:
            qtw.QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return

        # Проверка совпадения паролей
        if password != confirm_password:
            qtw.QMessageBox.warning(self, "Ошибка", "Пароли не совпадают.")
            return

        try:
            cursor = cnx.cursor()
            query = """
                INSERT INTO users (login, password, email, firstname, lastname) 
                VALUES (%s, %s, %s, %s, %s)
            """
            data = (username, password, email, firstname, lastname)
            cursor.execute(query, data)
            cnx.commit()

            # Уведомление об успешной регистрации
            qtw.QMessageBox.information(self, "Успех", "Вы успешно зарегистрированы.")
            self.close()
            self.login_window = LoginWindow()
            self.login_window.show()

        except mysql.connector.Error as e:
            # Обработка ошибок MySQL
            qtw.QMessageBox.warning(self, "Ошибка", f"Ошибка регистрации: {e.msg}")
            print(f"Ошибка регистрации: {e}")  # Для отладки


class EmailWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Отправка email")
        self.resize(400, 300)

        self.layout = qtw.QVBoxLayout(self)

        self.to_input = qtw.QLineEdit(self)
        self.to_input.setPlaceholderText("Введите адрес получателя")

        self.subject_input = qtw.QLineEdit(self)
        self.subject_input.setPlaceholderText("Введите тему")

        self.message_input = qtw.QTextEdit(self)
        self.message_input.setPlaceholderText("Введите сообщение")

        send_button = qtw.QPushButton("Отправить", self)
        send_button.clicked.connect(self.send_email)

        self.layout.addWidget(qtw.QLabel("Получатель:"))
        self.layout.addWidget(self.to_input)
        self.layout.addWidget(qtw.QLabel("Тема:"))
        self.layout.addWidget(self.subject_input)
        self.layout.addWidget(qtw.QLabel("Сообщение:"))
        self.layout.addWidget(self.message_input)
        self.layout.addWidget(send_button)

    def send_email(self):
        """Отправка email через SMTP."""
        to_email = self.to_input.text()
        subject = self.subject_input.text()
        message = self.message_input.toPlainText()

        if not to_email or not subject or not message:
            qtw.QMessageBox.warning(self, "Ошибка", "Заполните все поля!")
            return

        # Данные для подключения к серверу SMTP
        smtp_server = "smtp.mail.ru"  # Ваш SMTP сервер (например, smtp.gmail.com)
        smtp_port = 25  # Порт для отправки email (587 для TLS)
        smtp_user = "emailformycalendar@mail.ru"
        smtp_password = "wEsjenRugtAZjmhEK1r5"

        # Создание MIME-объекта
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(message, 'plain'))

        try:
            # Подключение к серверу SMTP и отправка письма
            server = smtplib.SMTP(smtp_server, smtp_port)
            server.starttls()  # Защищенное соединение
            server.login(smtp_user, smtp_password)
            text = msg.as_string()
            server.sendmail(smtp_user, to_email, text)
            server.quit()

            qtw.QMessageBox.information(self, "Успех", "Письмо успешно отправлено!")
        except Exception as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Не удалось отправить письмо: {str(e)}")


class LoginWindow(qtw.QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Вход")
        self.resize(300, 150)

        layout = qtw.QVBoxLayout(self)

        self.username_input = qtw.QLineEdit(self)
        self.username_input.setPlaceholderText("Введите имя пользователя")

        self.password_input = qtw.QLineEdit(self)
        self.password_input.setPlaceholderText("Введите пароль")
        self.password_input.setEchoMode(qtw.QLineEdit.EchoMode.Password)

        login_button = qtw.QPushButton("Войти", self)
        login_button.clicked.connect(self.login)

        register_button = qtw.QPushButton("Зарегистрироваться", self)
        register_button.clicked.connect(self.register)

        layout.addWidget(self.username_input)
        layout.addWidget(self.password_input)
        layout.addWidget(login_button)
        layout.addWidget(register_button)

    def login(self):
        """Логика входа пользователя."""
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            qtw.QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return

        try:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE login = %s AND password = %s", (username, password))
            user = cursor.fetchone()

            if user:
                self.close()
                self.profile_window = ProfileWindow(user['idusers'])
                self.profile_window.show()
            else:
                qtw.QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Ошибка подключения к базе данных: {e}")

    def register(self):
        """Открытие окна регистрации."""
        self.close()
        self.register_window = RegisterWindow()
        self.register_window.show()


if __name__ == "__main__":
    app = qtw.QApplication([])
    window = LoginWindow()
    window.show()
    app.exec()


    def login(self):
        """Логика входа пользователя."""
        username = self.username_input.text()
        password = self.password_input.text()

        if not username or not password:
            qtw.QMessageBox.warning(self, "Ошибка", "Заполните все поля.")
            return

        try:
            cursor = cnx.cursor(dictionary=True)
            cursor.execute("SELECT * FROM users WHERE login = %s AND password = %s", (username, password))
            user = cursor.fetchone()

            if user:
                self.close()
                self.profile_window = ProfileWindow(user['idusers'])
                self.profile_window.show()
            else:
                qtw.QMessageBox.warning(self, "Ошибка", "Неверный логин или пароль.")
        except mysql.connector.Error as e:
            qtw.QMessageBox.warning(self, "Ошибка", f"Ошибка подключения к базе данных: {e}")

if __name__ == "__main__":
    app = qtw.QApplication([])
    window = LoginWindow()
    window.show()

    app.exec_()

if __name__ == "__main__":
    app = qtw.QApplication(sys.argv)
    login_window = LoginWindow()
    login_window.show()
    sys.exit(app.exec())
