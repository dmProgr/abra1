# -*- coding: utf-8 -*-
import requests
import time
import os
import json
from re import findall                      # Импортируем библиотеку по работе с регулярными выражениями
from subprocess import check_output         # Импортируем библиотеку по работе с внешними процессами
import RPi.GPIO as GPIO

# Переменным ADMIN_ID и TOKEN необходимо присвоить Вашим собственные значения
INTERVAL = 3 # Интервал проверки наличия новых сообщений (обновлений) на сервере в секундах
ADMIN_ID = 421056069 # ID пользователя. Комманды от других пользователей выполняться не будут
URL = 'https://api.vk.com/method' # Адрес HTTP Bot API
TOKEN = 'ba777fbd7831e6fc3da8613dd838e2d14b76d8352e5f4aaf1693ccde23c1ee2f347f35d8a33d8291c701d' # Ключ авторизации для Вашего бота
offset = 1  #ID последнего полученного обновления
key = '0' #текщий токен доступа
currentUser = {} #словарь, {'user': 'действие'} последовальтельности действий
GPIO.setmode(GPIO.BCM)
GPIO.setup(22, GPIO.OUT, initial=0)
GPIO.setup(9, GPIO.OUT, initial=0) #задействуем как выход, что б получить 0

room1 = False # состояние комнаты 1
print ('Start server...')



def check_updates():
	"""Проверка обновлений на сервере и инициация действий, в зависимости от команды"""
	global offset


	try:
		request = requests.post('https://lp.vk.com/wh166256214?act=a_check&key=' + str(key) + '&ts=' + str(offset) + '&wait=25') # Отправка запроса обновлений
		#request = requests.post(URL + TOKEN + '/getUpdates', data=data)

	except:
		log_event('Error getting updates') # Логгируем ошибку
		return False # Завершаем проверку


	if not request.status_code == 200: return False # Проверка ответа сервера

	if 'failed' in request.json():
		log_event('Ощибка токена : %s' % request.json())
		initLongPollServer()
		return False

	if not request.json()['updates']: return False # Проверка успешности обращения к API
	#ToDo обработка ответа с ошибкой failed

	offset = request.json()['ts']
	for update in request.json()['updates']: # Проверка каждого элемента списка
		#offset = update['update_id'] # Извлечение ID сообщения
		#если не сообщение пользователя, то пропускаем его
		if update['type'] != 'message_new':
				continue


		# Ниже, если в обновлении отсутствует блок 'object'
		# или же в блоке 'object' отсутствует блок 'body', тогда
		if not 'object' in update or not 'body' in update['object']:
			log_event('Unknown update: %s' % update) # сохраняем в лог пришедшее обновление
			continue # и переходим к следующему обновлению

		msg_id = update['object']['id'] # Извлечение ID сообщения

		if update['object']['read_state'] == '1':
			log_event('сообщение: %s прочитано' % msg_id)
			continue #пропускаем прочитанные сообшения


		from_id = update['object']['user_id'] # Извлечение ID чата (отправителя)
		name = 'userName' # Извлечение username отправителя
		"""
		if from_id != ADMIN_ID: # Если отправитель не является администратором, то
			send_text("You're not autorized to use me!", from_id) # ему отправляется соответствующее уведомление
			log_event('Unautorized: %s' % update) # обновление записывается в лог
			continue # и цикл переходит к следующему обновлению
		"""
		message = update['object']['body'] # Извлечение текста сообщения
		msgID = update['object']['id'] # Извлечение текста сообщения

		#ToDo помечать сообшения как прочитаные messages.markAsRead и загружать только прочитаные сообщения "read_state":1, как исполненные команды
		#пометки messages.markAsRead не работают сообщения все равно остаются "read_state":0. Выход - сохранять ts при выходе
		parameters = (msg_id, name, from_id, message.lower())
		log_event('Message (id%s) from %s (id%s): "%s"' % parameters) # Вывод в лог ID и текста сообщения

		# В зависимости от сообщения, выполняем необходимое действие
		run_command(*parameters)

