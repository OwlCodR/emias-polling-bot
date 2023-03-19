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
from referral_info import ReferralInfo
from specialist_info import SpecialistInfo
from slot_info import SlotInfo
import logging

# Set your tag
admins = ['OwlCodR']
whitelist = ['OwlCodR']

# chat.id - user
users = {}

# chat.id - task
tasks = {}

# Set your paths
configPath = 'config.json'

LOGGER_LEVEL = logging.DEBUG
loggerFormat = "%(asctime)s | %(levelname)s\t| %(name)s.%(funcName)s:%(lineno)d | %(message)s"

headers = None
logger = None
stringsManager = None

def loadToken():
    with open(configPath) as f:
        d = json.load(f)
        return d['token']

bot = telebot.TeleBot(loadToken(), parse_mode=None)

def init():
    global headers, logger, stringsManager
    
    headers = {'Content-type': 'application/json'}
    
    with open(configPath) as f:
        d = json.load(f)
        
        stringsManager = StringsManager(d['strings_path'])
        logsPath = d['logs_path']
        
        logging.basicConfig(
            format=loggerFormat, 
            filename=logsPath, 
            encoding='utf-8', 
            level=LOGGER_LEVEL
        )
        
        logger = logging.getLogger('emias-polling-bot')

        logger.info('init() finished')


async def createAppointment(chatId, startTime, endTime):
    logger.info(f'{chatId} | createAppointment()...')
    
    url = 'https://emias.info/api/emc/appointment-eip/v1/?createAppointment'
    json = {
        "jsonrpc": "2.0",
        "id": "11hd739li-FvIzmC0aKHv",
        "method": "createAppointment",
        "params": {
            "omsNumber": users[chatId].oms,
            "birthDate": users[chatId].birthday,
            "availableResourceId": users[chatId].availableResourceId,
            "complexResourceId": users[chatId].complexResourceId,
            "specialityId": users[chatId].speciality,
            "referralId": users[chatId].referralId,
            "startTime": users[chatId].startTime,
            "endTime": users[chatId].endTime
        }
    }
    
    response = requests.post(url=url, json=json, headers=headers)
    data = response.json()
    
    logger.debug(f'{chatId} | {json}')


def checkOmsAndBirthday(chatId):
    logger.info(f'{chatId} | checkOmsAndBirthday()...')

    isData = users[chatId].oms == None or users[chatId].birthday == None

    if not isData:
        logger.error(f'{chatId} | Oms or birthday is None!')

    return isData


def setAvailableSlot(chatId):
    logger.info(f'{chatId} | getAvailableSlots()...')
    
    checkOmsAndBirthday(chatId)

    url = 'https://emias.info/api/emc/appointment-eip/v1/?getAvailableResourceScheduleInfo'
    json = {
        "jsonrpc": "2.0",
        "id": "11hd739li-FvIzmC0aKHv",
        "method": "getAvailableResourceScheduleInfo",
        "params": {
            "omsNumber": users[chatId].oms,
            "birthDate": users[chatId].birthday,
            "availableResourceId": users[chatId].availableResourceId,
        }
    }

    response = requests.post(url=url, json=json, headers=headers)
    data = response.json()

    logger.debug(f'{chatId} | {json}')

    result = data['result']
    schedule = result['scheduleOfDay']

    for day in schedule:
        date = day['date']

        if users[chatId].availabilityDate[:10] in date:
            slots = day['scheduleBySlot'][0]['slot']
            for slot in slots:
                if users[chatId].availabilityDate == slot['startTime']:
                    users[chatId].startTime = users[chatId].availabilityDate
                    users[chatId].endTime = slot['startTime']['endTime']


async def poll(chatId):
    logger.info(f'{chatId} | poll()...')
    
    url = 'https://emias.info/api/emc/appointment-eip/v1/?getDoctorsInfo'
    json = {
        "jsonrpc": "2.0",
        "id": "11hd739li-FvIzmC0aKHv", 
        "method": "getDoctorsInfo",
        "params": 
        {
            "omsNumber": users[chatId].oms, 
            "birthDate": users[chatId].birthday, 
            "referralId": users[chatId].referralId
        }
    }

    response = requests.post(url=url, json=json, headers=headers)
    data = response.json()
    
    logger.debug(f'{chatId} | {json}')
    
    medics = data['result']

    for medic in medics:
        places = medic['complexResource']
        for place in places: 
            if 'room' in place:
                bot.send_message(
                    chatId,
                    stringsManager.getString('found_slot'), 
                    parse_mode="Markdown"
                )
                
                users[chatId].complexResourceId = place['id']
                users[chatId].availabilityDate = place['room']['availabilityDate']
                users[chatId].availableResourceId = medics['id']
                
                setAvailableSlot(chatId)

                if users[chatId].isAutoAppointment:
                    createAppointment(chatId)

    logger.info(f'{chatId} | poll() finished')


async def startPolling(chatId):
    logger.info(f'{chatId} | startPolling()...')
    pollingIntervalMinutes = users[chatId].pollingIntervalMinutes
    while True:
        await poll(chatId)
        logger.info(f'{chatId} | Waiting for {pollingIntervalMinutes} mins...')
        await asyncio.sleep(pollingIntervalMinutes * 60)


def getSpecialists(message):
    user = users[message.chat.id]

    url = 'https://emias.info/api/emc/appointment-eip/v1/?getSpecialitiesInfo'
    json = {
        "jsonrpc": "2.0",
        "id": user.id, 
        "method": "getSpecialitiesInfo",
        "params": 
        {
            "omsNumber": user.oms, 
            "birthDate": user.birthday,
        }
    }

    response = requests.post(url=url, json=json, headers=headers)
    data = response.json()
    
    logger.debug(f'{message.chat.id} | {json}')

    specialistsJson = data['result']
    
    specialists = []
    
    for specialist in specialistsJson:
        name = specialist['name']
        code = specialist['code']
        
        specialists.append(SpecialistInfo(name, code))
    
    return specialists


