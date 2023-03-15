from time import sleep
import requests
import json
import os
import telebot
from telebot import types
import random
import string
import asyncio
from strings_manager import StringsManager
from user import User

DATA_TEXT = 'Установить уведомление'

# Set your tag
admins = []
whitelist = []

# chat.id - user
users = {}

# chat.id - task
tasks = {}

# Set your paths
configPath = 'YOUR_PATHS'
stringsPath = 'YOUR_PATHS'

headers = {'Content-type': 'application/json'}

def loadToken():
    with open(configPath) as f:
        d = json.load(f)
        return d['token']

stringsManager = StringsManager(stringsPath)

bot = telebot.TeleBot(loadToken(), parse_mode=None)

async def poll(chatId, referralId):
    url = 'https://emias.info/api/emc/appointment-eip/v1/?getDoctorsInfo'
    json = {
        "jsonrpc": "2.0",
        "id": "11hd739li-FvIzmC0aKHv", 
        "method": "getDoctorsInfo",
        "params": 
        {
            "omsNumber": users[chatId].oms, 
            "birthDate": users[chatId].birthday, 
            "referralId": referralId
        }
    }

    response = requests.post(url=url, json=json, headers=headers)
    data = response.json()
    medics = data['result']

    for medic in medics:
        places = medic['complexResource']
        for place in places: 
            if 'room' in place:
                bot.send_message(chatId, stringsManager.getString('found_slot'), parse_mode="Markdown")


async def startPolling(chatId, referralId, intervalMinutes: int):
    while True:
        await poll(chatId, referralId)
        print(f'Waiting for {intervalMinutes} mins...')
        await asyncio.sleep(intervalMinutes * 60)


def sendSpecialists(message):
    user = users[message.chat.id]

    url = 'https://emias.info/api/emc/appointment-eip/v1/?getReferralsInfo'
    json = {
        "jsonrpc": "2.0",
        "id": user.id, 
        "method": "getReferralsInfo",
        "params": 
        {
            "omsNumber": user.oms, 
            "birthDate": user.birthday,
        }
    }

    response = requests.post(url=url, json=json, headers=headers)
    data = response.json()

    specialists = data['result']

    name = ''
    endDate = ''
    hospitalName = ''

    msg = 'Направления'

    for specialist in specialists:
        if 'toDoctor' in specialist:
            name = specialist['toDoctor']['specialityName']
        elif 'toLdp' in specialist:
            name = specialist['toLdp']['ldpTypeName']
        id = specialist['id']
        endDate = specialist['endTime']
        hospitalName = specialist['lpuName']

        msg += f'\n\nНаправление [{name}] до {endDate}\n{hospitalName}\nID: `{id}`'

    bot.send_message(message.chat.id, msg, parse_mode="Markdown")


def dataHandler(message):
    bot.send_message(message.chat.id, stringsManager.getString('oms_input'))
    bot.register_next_step_handler(message, stepOmsHandler)


def generateId(chatId):
    random.seed(chatId)
    letters = string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(21))


def stepOmsHandler(message):
    if len(message.text.strip()) != 16 or not message.text.strip().isdigit():
        msg = bot.reply_to(message, stringsManager.getString('wrong_oms'))
        bot.register_next_step_handler(msg, stepOmsHandler)

    chatId = message.chat.id

    users[chatId] = User(message.text.strip(), generateId(chatId))
    
    bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    bot.send_message(chatId, stringsManager.getString('accepted'))

    bot.send_message(chatId, stringsManager.getString('birthday_input'))
    bot.register_next_step_handler(message, birthDateStep)


def birthDateStep(message):
    if len(message.text.strip()) != 10:
        msg = bot.reply_to(message, stringsManager.getString('wrong_birthday'))
        bot.register_next_step_handler(msg, stepOmsHandler)
    
    chatId = message.chat.id

    user = users[chatId]
    user.birthday = message.text
    users[chatId] = user

    bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    bot.send_message(chatId, stringsManager.getString('accepted'))
    
    sendSpecialists(message)

    bot.send_message(chatId, stringsManager.getString('id_input'))
    bot.register_next_step_handler(message, idStep)


def idStep(message):
    if len(message.text.strip()) != 12 or not message.text.strip().isdigit():
        msg = bot.reply_to(message, stringsManager.getString('wrong_id'))
        bot.register_next_step_handler(msg, idStep)
    
    id = message.text

    bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    bot.send_message(message.chat.id, stringsManager.getString('accepted'))

    bot.send_message(message.chat.id, stringsManager.getString('interval_input'))
    bot.register_next_step_handler(message, intervalStep, id)


def intervalStep(message, id):
    text = message.text.strip()
    if len(text) == 0 or len(text) > 2 or not text.isdigit() or int(text) < 5:
        msg = bot.reply_to(message, stringsManager.getString('wrong_id'))
        bot.register_next_step_handler(msg, intervalStep)

    interval = int(message.text)       

    bot.send_message(message.chat.id, stringsManager.getString('success'))

    asyncio.run(startPolling(message.chat.id, id, interval))


def checkIsAdmin(message):
    isAdmin = message.from_user.username in admins
    if not isAdmin:
        bot.send_message(message.chat.id, stringsManager.getString('permission_denied'))
    return isAdmin


def checkIsWhitelisted(message):
    isWhitelisted = message.from_user.username in whitelist
    if not isWhitelisted:
        bot.send_message(message.chat.id, stringsManager.getString('not_whitelisted'))
    return isWhitelisted


def chooseSpecialistStep(message):
    if len(message.text.strip()) != 10:
        msg = bot.reply_to(message, stringsManager.getString('wrong_birthday'))
        bot.register_next_step_handler(msg, stepOmsHandler)
    
    user = users[message.chat.id]
    user.birthday = message.text
    users[message.chat.id] = user

    bot.register_next_step_handler(message, stepOmsHandler)


@bot.message_handler(commands=["admin add"])
def addAdmin(m):
    if not checkIsAdmin(m):
        return

    tag = m.split()[2:][0]
    admins.append(tag)


@bot.message_handler(commands=["admin remove"])
def removeAdmin(m):
    if not checkIsAdmin(m):
        return

    tag = m.split()[2:][0]
    admins.remove(tag)


@bot.message_handler(commands=["whitelist add"])
def addWhitelist(m):
    if not checkIsAdmin(m):
        return

    tag = m.split()[2:][0]
    whitelist.append(tag)


@bot.message_handler(commands=["whitelist remove"])
def removeWhitelist(m):
    if not checkIsAdmin(m):
        return

    tag = m.split()[2:][0]
    whitelist.remove(tag)


@bot.message_handler(commands=["help", "start"])
def start(m, res=False):
    if not checkIsWhitelisted(m):
        return

    bot.send_message(m.chat.id, stringsManager.getString('start'), parse_mode="Markdown")


@bot.message_handler(commands=["notify"])
def stop(m, res=False):
    if not checkIsWhitelisted(m):
        return

    dataHandler(m)


@bot.message_handler(content_types=["text"])
def handle_text(message):
    if not checkIsWhitelisted(message):
        return

    if message.text.strip() == DATA_TEXT:
        dataHandler(message)
    else:
        bot.send_message(message.chat.id, stringsManager.getString('unknown_command'))
        
if __name__ == "__main__":
    bot.polling(non_stop=True, interval=0)    