def run_command(offset, name, from_id, cmd):
	global key
	global currentUser
	global room1
	
	if from_id in currentUser:
		
	#if from_id in currentUser and currentUser[from_id] == 'start':
		if not isINT(cmd):
			send_msg_id = send_text(from_id, 'Не верная команда', offset)
			return
			
		navigateMenu(cmd, from_id)
		if currentUser[from_id] == 1:
			msg = 'Меню 1\n1 - Меню 11\n2 - Меню 12'
		elif currentUser[from_id] == 11:
			msg = 'Меню 11\n1'
		elif currentUser[from_id] == 12:
			msg = 'Меню 12\n'
		elif currentUser[from_id] == 2 or currentUser[from_id] == 21:
			if cmd == '1': #если пришла команда на отключение/включение
				room1 = off_on_swith(room1)
				navigateMenu('9', from_id) #возвращаем на верх
			
			msg = 'Комната\n Свет - '
			if room1:
				msg = msg + 'Включен\n1 - Отключить свет'
			else:
				msg = msg + 'Отключен\n1 - Включить свет'
			msg = msg + '\n'
			
			
		#elif currentUser[from_id] == 21:
			#msg = 'Меню 21\n'
		elif currentUser[from_id] == 3:
			GPIO.output(22, 0)
			msg = 'Демонстрация работы выходов:\n22 - ВЫХОД\n3.3V\n9 - 0V\nСейчас 22 выход - 0V\n'
			msg = msg + 'Можно померить относительно +3.3В\n1 - активировать 22 выход'
		elif currentUser[from_id] == 31:
			GPIO.output(22, GPIO.HIGH)
			msg = 'Демонстрация работы выходов:\n22 - ВЫХОД\n3.3V\n9 - 0V\n'
			msg = msg + 'Сейчас 22 выход активен 3.3В\nМожно померить относительно 9 выхода (0В)'
		elif currentUser[from_id] == 0:
			msg = menuStart()
		elif currentUser[from_id] == 999:
			msg = 'Спасибо, до свидания'
			del currentUser[from_id]
		else:
			navigateMenu('9', from_id) # если нет обработчика такого пунта меню,
			# то отбрасываем на уровень вверх
			msg = 'Что то не так ' + str(currentUser[from_id])

		msg = msg + '\n9 - Назад\n0 - Выход'
		send_msg_id = send_text(from_id, msg, offset)
		#send_msg_id = send_text(from_id, msg, offset)
		#del currentUser[from_id]
		#key = cmd
		return

	elif cmd == 'start': # начало работы
		currentUser[from_id] = 0
		msg = menuStart()

	elif cmd == '/ping': # Ответ на ping
		msg = 'pong'

	elif cmd == '/temp': # Ответ на ping
		msg = checkTemp()
		
	elif cmd == '/help': # Ответ на help
		msg = 'No help today. Sorry.'

	else:
		msg = cmd

	send_msg_id = send_text(from_id, msg, offset) # Отправка ответа
	log_event('Send text to' + str(from_id) + ', id=' + str(send_msg_id))
	set_read_status2msg (offset) #помечаем сообщение как прочитаное

def log_event(text):
    """
    Процедура логгирования
    ToDo: 1) Запись лога в файл
    """
    event = '%s >> %s' % (time.ctime(), text)
    print (event)

def send_text(chat_id, text, msgID):
	"""Отправка текстового сообщения по chat_id
	ToDo: повторная отправка при неудаче"""
	log_event('Sending to %s: %s' % (chat_id, text)) # Запись события в лог
	data = {'user_id': chat_id, 'message': text, 'forward_messages': msgID, 'access_token': TOKEN, 'v': 5.50} # Формирование запроса
	request = requests.post(URL + '/messages.send', data=data) # HTTP запрос
	if not request.status_code == 200: # Проверка ответа сервера
		return False # Возврат с неудачей
	return request.json()['response'] # Проверка успешности обращения к API

def set_read_status2msg (msg_id):
	data = {'message_ids': msg_id, 'access_token': TOKEN, 'v': 5.50} # Формирование запроса
	request = requests.post(URL + '/messages.markAsRead', data=data) # HTTP запрос

def saveSettings():
	global offset
	settings_file = open("settings.txt", "w")
	settings_file.write(str(offset))
	settings_file.close()

def getSettings():
	global offset
	if os.path.exists("settings.txt"):
		settings_file = open("settings.txt")
		offset = settings_file.read()
		settings_file.close()


def initLongPollServer():
	global offset
	global key
	getServer = 'https://api.vk.com/method/groups.getLongPollServer?group_id=166256214&v=5.50&access_token=' + TOKEN
	response = requests.get(getServer)
	offset = response.json()['response']['ts']
	key = response.json()['response']['key']
	log_event('текущий ts: %s' % offset)

def navigateMenu(digit, userId):
	global currentUser
	inputint = int(digit)

	if inputint == 9:
		currentUser[userId] = currentUser[userId] // 10
	elif inputint == 0:
		currentUser[userId] = 999
	else:
		currentUser[userId] = currentUser[userId] * 10 + inputint

def menuStart():
	return '1 - Меню 1\n2 - Комната\n3 - Демонстрация работы выходов\n0 - Выход'

def isINT(a):
	try:
		int(a)
		return True
	except ValueError:
		return False
		
def checkTemp():
	try:
		temp = check_output(["vcgencmd","measure_temp"]).decode()    # Выполняем запрос температуры
		temp = float(findall('\d+\.\d+', temp)[0])                   # Извлекаем при помощи регулярного выражения значение температуры из строки "temp=47.8'C"
	except:
		temp = 'временно не поддерживается'
	return temp

def off_on_swith(swith):
	return not swith

#getSettings()
initLongPollServer()

if __name__ == "__main__":
	while True:
		try:
			check_updates()
			time.sleep(INTERVAL)
		except KeyboardInterrupt:
			GPIO.cleanup()
			saveSettings()
			print ('Прервано пользователем..')
			break
