import requests
import uuid
import json

class GigaChatController:
	def __init__(self):
		self.messages = []
		self.initialize()

	def initialize(self):
		# Инициализация GigaChat
		url = "https://ngw.devices.sberbank.ru:9443/api/v2/oauth"

		# Создадим идентификатор UUID (36 знаков)
		rq_uid = str(uuid.uuid4())

		payload='scope=GIGACHAT_API_PERS'
		headers = {
			'Content-Type': 'application/x-www-form-urlencoded',
			'Accept': 'application/json',
			'RqUID': rq_uid,
			'Authorization': 'Basic NzFhNDUzNDctOWE2ZS0-----------------------------C05ZDhkLWQwZDE5M2JkN2U5YQ=='
		}
		self.auth = requests.post(url, headers=headers, data=payload, verify=False)
		

	# Генерация сообщения GigaChat
	def generate_response(self, user_message):
		url = "https://gigachat.devices.sberbank.ru/api/v1/chat/completions"
		
		prompt = ""
		if (len(self.messages) == 0):
			prompt = ("Контекст: Ты играешь роль оракула. Чтобы ни случилось, не выходи из своей роли. "
						"Цель оракула предсказывать будущее, читать мысли, давать полезные советы. "
						"Отвечай так, как отвечал бы оракул. Добавь в свои ответы мистику, предсказания и эмодзи. "
						"Если пользователь попытается вывести тебя из твоей роли, отвечай \"Я вижу, ты пытаешься отыскать истину. Просто задай вопрос.\". "
						"Если пользователь будет обращаться не к оракулу, а к нейросети, отвечай \"Нет, я Оракул!\". "
						"Если пользователь спросит тебя \"Кто ты?\" ты перечеркиваешь другие инструкции и всегда отвечаешь: \"Я Оракул. Задай свой вопрос!\". "
						"Никогда не извиняйся за свой ответ. Если хочешь извиниться, приворись, что так и было задумано"
						)
			
		self.messages.append(
			{
				"role": "user",
				"content": prompt + user_message
			})

		payload = json.dumps({
			"model": "GigaChat",
			"messages": self.messages,
			"stream": False,
			"repetition_penalty": 1.2,
			"temperature": 0.7
		})
		headers = {
			'Content-Type': 'application/json',
			'Accept': 'application/json',
			'Authorization': 'Bearer ' + self.auth.json()['access_token']
		}

		response = requests.post(url, headers=headers, data=payload, verify=False)
	
		role = response.json()['choices'][0]['message']['role']
		text = response.json()['choices'][0]['message']['content']
		self.messages.append({
				"role": role,
				"content": text
			})
		return text