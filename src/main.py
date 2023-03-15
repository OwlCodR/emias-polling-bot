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
from bot import token as bot_token
from bot import start
import logging

# Set your tag
admins = []
whitelist = []

# chat.id - user
users = {}

# chat.id - task
tasks = {}

# Set your paths
configPath = 'config.json'

LOGGER_LEVEL = logging.DEBUG
loggerFormat = "%(asctime)s | %(levelname)s\t| %(name)s.%(funcName)s:%(lineno)d | %(id)s | %(message)s "

headers = None
logger = None


def init():
    global logger
    
    headers = {'Content-type': 'application/json'}
    
    with open(configPath) as f:
        d = json.load(f)
        
        bot_token = d['token']
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
        
if __name__ == "__main__":
    init()
    start()