def getReferrals(message):
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
    
    logger.debug(f'{message.chat.id} | {json}')

    specialists = data['result']

    referrals = []
    
    for specialist in specialists:
        name = None
        if 'toDoctor' in specialist:
            name = specialist['toDoctor']['specialityName']
        elif 'toLdp' in specialist:
            name = specialist['toLdp']['ldpTypeName']
        referralId = specialist['id']
        endDate = specialist['endTime']
        hospitalName = specialist['lpuName']
        
        referrals.append(ReferralInfo(name, endDate, hospitalName, referralId))
    
    return referrals


def getAppointemntsInfo(message):
    logger.info(f'{message.chat.id} | sendAppointemntsInfo()...')
    
    referrals = getReferrals(message)
    
    # TODO Add specialists support
    # specialists = getSpecialists(message)

    msg = 'Направления'
    
    for referral in referrals:
        msg += f'\n\nНаправление "{referral.name}" до {referral.endDate}\n{referral.hospitalName}\nID: `{referral.referralId}`'
    
    bot.send_message(message.chat.id, msg, parse_mode="Markdown")
    
    return referrals


def dataHandler(message):    
    bot.send_message(message.chat.id, stringsManager.getString('oms_input'))
    bot.register_next_step_handler(message, stepOmsHandler)


def generateId(chatId):
    random.seed(chatId)
    letters = string.ascii_uppercase
    return ''.join(random.choice(letters) for i in range(21))


def stepOmsHandler(message):
    chatId = message.chat.id

    if len(message.text.strip()) != 16 or not message.text.strip().isdigit():
        msg = bot.send_message(chatId, stringsManager.getString('wrong_oms'))
        bot.register_next_step_handler(msg, stepOmsHandler)
    
    users[chatId] = User(message.text.strip(), generateId(chatId))
    
    accept(message)

    bot.send_message(chatId, stringsManager.getString('birthday_input'))
    bot.register_next_step_handler(message, birthDateStep)


def birthDateStep(message):
    chatId = message.chat.id

    if len(message.text.strip()) != 10:
        msg = bot.send_message(chatId, stringsManager.getString('wrong_birthday'))
        bot.register_next_step_handler(msg, stepOmsHandler)

    users[chatId].birthday = message.text

    accept(message)
    
    referrals = getAppointemntsInfo(message)
    
    # TODO ldpID or specialityId

    bot.send_message(chatId, stringsManager.getString('id_input'))
    bot.register_next_step_handler(message, idStep)


def idStep(message):
    if len(message.text.strip()) != 12 or not message.text.strip().isdigit():
        msg = bot.send_message(message.chat.id, stringsManager.getString('wrong_id'))
        bot.register_next_step_handler(msg, idStep)
    
    users[message.chat.id].referralId = message.text

    accept(message)

    bot.send_message(message.chat.id, stringsManager.getString('interval_input'))
    bot.register_next_step_handler(message, intervalStep)


def intervalStep(message):
    text = message.text.strip()
    if len(text) == 0 or len(text) > 2 or not text.isdigit() or int(text) < 5:
        msg = bot.send_message(message.chat.id, stringsManager.getString('wrong_id'))
        bot.register_next_step_handler(msg, intervalStep)

    users[message.chat.id].pollingIntervalMinutes = int(message.text) 
    
    accept(message)
    
    bot.send_message(message.chat.id, stringsManager.getString('auto_appoint_step'))
    bot.register_next_step_handler(message, autoAppointmentStep)


def autoAppointmentStep(message):
    text = message.text.strip().lower()
    
    yes = stringsManager.getString('yes')
    no = stringsManager.getString('no')
    
    if text != yes and text != no:
        msg = bot.send_message(
            message.chat.id, stringsManager.getString('wrong_answer')
        )
        bot.register_next_step_handler(msg, autoAppointmentStep)

    users[message.chat.id].isAutoAppointment = True if text == yes else False
    
    accept(message)
    
    bot.send_message(message.chat.id, stringsManager.getString('success'))
    asyncio.run(startPolling(message.chat.id))


def checkIsAdmin(message):
    isAdmin = message.from_user.username in admins
    if not isAdmin:
        bot.send_message(message.chat.id, stringsManager.getString('permission_denied'))
    return isAdmin


def checkIsWhitelisted(message):
    if message.from_user.username in admins:
        return True
    
    isWhitelisted = message.from_user.username in whitelist
    if not isWhitelisted:
        bot.send_message(message.chat.id, stringsManager.getString('not_whitelisted'))
    return isWhitelisted


def chooseSpecialistStep(message):
    if len(message.text.strip()) != 10:
        msg = bot.send_message(
            message.chat.id, stringsManager.getString('wrong_birthday')
        )
        bot.register_next_step_handler(msg, stepOmsHandler)
    
    users[message.chat.id].birthday = message.text
    
    accept(message)

    bot.register_next_step_handler(message, stepOmsHandler)


def accept(message):
    bot.delete_message(chat_id=message.chat.id, message_id=message.id)
    bot.send_message(message.chat.id, stringsManager.getString('accepted'))


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

    if message.text.strip() == stringsManager.getString('notify_command'):
        dataHandler(message)
    else:
        bot.send_message(message.chat.id, stringsManager.getString('unknown_command'))


def start():
    bot.polling(non_stop=True, interval=0)    


if __name__ == "__main__":
    init()
    start()