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
import logging

# Set token from outside
token = None
bot = telebot.TeleBot(token, parse_mode=None)

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