import asyncio
import configparser
import os
import platform
import random
import sys
import time
from pathlib import Path
from random import randint

import yaml
from art import *

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import UsernameNotOccupied, UsernameInvalid
from pyrogram.errors.exceptions.flood_420 import FloodWait, Flood, FloodTestPhoneWait
from pyrogram.types import Dialog

from pyrogram.types import InputMediaPhoto, InputMediaVideo

PATH = "./base.txt"
CLIENTS_SESSIONS_INFO = "./exe_info.yml"
CONFIG_FILE = "./config.ini"
CLIENTS_POOL = []
CLIENTS_LINKS = []
CLIENTS_LOG = {}

# api_id = "23701050"
# api_hash = "d10b91f22d217030cc9edfaf22f12b68"

proxy = {
    "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
    "hostname": "host",
    "port": 8080,
    "username": "username",
    "password": "password"
}


async def get_accounts_from_sessions(api_id, api_hash, proxy, config_yaml, config_ini):
    client_list = list(Path(".").glob("client.session_*"))
    filtered_client_list = list(filter(lambda cl: "journal" not in str(cl), client_list))
    for client_counter in range(1, len(filtered_client_list) + 1):
        await set_client(api_id, api_hash, proxy, client_counter, config_yaml, config_ini)


async def set_client(api_id, api_hash, proxy, name, config_yaml, config_ini):
    try:
        client = Client(f"client.session_{name}", api_hash=api_hash, api_id=api_id,
                        proxy=proxy, device_model=config_ini["Api"]["device"],
                        system_version=config_ini["Api"]["system"] + " v" + config_ini["Api"]["app_version"])
        await client.start()
        if len(config_yaml["clients"]) == 0:
            config_yaml["clients"].append(
                {"id": client.me.id, "handled_autojoiner_counter": 0, "success_autojoiner_counter": 0,
                 "success_spammer_counter": 0, "handled_spammer_counter": 0})
            write_yaml(CLIENTS_SESSIONS_INFO, config_yaml)
        CLIENTS_POOL.append(client)
    except (FloodWait, Flood, FloodTestPhoneWait) as e:
        print(f"Этот аккаунт забанен из-за флуда. Ожидайте {e.value} секунд или попробуйте использовать другой аккаунт")
    except Exception as e:
        print("Ошибка при создании аккаунта: ", e)

        # define our clear function


def clear():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')


def prepare_links(links):
    no_duplicate_links = list()
    for link in links:
        cleaned_link = link.replace("https://t.me/", "").replace("@", "").replace("\n", "")
        if cleaned_link not in no_duplicate_links:
            no_duplicate_links.append(cleaned_link)
    return no_duplicate_links


def read_file(path):
    with open(path, "r") as f:
        links = list(f.readlines())
    return links


def print_current_status(name, count, timer):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print()
    CLIENTS_LOG[name] = [count, timer]

    for key, info in CLIENTS_LOG.items():
        print("Имя/id аккаунта: " + str(key))
        print("Количество вступлений:", info[0])
        print("Ожидание:", info[1], "минут(а/ы)")
        print()


def print_spammer_status(name, count, timer):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print()
    CLIENTS_LOG[name] = [count, timer]

    for key, info in CLIENTS_LOG.items():
        print("Имя/id аккаунта: " + str(key))
        print("Количество отправленных сообщений:", info[0])
        if info[1] is not None:
            print("Ожидание:", info[1], "секунд(а/ы)")
        else:
            print("Ожидание...")
        print()


