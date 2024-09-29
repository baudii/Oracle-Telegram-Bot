from telegram import Update
from datetime import datetime
import json
import os

loaded_data = {}
FILENAME = "data/user_data.json"
USER_ID_KEY = 'user_id'
USERNAME_KEY = 'username'
REAL_NAME_KEY = 'real_name'
BIRTHDATE_KEY = 'birthdate'
LAST_TIME_USED = 'last_time_used'
ANSWER_ORDER = 'answer_order'
INCREMENT = 'increment'

QUESTION_ORDER = 'question_order'

def initialize():
	load_data()

# Функция для добавления данных в JSON-файл
def save_user_data(user_data):
	global loaded_data
	
	# Обновляем или добавляем данные пользователя
	loaded_data[user_data[USER_ID_KEY]] = user_data

	# Записываем обратно в файл
	save_data(loaded_data)


def save_data(data):
    try:
        # Создаем директорию, если она не существует
        os.makedirs(os.path.dirname(FILENAME), exist_ok=True)
            
        with open(FILENAME, 'w', encoding='utf-8') as file:
            json.dump(data, file, indent=2)
        print("Данные успешно сохранены.")
    except IOError as e:
        print(f"Ошибка при сохранении данных в файл: {e}")


# Функция для загрузки или обновления загруженных данных из JSON-файла
def load_data():
	global loaded_data
	if os.path.exists(FILENAME):
		try:
			with open(FILENAME, 'r', encoding='utf-8') as file:
				data = json.load(file)
		except (IOError, json.JSONDecodeError) as e:
			print(f"Ошибка при загрузке данных из файла: {e}")
			return
		loaded_data = data



# Функция для получения данных пользователя по ID
def get_data(id, name) -> dict[str, str]:
	user_id = str(id)  # Ключ должен быть строкой
	username = name

	user_data = loaded_data.get(user_id)
	
	if (user_data is None):
		# Создаем новые данные профиля пользователя
		user_data = {
			USER_ID_KEY: user_id,
			USERNAME_KEY: username,
			REAL_NAME_KEY: '',
			BIRTHDATE_KEY: '',
			LAST_TIME_USED: '',
			ANSWER_ORDER: [],
			INCREMENT: 0
		}
		
		save_user_data(user_data)

	return user_data
