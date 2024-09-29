from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, ConversationHandler, MessageHandler, CallbackContext, filters
from datetime import datetime
import logging
import traceback
import random

from data import user_data_manager as udm
from predictions import questions
from gigachat_controller import GigaChatController
import predictions
import push

# Включаем логирование
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)
logger = logging.getLogger(__name__)

USER_DATA = 'user_data'
CONVERSATION_HANDLER = 'conversation_handler'

BUTTONS, ORACLE_MODULE, ASK_BIRTHDAY, ASK_QUESTIONS = range(4)

# ================================
# Обработчики
# ================================


# Обработчик команды /start
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
	logger.info(f"Функция start вызвана пользователем: {update.effective_user.username}")

	user_data = udm.get_data(update.effective_user.id, update.effective_user.username)
	context.user_data[USER_DATA] = user_data

	context.user_data[udm.QUESTION_ORDER] = random.sample(range(0, len(questions)), len(questions))

	markup = get_standard_markup(user_data)
	# Отправка сообщения с кнопками
	hello = get_hello(user_data)


	await update.message.reply_text(
		hello,
		reply_markup=markup
	)
	
	logger.info(f"Возвращаем BUTTONS={BUTTONS}")
	return BUTTONS
	


# Обработчик команды /help
async def help_command(update: Update, context):
    help_text = (
        "🌟 Привет! Я твой Оракул. Вот что я могу предложить:\n\n"
        "1️⃣ **Активируй бота с помощью /start!**\n\n"
        "2️⃣ **Говорить с оракулом:**\n"
        "   Переходи в режим живого общения и задавай любые вопросы, которые тебя волнуют.\n\n"
        "3️⃣ **Пройти тест:**\n"
        "   Ответь на вопросы, чтобы я смог составить твой портрет и предоставить индивидуальное предсказание.\n\n"
        "4️⃣ **Получить предсказание:**\n"
        "   Получи свое уникальное предсказание, основанное на твоих данных.\n\n"
        "✨ Если у тебя есть другие вопросы, просто напиши их!"
    )
    
    await update.message.reply_text(help_text, parse_mode='Markdown')

# Обработчик исключений
async def handle_error(update: Update, context: ContextTypes.DEFAULT_TYPE):
	# Получаем информацию об ошибке    
	error_message = str(context.error)
	error_type = type(context.error).__name__  # Получаем тип ошибки
	traceback_str = traceback.format_exc()  # Получаем traceback

	# Получаем ID чата из обновления, если доступно
	chat_id = update.effective_chat.id if update.effective_chat else "Неизвестный чат"
	
	# Логируем ошибку (опционально)
	logger.error(f"Type: {error_type} - {error_message}\nTraceback:\n{traceback_str}")

	# Отправляем сообщение об ошибке в чат
	await context.bot.send_message(chat_id=chat_id, text=f"Упс! Что-то пошло не так... Попробуйте снова!")
	
# Обработчик команды /cancel
async def cancel(update: Update, context: CallbackContext) -> int:
	update.message.reply_text("Диалог завершен.")
	return BUTTONS