async def follow_chat(links, app, timer, client_config, yaml_config, ini_config):
    rest_links = links.copy()
    client_name = get_client_name(app)
    for link in links:
        try:
            await app.join_chat(link)
            client_config["success_autojoiner_counter"] += 1
            rest_links.remove(link)
            print_current_status(client_name, client_config["success_autojoiner_counter"], timer)
        except (FloodWait, Flood, FloodTestPhoneWait) as e:
            # Ждем окончание флуда для аккаунта
            print_current_status(client_name, client_config["success_autojoiner_counter"], e.value)
            await asyncio.sleep(e.value)
            await follow_chat(rest_links, app, timer, client_config, yaml_config, ini_config)
            break
        except (UsernameNotOccupied, UsernameInvalid):
            pass
        except:
            print_current_status(client_name, client_config["success_autojoiner_counter"], 10)
            await asyncio.sleep(10)
        ini_config["Settings"]["autojoiner_counter"] = str(int(ini_config["Settings"]["autojoiner_counter"]) + 1)
        write_ini(ini_config)
        client_config["handled_autojoiner_counter"] += 1
        write_yaml(CLIENTS_SESSIONS_INFO, yaml_config)
        if timer > 0:
            await asyncio.sleep(60 * timer)


def write_file(file, link):
    with open(file, "a") as f:
        f.write(f"@{link}\n")


def check_if_all_finish():
    flag = True
    for i in range(0, len(CLIENTS_LINKS)):
        flag = flag and (len(CLIENTS_LINKS[i]) == 0)
    return flag


def read_yaml(path):
    with open(path) as stream:
        try:
            return yaml.load(stream, Loader=yaml.FullLoader)
        except yaml.YAMLError as exc:
            pass
            # print(exc)


def write_yaml(path, config):
    with open(path, 'w') as stream:
        try:
            yaml.dump(config, stream)
        except yaml.YAMLError as exc:
            pass
            # print(exc)


def write_ini(config):
    with open(CONFIG_FILE, 'w') as configfile:
        config.write(configfile)


def get_proxy():
    proxy_mode = int(input("\nПрокси протокол:\n[1] - socks5 \n[2] - https\nВведите число, "
                           "соответствующее выбранной опции: "))
    if proxy_mode == 1:
        proxy["scheme"] = "socks5"
    elif proxy_mode == 2:
        proxy["scheme"] = "https"
    else:
        print("Опции не существует")
        sys.exit(1)
    proxy["hostname"] = input("Введите прокси адрес: ")
    proxy["port"] = int(input("Введите порт: "))
    mode_username = input("\nХотите ввести имя и пароль для прокси? Д/н ")
    if mode_username.lower() == "д":
        proxy["username"] = input("Введите имя аккаунта: ")
        proxy["password"] = input("Введите пароль: ")

    return proxy


def get_command():
    print_logo_and_info("Список команд:")
    command = int(input("[1] - для запуска автоподписчика\n[2] - для запуска рассылки по чатам\nВведите команду: "))
    return command


def getApiDataFromUser():
    api_id = input("Введите API ID: ")
    api_hash = input("Введите API Hash: ")
    return (api_id, api_hash)


def getApiDataFromConfig(config_ini):
    try:
        api_id = config_ini["Api"]["id"]
        api_hash = config_ini["Api"]["hash"]
    except Exception:
        print("Ошибка чтения данных Api в конфигурационном файле. Проверьте файл.")
        time.sleep(3)
        sys.exit(1)
    return (api_id, api_hash)


def edit(text: str) -> str:
    replaces = {"а": "a",
                "у": "y",
                "к": "k",
                "е": "e",
                "н": "H",
                "х": "x",
                "в": "B",
                "п": "n",
                "р": "p",
                "о": "o",
                "с": "c",
                "м": "m",
                "и": "u",
                "т": "T"}
    l = list(replaces.items())
    random.shuffle(l)
    l = l[0:3]
    replaces = dict(l)
    resp = text.translate(str.maketrans(replaces))
    return resp


async def send_message(app: Client, dialog: Dialog, text: str):
    await app.send_message(dialog.chat.id, text)


