from telegram.ext import ContextTypes
from apscheduler.triggers.cron import CronTrigger
from apscheduler.schedulers.asyncio import AsyncIOScheduler
import asyncio
import logging
import json
import os

from data import user_data_manager as udm
import predictions

# Логирование
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Файл для хранения данных пользователей
FILENAME = 'user_data.json'


# Отправка пуш-уведомлений
async def send_push_notifications(context: ContextTypes.DEFAULT_TYPE):
	udm.load_data()
	
	for chat_id, data in udm.loaded_data.items():
		try:
			await context.bot.send_message(chat_id=chat_id, text=predictions.get_new_preditction(data))
		except Exception as e:
			logger.error(f"Не удалось отправить сообщение пользователю {chat_id}: {e}")

# Запуск планировщика для ежедневных уведомлений
def start_scheduler(application):
	scheduler = AsyncIOScheduler(timezone="UTC")
	
	# Запуск каждый день в 10:00 UTC
	trigger = CronTrigger(hour=17, minute=12)
	
	scheduler.add_job(
		send_push_notifications, 
		trigger=trigger,  # Ежедневный запуск в 10:00 UTC
		args=[application],
	)
	scheduler.start()