# Обработчик нажатий на кнопки
async def handle_mode_choice(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
	print("Кнопка нажата")
	query = update.callback_query
	await query.answer()  # Подтверждаем нажаnтие кнопки
	await query.message.edit_reply_markup(reply_markup=None)
	
	user_data = context.user_data[USER_DATA]
	
	# Обрабатываем нажатие на кнопку
	match query.data:
		case 'talk_with_oracle':
			context.user_data['gigachat'] = GigaChatController()
			await query.edit_message_text(text="Вы выбрали: Говорить с оракулом.", reply_markup=None)
			await query.message.reply_text(text="Привет! Я Оракул, использующий силу генерации текста. Задай мне вопрос!")
			return ORACLE_MODULE
		
		case 'change_data':
			await query.edit_message_text(text="Вы выбрали: Пройти тест.")
			await query.message.reply_text(text="Привет! Я помогу тебе узнать твой гороскоп. Для начала скажи мне свою дату рождения в формате ДД.ММ.ГГГГ.")
			return ASK_BIRTHDAY
		
		case 'get_prediction':
			await query.message.reply_text(text="Вы выбрали: Получить предсказание.")
			answers_order = user_data.get(udm.ANSWER_ORDER, None)
			if not answers_order:
				keyboard = [
					[InlineKeyboardButton("Пройти тест!", callback_data='change_data')],
					[InlineKeyboardButton("Говорить с оракулом", callback_data='talk_with_oracle')]
				]
				reply = "Для составления личного гороскопа нужно пройти тест и ответить на несколько вопросов"
			else:
				keyboard = [ [InlineKeyboardButton("Вернуться!", callback_data='back')] ]
				reply = predictions.generate_prediction(user_data)
			
			reply_markup = InlineKeyboardMarkup(keyboard)
				
			await query.message.reply_text(text=reply, reply_markup=reply_markup)
			return BUTTONS
		
		case 'back':
			await query.edit_message_text("Вы вернулись. Хотите сделать что-то еще?", reply_markup=get_standard_markup(user_data))
			return BUTTONS

# ================================
# Состояния
# ================================

# Функция для обработки сообщений (вопросов)
async def handle_message(update: Update, context):
	user_message = update.message.text
	sent_message = await update.message.reply_text("Оракул обдумывает твой вопрос...")
	
	# Генерируем ответ через GigaChat
	response = context.user_data['gigachat'].generate_response(user_message)
	
	# Отправляем ответ пользователю
	await sent_message.edit_text(response)
	
# Спрашиваем дату рождения
async def ask_birthday(update: Update, context: CallbackContext) -> int:
	try:
		user_message = update.message.text
		birthdate = datetime.strptime(user_message, '%d.%m.%Y')
		age = (datetime.now() - birthdate).days // 365

		if age < 2 or age > 110:
			raise ValueError()
			
		birthdate_str = birthdate.strftime('%d.%m.%Y')
			
		await update.message.reply_text(f"Дата рождения принята: {birthdate_str}. Теперь давай я задам тебе несколько вопросов.")

		context.user_data[udm.BIRTHDATE_KEY] = birthdate_str
		
		# Задаем первый вопрос
		await update.message.reply_text(questions[context.user_data[udm.QUESTION_ORDER][0]])
		context.user_data[udm.ANSWER_ORDER] = []
		return ASK_QUESTIONS
	except ValueError:
		await update.message.reply_text("Пожалуйста, введи корректную дату в формате ДД.ММ.ГГГГ.")
		return ASK_BIRTHDAY

# Функция "рекурсивно" задает 4 вопроса и выдает результат
async def ask_questions(update: Update, context: CallbackContext) -> int:
	answer = update.message.text
	index = predictions.get_answer_index(answer)
	if index < 0:
		await update.message.reply_text("Не смог обработать твой ответ. Введите один из предложенных вариантов, который тебе наиболее близок.")
		return ASK_QUESTIONS

	context.user_data[udm.ANSWER_ORDER].append(index)
	
	questions_answered = len(context.user_data[udm.ANSWER_ORDER])
	questions_order = context.user_data[udm.QUESTION_ORDER]
	# Если еще есть вопросы, задаем следующий
	if questions_answered < predictions.TOTAL_QUESTION_NUM:
		next_question = questions[questions_order[questions_answered]]
		await update.message.reply_text(next_question)
		return ASK_QUESTIONS

	# Если все вопросы заданы, переходим к следующему этапу
	user_data = context.user_data[USER_DATA]
	user_data[udm.BIRTHDATE_KEY] = context.user_data[udm.BIRTHDATE_KEY]
	user_data[udm.ANSWER_ORDER] = context.user_data[udm.ANSWER_ORDER]
	
	prediction = predictions.generate_prediction(user_data)

	keyboard = [ [InlineKeyboardButton("Вернуться!", callback_data='back')] ]

	await update.message.reply_text(text = prediction, reply_markup = InlineKeyboardMarkup(keyboard))
	return BUTTONS

# Получаем приветствие бота
def get_hello(user_data):
	if user_data[udm.REAL_NAME_KEY] != "":
		return f"Рад снова тебя видеть, { user_data[udm.REAL_NAME_KEY]}! Как я могу помочь тебе сегодня?"
	return "Привет, странник! Как я могу помочь тебе сегодня?"
	
def get_standard_markup(user_data):
	# Определение кнопок
	ans_ord = user_data[udm.ANSWER_ORDER]
	
	test_button_text = "Пройти тест" if not ans_ord else "Перепройти тест"
	
	keyboard = [
		[InlineKeyboardButton(test_button_text, callback_data='change_data')],
		[InlineKeyboardButton("Получить предсказание", callback_data='get_prediction')],
		[InlineKeyboardButton("Говорить с оракулом", callback_data='talk_with_oracle')]
	]
	
	# Создание клавиатуры
	return InlineKeyboardMarkup(keyboard)


# ================================
# MAIN
# ================================

if __name__ == "__main__":
	TOKEN = "--------------------------"
	
	application = Application.builder().token(TOKEN).build()

	# Добавляем обработчики
	application.add_handler(CommandHandler("back", start))
	application.add_handler(CommandHandler("help", help_command))
	application.add_handler(ConversationHandler(
		entry_points=[CommandHandler('start', start)],
		states={
			BUTTONS:	       [CallbackQueryHandler(handle_mode_choice)],
			ORACLE_MODULE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message)],
			ASK_BIRTHDAY:  [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_birthday)],
			ASK_QUESTIONS: [MessageHandler(filters.TEXT & ~filters.COMMAND, ask_questions)]
		},
		fallbacks=[CommandHandler('start', start)],
		allow_reentry=True
	))
	
	application.add_error_handler(handle_error)
	
	udm.initialize()
	push.start_scheduler(application)
	application.run_polling()