async def send_media(app: Client, dialog: Dialog, media, mode_edit):
    if media.text is not None:
        if mode_edit is True:
            text = edit(media.text)
        else:
            text = media.text
        await app.send_message(dialog.chat.id, text)
    elif media.photo is not None:
        await app.send_photo(chat_id=dialog.chat.id, photo=media.photo.file_id, caption=media.caption)
    elif media.video is not None:
        await app.send_video(chat_id=dialog.chat.id, video=media.video.file_id, caption=media.caption)


def get_client_name(app):
    if app.me.first_name is not None:
        client_name = app.me.first_name
        if app.me.last_name is not None:
            client_name = app.me.first_name + " " + app.me.last_name
    else:
        client_name = app.me.id
    return client_name


async def spam_1(app, timer, count_chat_for_send, mode_edit, client_config,
                 yaml_config, ini_config):
    client_name = get_client_name(app)
    while True:
        if count_chat_for_send is None:
            try:
                dialogs = [dialog async for dialog in app.get_dialogs() if
                           dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]]
                for dialog in dialogs:
                    inner_timer = timer
                    if type(timer) == list:
                        inner_timer = randint(timer[0], timer[1])
                    try:
                        msg = [message async for message in app.get_chat_history("me", 1)][0]
                    except (FloodWait, Flood, FloodTestPhoneWait) as e:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                        await asyncio.sleep(e.value)
                        continue
                    except:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                        await asyncio.sleep(10)
                        continue
                    try:
                        await send_media(app, dialog, msg, mode_edit)
                        client_config["success_spammer_counter"] += 1
                        ini_config["Settings"]["spammer_counter"] = str(
                            int(ini_config["Settings"]["spammer_counter"]) + 1)
                    except (FloodWait, Flood, FloodTestPhoneWait) as e:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                        await asyncio.sleep(e.value)
                    except:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                        await asyncio.sleep(10)
                    write_ini(ini_config)
                    write_yaml(CLIENTS_SESSIONS_INFO, yaml_config)
                    print_spammer_status(client_name, client_config["success_spammer_counter"], inner_timer)
                    await asyncio.sleep(inner_timer)
            except (FloodWait, Flood, FloodTestPhoneWait) as e:
                print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                await asyncio.sleep(e.value)
            except:
                print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                await asyncio.sleep(10)


async def spam_2(app, timer, count_chat_for_send, mode_edit, client_config,
                 yaml_config, ini_config):
    client_name = get_client_name(app)
    while True:
        if count_chat_for_send is None:
            try:
                dialogs = [dialog async for dialog in app.get_dialogs() if
                           dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]]
                inner_timer = timer
                if type(timer) == list:
                    inner_timer = randint(timer[0], timer[1])
                for dialog in dialogs:
                    try:
                        msg = [message async for message in app.get_chat_history("me", 1)][0]
                    except (FloodWait, Flood, FloodTestPhoneWait) as e:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                        await asyncio.sleep(e.value)
                        continue
                    except:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                        await asyncio.sleep(10)
                        continue
                    try:
                        await send_media(app, dialog, msg, mode_edit)
                        client_config["success_spammer_counter"] += 1
                        ini_config["Settings"]["spammer_counter"] = str(
                            int(ini_config["Settings"]["spammer_counter"]) + 1)
                        await asyncio.sleep(1)
                    except (FloodWait, Flood, FloodTestPhoneWait) as e:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                        await asyncio.sleep(e.value)
                    except:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                        await asyncio.sleep(10)
                    write_ini(ini_config)
                    write_yaml(CLIENTS_SESSIONS_INFO, yaml_config)
                    print_spammer_status(client_name, client_config["success_spammer_counter"], inner_timer)
                await asyncio.sleep(inner_timer)
            except (FloodWait, Flood, FloodTestPhoneWait) as e:
                print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                await asyncio.sleep(e.value)
            except:
                print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                await asyncio.sleep(10)


