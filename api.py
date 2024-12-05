from flask import Flask, jsonify, request
from flasgger import Swagger
import mysql.connector
from mysql.connector import Error

app = Flask(__name__)
swagger = Swagger(app)


# Соединение с базой данных MySQL
def get_db_connection():
    try:
        # Убедитесь, что данные для подключения корректны
        connection = mysql.connector.connect(
            host='localhost',
            user='root',
            password='1234',
            database='calendar'
        )
        if connection.is_connected():
            print("Successfully connected to the database")
            return connection
    except Error as e:
        print("Error while connecting to MySQL", e)
        return None  # Возвращаем None, если не удалось подключиться

    connection = get_db_connection()
    if connection is None:
        return jsonify({"error": "Database connection failed"}), 500

    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM events')
    events = cursor.fetchall()
    cursor.close()
    connection.close()

    return jsonify(events)


# Получить все события
@app.route('/events', methods=['GET'])
def get_events():
    """
    Получить список всех событий
    ---
    responses:
      200:
        description: Список всех событий
        content:
          application/json:
            schema:
              type: array
              items:
                $ref: '#/components/schemas/Event'
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM events')
    events = cursor.fetchall()
    cursor.close()
    connection.close()
    return jsonify(events)


# Получить событие по ID
@app.route('/events/<int:event_id>', methods=['GET'])
def get_event(event_id):
    """
    Получить событие по ID
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: ID события
    responses:
      200:
        description: Событие найдено
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Event'
      404:
        description: Событие не найдено
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('SELECT * FROM events WHERE idevents = %s', (event_id,))
    event = cursor.fetchone()
    cursor.close()
    connection.close()

    if event:
        return jsonify(event)
    else:
        return jsonify({'message': 'Event not found'}), 404


# Создать новое событие
@app.route('/events', methods=['POST'])
def create_event():
    """
    Создать новое событие
    ---
    parameters:
      - name: event_name
        in: formData
        type: string
        required: true
        description: Название события
      - name: event_date
        in: formData
        type: string
        required: true
        description: Дата события
      - name: description
        in: formData
        type: string
        required: true
        description: Описание события
      - name: location
        in: formData
        type: string
        required: true
        description: Место события
    responses:
      201:
        description: Событие успешно создано
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Event'
    """
    event_name = request.form['event_name']
    event_date = request.form['event_date']
    description = request.form['description']
    location = request.form['location']

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)

    cursor.execute('''INSERT INTO events (event_name, event_date, description, location)
                      VALUES (%s, %s, %s, %s)''',
                   (event_name, event_date, description, location))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({
        'event_name': event_name,
        'event_date': event_date,
        'description': description,
        'location': location
    }), 201


# Обновить событие
@app.route('/events/<int:event_id>', methods=['PUT'])
def update_event(event_id):
    """
    Обновить событие по ID
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: ID события
      - name: event_name
        in: formData
        type: string
        required: false
        description: Новое название события
      - name: event_date
        in: formData
        type: string
        required: false
        description: Новая дата события
      - name: description
        in: formData
        type: string
        required: false
        description: Новое описание события
      - name: location
        in: formData
        type: string
        required: false
        description: Новое место события
    responses:
      200:
        description: Событие обновлено
        content:
          application/json:
            schema:
              $ref: '#/components/schemas/Event'
      404:
        description: Событие не найдено
    """
    event_name = request.form.get('event_name')
    event_date = request.form.get('event_date')
    description = request.form.get('description')
    location = request.form.get('location')

    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('''UPDATE events SET event_name = %s, event_date = %s, description = %s, location = %s
                      WHERE idevents = %s''',
                   (event_name, event_date, description, location, event_id))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({
        'event_id': event_id,
        'event_name': event_name,
        'event_date': event_date,
        'description': description,
        'location': location
    })


# Удалить событие
@app.route('/events/<int:event_id>', methods=['DELETE'])
def delete_event(event_id):
    """
    Удалить событие по ID
    ---
    parameters:
      - name: event_id
        in: path
        type: integer
        required: true
        description: ID события
    responses:
      200:
        description: Событие удалено
      404:
        description: Событие не найдено
    """
    connection = get_db_connection()
    cursor = connection.cursor(dictionary=True)
    cursor.execute('DELETE FROM events WHERE idevents = %s', (event_id,))
    connection.commit()
    cursor.close()
    connection.close()

    return jsonify({'message': 'Event deleted successfully'})


# Определение схемы для документации Swagger
def setup_swagger():
    app.config['SWAGGER'] = {
        "components": {
            "schemas": {
                "Event": {
                    "type": "object",
                    "properties": {
                        "idevents": {
                            "type": "integer",
                            "description": "ID события"
                        },
                        "event_name": {
                            "type": "string",
                            "description": "Название события"
                        },
                        "event_date": {
                            "type": "string",
                            "description": "Дата события"
                        },
                        "description": {
                            "type": "string",
                            "description": "Описание события"
                        },
                        "location": {
                            "type": "string",
                            "description": "Место события"
                        }
                    }
                }
            }
        }
    }


# Запуск Swagger UI и Flask
if __name__ == '__main__':
    setup_swagger()  # настройка Swagger
    app.run(debug=True)
