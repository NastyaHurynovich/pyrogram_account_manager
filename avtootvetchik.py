import configparser
import os
import platform
import sys
import time
from pathlib import Path

from pyrogram.enums import ChatType

from pyrogram import Client
import asyncio

CONFIG_FILE = "./config.ini"


def write_ini(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def delete_journals():
    client_list = list(Path(".").glob("client.session_*"))
    filtered_client_list = list(filter(lambda cl: "journal" in str(cl), client_list))
    for journal in filtered_client_list:
        try:
            os.remove(journal)
        except Exception as exp:
            pass


def getApiDataFromConfig(config_ini):
    try:
        api_id = config_ini["Api"]["id"]
        api_hash = config_ini["Api"]["hash"]
    except Exception:
        print("Ошибка чтения данных Api в конфигурационном файле. Проверьте файл.")
        time.sleep(3)
        sys.exit(1)
    return (api_id, api_hash)


def getApiDataFromUser():
    api_id = input("Введите API ID: ")
    api_hash = input("Введите API Hash: ")
    return (api_id, api_hash)


# Чистим файлы перед началом работы
delete_journals()

config_ini_path = Path(CONFIG_FILE)
config_ini = configparser.ConfigParser()

if config_ini_path.is_file() is not True:
    config_ini["Api"] = {}
    config_ini["Api"]["device"] = platform.node()
    config_ini["Api"]["app_version"] = "1.0.0"
    config_ini["Api"]["system"] = platform.system() + " " + platform.release()
else:
    config_ini.read(CONFIG_FILE)

use_config = int(input("[1] Данные по умолчанию\n[2] Ввести данные вручную\n"
                       "Введите число, соответствующее выбранной опции: "))

if use_config == 1:
    api_id, api_hash = getApiDataFromConfig(config_ini)
elif use_config == 2:
    api_id, api_hash = getApiDataFromUser()
else:
    print("Опции не существует")
    sys.exit(1)

# api_id = "23701050"
# api_hash = "d10b91f22d217030cc9edfaf22f12b68"
if config_ini_path.is_file() is not True:
    config_ini["Api"]["id"] = api_id
    config_ini["Api"]["hash"] = api_hash

write_ini(config_ini)

# Нужный текст для автоответчика
message = input("Введите текст для автоответчика: ")

app = Client("client.session", api_hash=api_hash, api_id=api_id)


@app.on_message()
async def handler(client, bot_message):
    if bot_message.chat.type not in [ChatType.GROUP, ChatType.SUPERGROUP, ChatType.BOT, ChatType.CHANNEL]:
        await asyncio.sleep(3)
        await bot_message.reply(message)
        await asyncio.sleep(10)

app.run()