async def spam_3(app, timer, count_chat_for_send, mode_edit, client_config,
                 yaml_config, ini_config):
    counter = 0
    client_name = get_client_name(app)
    while True:
        if count_chat_for_send is not None:
            try:
                dialogs = [dialog async for dialog in app.get_dialogs() if
                           dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]]
                for dialog in dialogs:
                    if counter >= min(count_chat_for_send, len(dialogs)):
                        inner_timer = timer
                        if type(timer) == list:
                            inner_timer = randint(timer[0], timer[1])
                        counter = 0
                        print_spammer_status(client_name, client_config["success_spammer_counter"], inner_timer)
                        await asyncio.sleep(inner_timer)
                    try:
                        msg = [message async for message in app.get_chat_history("me", 1)][0]
                    except (FloodWait, Flood, FloodTestPhoneWait) as e:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                        await asyncio.sleep(e.value)
                        continue
                    except:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                        await asyncio.sleep(10)
                        continue
                    try:
                        await send_media(app, dialog, msg, mode_edit)
                        client_config["success_spammer_counter"] += 1
                        ini_config["Settings"]["spammer_counter"] = str(
                            int(ini_config["Settings"]["spammer_counter"]) + 1)
                    except (FloodWait, Flood, FloodTestPhoneWait) as e:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                        await asyncio.sleep(e.value)
                    except:
                        print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                        await asyncio.sleep(10)
                    write_ini(ini_config)
                    write_yaml(CLIENTS_SESSIONS_INFO, yaml_config)
                    print_spammer_status(client_name, client_config["success_spammer_counter"], 2)
                    await asyncio.sleep(2)
                    counter += 1
            except (FloodWait, Flood, FloodTestPhoneWait) as e:
                print_spammer_status(client_name, client_config["success_spammer_counter"], e.value)
                await asyncio.sleep(e.value)
            except:
                print_spammer_status(client_name, client_config["success_spammer_counter"], 10)
                await asyncio.sleep(10)


async def exit_on_timer(work_time):
    await asyncio.sleep(work_time * 60)
    print("Программа вышла по таймеру")
    time.sleep(3)
    sys.exit(0)


def delete_journals():
    client_list = list(Path(".").glob("client.session_*"))
    filtered_client_list = list(filter(lambda cl: "journal" in str(cl), client_list))
    for journal in filtered_client_list:
        try:
            os.remove(journal)
        except Exception as exp:
            pass


def print_logo_and_info(info):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print(info)


async def stop_clients():
    for client in CLIENTS_POOL:
        await client.stop()


async def main():
    print_logo_and_info("")

    # Чистим файлы перед началом работы
    delete_journals()

    config_ini_path = Path(CONFIG_FILE)
    config_ini = configparser.ConfigParser()

    if config_ini_path.is_file() is not True:
        config_ini["Api"] = {}
        config_ini["Api"]["device"] = platform.node()
        config_ini["Api"]["app_version"] = "1.0.0"
        config_ini["Api"]["system"] = platform.system() + " " + platform.release()
        config_ini["Settings"] = {"autojoiner_counter": 0, "spammer_counter": 0}
    else:
        config_ini.read(CONFIG_FILE)

    config_yaml_path = Path(CLIENTS_SESSIONS_INFO)

    if config_yaml_path.is_file() is not True:
        config_yaml = {"clients": []}
        config_ini["Settings"] = {"autojoiner_counter": 0, "spammer_counter": 0}
    else:
        config_yaml = read_yaml(config_yaml_path)

    for counter_name in ["autojoiner_counter", "spammer_counter"]:
        if int(config_ini["Settings"][counter_name]) == 0:
            for client in config_yaml["clients"]:
                client["success_" + counter_name] = 0
                if counter_name != "spammer_counter":
                    client["handled_" + counter_name] = 0

    print_logo_and_info("### НАСТРОЙКА API ###")

    use_config = int(input("[1] Данные по умолчанию\n[2] Ввести данные вручную\n"
                           "Введите число, соответствующее выбранной опции: "))

    if use_config == 1:
        api_id, api_hash = getApiDataFromConfig(config_ini)
    elif use_config == 2:
        api_id, api_hash = getApiDataFromUser()
    else:
        print("Опции не существует")
        sys.exit(1)

    if config_ini_path.is_file() is not True:
        config_ini["Api"]["id"] = api_id
        config_ini["Api"]["hash"] = api_hash

    write_ini(config_ini)
    write_yaml(config_yaml_path, config_yaml)

    print_logo_and_info("### НАСТРОЙКА ПРОКСИ ###")

    use_proxy = int(
        input("[1] - Пропустить \n[2] - Подключение через прокси\nВведите число, соответствующее выбранной опции: "))

    if use_proxy == 1:
        proxy = None
    elif use_proxy == 2:
        proxy = get_proxy()
    else:
        print("Опции не существует")
        sys.exit(1)

    command = get_command()

    print()
    print("### Подключение аккаунт(а/ов) ###")

    await get_accounts_from_sessions(api_id, api_hash, proxy, config_yaml, config_ini)
    if len(CLIENTS_POOL) == 0:
        while True:
            await set_client(api_id, api_hash, proxy, len(CLIENTS_POOL) + 1, config_yaml, config_ini)
            answer = input("Хотите ввести ещё один аккаунт? Д/н ")
            if answer.lower() == "н":
                break

    if len(CLIENTS_POOL) == 0:
        print_logo_and_info("Аккаунты для работы не созданы")
        time.sleep(2)
        sys.exit(1)

    print("Подключение к базе данных...")

    if command == 2:
        print_logo_and_info("### ВЫБОР РЕЖИМА ###")
        modes = [spam_1, spam_2, spam_3]
        mode = int(input(
            "[1] - рассылка по 1 чату\n"
            "[2] - рассылка во все чаты\n"
            "[3] - выбрать количество чатов для отправки\nВведите число, соответствующее выбранной опции: "
        ))

        count_chat_for_send = None
        if mode == 3:
            count_chat_for_send = int(input("\nВыберите количество чатов для отправки? "))

        mode_edit = False
        choice_edit = input("\nХотите подключить смену букв? Д/н ")
        if choice_edit.lower() == "д":
            mode_edit = True

        mode_timer = int(input("\nВыберите режим таймера:\n[1] - рандомное\n[2] - фиксированное\nВведите число, "
                               "соответствующее выбранной опции: "))
        if mode_timer == 1:
            timer = []
            timer.append(int(input("Выберите время от: ")))
            timer.append(int(input("Выберите время до: ")))
        else:
            timer = int(input("Выберите время: "))

        work_time = int(
            input("\nТаймер отключения скрипта (минуты). Введите 0, если не хотите завершать программу по таймеру: "))

        tasks = []
        for client in CLIENTS_POOL:
            client_config = next(
                (obj for obj in config_yaml["clients"] if obj["id"] == client.me.id),
                None
            )
            tasks.append(
                asyncio.create_task(modes[int(mode) - 1](client, timer, count_chat_for_send, mode_edit, client_config,
                                                         config_yaml, config_ini)))
            if work_time > 0:
                tasks.append(exit_on_timer(work_time))

        await asyncio.gather(*tasks)

    elif command == 1:
        timer = int(input("Введите время между добавлениями чатов: "))
        links_for_processing = prepare_links(read_file(PATH))
        tasks = []
        for client in CLIENTS_POOL:
            client_config = next(
                (obj for obj in config_yaml["clients"] if obj["id"] == client.me.id),
                None
            )
            already_handled_links_count = client_config["handled_autojoiner_counter"]
            tasks.append(asyncio.create_task(
                follow_chat(links_for_processing[already_handled_links_count:], client, timer, client_config,
                            config_yaml, config_ini)))

        await asyncio.gather(*tasks)

    await stop_clients()
    print_logo_and_info("Работа выполнена!")
    input("Программа завершена введите Enter для завершения: ")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except:
        pass
