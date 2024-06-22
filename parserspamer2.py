import configparser
import os
import platform
import sys
import time
import traceback
from datetime import datetime, timezone, timedelta
from pathlib import Path

import yaml
from art import *

from pyrogram import Client
from pyrogram.enums import ChatType
from pyrogram.errors import UsernameNotOccupied, UsernameInvalid
from pyrogram.errors.exceptions.flood_420 import FloodWait, Flood, FloodTestPhoneWait
from pyrogram.types import InputPhoneContact

PATH = "./base.txt"
VALID_LINK = "существующие ссылки.txt"
All_HANDLE_LINK = "проверенные ссылки.txt"
All_HANDLE_CHAT = "проверенные чаты"
CLIENTS_SESSIONS_INFO = "./exe_info.yml"
CONFIG_FILE = "./config.ini"
CLIENTS_POOL = []
BANNED_ACCOUNTS = []
CLIENTS_LINKS = []
MEMBERS_FILE = "user.txt"

CLIENTS_LOG = {}
STATUS = {"1": "ONLINE",
          "2": "RECENTLY",
          "3": "LAST_WEEK",
          "4": "ALL"}

# api_id = "23701050"
# api_hash = "d10b91f22d217030cc9edfaf22f12b68"

proxy = {
    "scheme": "socks5",  # "socks4", "socks5" and "http" are supported
    "hostname": "host",
    "port": 8080,
    "username": "username",
    "password": "password"
}


def get_accounts_from_sessions(api_id, api_hash, proxy, clients_info_config, config):
    client_list = list(Path(".").glob("client.session_*"))
    filtered_client_list = list(filter(lambda cl: "journal" not in str(cl), client_list))
    for client_counter in range(1, len(filtered_client_list) + 1):
        set_client(api_id, api_hash, proxy, client_counter, clients_info_config, False, config)


def set_client(api_id, api_hash, proxy, name, clients_info_config, write_in_yaml, config):
    try:
        client = Client(f"client.session_{name}", api_hash=api_hash, api_id=api_id,
                        proxy=proxy, device_model=config["Api"]["device"],
                        system_version=config["Api"]["system"] + " v" + config["Api"]["app_version"])
        client.start()
        if write_in_yaml or len(clients_info_config["clients"]) == 0:
            clients_info_config["clients"].append(
                {"id": client.me.id, "handled_links_validator_counter": 0, "success_links_validator_counter": 0,
                 "handled_chat_validator_counter": 0,
                 "success_chat_validator_counter": 0})
            write_yaml(CLIENTS_SESSIONS_INFO, clients_info_config)
        CLIENTS_POOL.append(client)
        BANNED_ACCOUNTS.append(-1)

    except (FloodWait, Flood, FloodTestPhoneWait) as e:
        print(f"Этот аккаунт забанен из-за флуда. Ожидайте {e.value} секунд или попробуйте использовать другой аккаунт")
    except Exception as e:
        print("Ошибка при создании аккаунта: ", e)


def print_status(name, count, timer):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print()
    CLIENTS_LOG[name] = [count, timer]

    for key, info in CLIENTS_LOG.items():
        print("Имя/id аккаунта: " + str(key))
        print("Количество проверенных ссылок:", info[0])
        if info[1] is not None:
            print("Ожидание:", info[1], "секунд(а/ы)")
        else:
            print("Ожидание...")
        print()


def print_parse_status(name, count, timer):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print()
    CLIENTS_LOG[name] = [count, timer]

    for key, info in CLIENTS_LOG.items():
        print("Имя/id аккаунта: " + str(key))
        print("Количество проверенных чатов:", info[0])
        if info[1] is not None:
            print("Ожидание:", info[1], "секунд(а/ы)")
        else:
            print("Ожидание...")
        print()


# define our clear function
def clear():
    # for windows
    if os.name == 'nt':
        _ = os.system('cls')

    # for mac and linux(here, os.name is 'posix')
    else:
        _ = os.system('clear')


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
    command = int(input("[1] - запуск парсера\n[2] - запуск спамера по ЛС\nВведите команду: "))
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
        print_logo_and_info("Ошибка чтения данных Api в конфигурационном файле. Проверьте файл.")
        time.sleep(3)
        sys.exit(1)
    return (api_id, api_hash)


def get_not_banned_account(start_position):
    position = start_position
    t_index = 0
    non_ban_exist = False
    while t_index < len(BANNED_ACCOUNTS):
        if BANNED_ACCOUNTS[t_index] < datetime.now(tz=timezone.utc).timestamp():
            BANNED_ACCOUNTS[t_index] = -1
            non_ban_exist = non_ban_exist or True
        t_index += 1
    if non_ban_exist:
        if len(BANNED_ACCOUNTS) - 1 <= position:
            position = 0
        else:
            position += 1
        while BANNED_ACCOUNTS[position] > 0:
            position += 1
        return position
    return -1


def get_sooner_unbanned_account():
    sooner = 922337203685477580
    index = 0
    idx = 0
    for account_unbanned_time in BANNED_ACCOUNTS:
        if -1 < account_unbanned_time < sooner:
            sooner = account_unbanned_time
            index = idx
        idx += 1
    return index


def write_file(file, data):
    with open(file, "a", encoding='utf-8') as f:
        f.write(f"{data}\n")


def request_int(string):
    return int(input(string))


def read_file(path):
    with open(path, "r") as f:
        links = set(f.readlines())
    return links


def prepare_links(links):
    no_duplicate_links = list()
    for link in links:
        cleaned_link = link.replace("https://t.me/", "").replace("@", "").replace("\n", "")
        if cleaned_link not in no_duplicate_links:
            no_duplicate_links.append(cleaned_link)
    return no_duplicate_links


def check_criteria(pool_client, link, criteria, period):
    messages = list(
        pool_client.get_chat_history(chat_id=link, limit=(1 if criteria == 0 else criteria),
                                     offset_date=datetime.now(tz=timezone.utc)))
    if len(messages) > 0:
        last_message = messages[-1]
        return (last_message.date.timestamp() >= (
                datetime.now(tz=timezone.utc) - timedelta(hours=period)).timestamp()) or \
               (criteria == 0 and period == 0)
    return criteria == 0


def get_chat_members(links, pool_number, status_members, yaml_config, ini_config):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print()
    curr_client = CLIENTS_POOL[pool_number]
    client_config = next(
        (obj for obj in yaml_config["clients"] if obj["id"] == curr_client.me.id),
        None
    )
    if curr_client.me.first_name is not None:
        client_name = curr_client.me.first_name
        if curr_client.me.last_name is not None:
            client_name = curr_client.me.first_name + " " + curr_client.me.last_name
        else:
            client_name = curr_client.me.id
    errors_links = []
    links_handled_per_client = 0
    for link in links:
        links_handled_per_client += 1
        # Меняем аккаунт каждые 20 каналов из списка или когда встречаем бан за Flood, а также если больше одного
        # аккаунта
        if links_handled_per_client >= 5 and len(CLIENTS_POOL) > 1:
            index = get_not_banned_account(pool_number)
            if index > -1:
                print("Смена аккаунта. ", CLIENTS_POOL[index].phone_number)
                links_handled_per_client = 0
                curr_client = CLIENTS_POOL[index]
                pool_number = index
        try:
            for member in curr_client.get_chat_members(link):
                if member.user.is_bot is not True and (
                        status_members.lower() == member.user.status.value.lower() or status_members == "ALL"):
                    member_id = member.user.id
                    member_username = "<Нет имени>"
                    if member.user.username is not None:
                        member_username = member.user.username
                    write_file(MEMBERS_FILE, f"Участник чата {link}: @{member_username} - {member_id}")

        except (FloodWait, Flood, FloodTestPhoneWait) as e:
            print(f"Аккаунт был забанен за флуд. Время ожидания окончания блокировки аккаунта {e.value} секунд")
            BANNED_ACCOUNTS[pool_number] = datetime.now(tz=timezone.utc).timestamp() + e.value + 100
            new_account_index = get_not_banned_account(pool_number)
            if new_account_index > -1:
                print("Продолжаем работу с другим аккаунтом")
                curr_client = CLIENTS_POOL[new_account_index]
                pool_number = new_account_index
            else:
                # Не забаненых клиентов не найдено - ждем
                first_on_release = get_sooner_unbanned_account()
                waiting_time = int(BANNED_ACCOUNTS[first_on_release] - datetime.now(tz=timezone.utc).timestamp())
                if waiting_time > 0:
                    print("Ожидание разблокировки...")
                    time.sleep(waiting_time)
                BANNED_ACCOUNTS[first_on_release] = -1
                curr_client = CLIENTS_POOL[first_on_release]
                pool_number = first_on_release
            errors_links.append(link)
        except (UsernameNotOccupied, UsernameInvalid):
            print("@" + link, ": невалидная ссылка")
        except:
            print_parse_status(client_name, client_config["success_chat_validator_counter"], 25)
            time.sleep(25)
        # Симулируем поведение человека, ждем 10 секунд перед обработкой следующей ссылки
        client_config["success_links_validator_counter"] += 1
        client_config["handled_links_validator_counter"] += 1
        print_status(client_name, client_config["handled_links_validator_counter"], 7)
        write_file(All_HANDLE_LINK, link)
        ini_config["Settings"]["links_validator_counter"] = str(
            int(ini_config["Settings"]["links_validator_counter"]) + 1)
        write_ini(ini_config)
        write_yaml(CLIENTS_SESSIONS_INFO, yaml_config)
        time.sleep(7)

    return errors_links


def get_chat_members_by_chat_id(client, status_members, yaml_config, ini_config):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print()
    if client.me.first_name is not None:
        client_name = client.me.first_name
        if client.me.last_name is not None:
            client_name = client.me.first_name + " " + client.me.last_name
        else:
            client_name = client.me.id
    client_config = next(
        (obj for obj in yaml_config["clients"] if obj["id"] == client.me.id),
        None
    )
    dialogs = [dialog for dialog in client.get_dialogs() if
               dialog.chat.type in [ChatType.GROUP, ChatType.SUPERGROUP]]
    for dialog in dialogs:
        try:
            for member in client.get_chat_members(chat_id=dialog.chat.id):
                if member.user.is_bot is not True and (
                        status_members.lower() == member.user.status.value.lower() or status_members == "ALL"):
                    member_id = member.user.id
                    if member.user.username is None:
                        member_username = "<Нет имени>"
                    else:
                        member_username = member.user.username
                    write_file(MEMBERS_FILE,
                               f"Участник чата {dialog.chat.title} ({dialog.chat.id}): {member_username} - {member_id}")
        except (FloodWait, Flood, FloodTestPhoneWait) as e:
            print_parse_status(client_name, client_config["success_chat_validator_counter"], e.value)
            time.sleep(e.value)
        except:
            print_parse_status(client_name, client_config["success_chat_validator_counter"], 25)
            time.sleep(25)
        client_config["success_chat_validator_counter"] += 1
        client_config["handled_chat_validator_counter"] += 1
        print_parse_status(client_name, client_config["handled_chat_validator_counter"], 7)
        write_file(All_HANDLE_CHAT, dialog.chat.title)
        ini_config["Settings"]["chat_validator_counter"] = str(
            int(ini_config["Settings"]["chat_validator_counter"]) + 1)
        write_ini(ini_config)
        write_yaml(CLIENTS_SESSIONS_INFO, yaml_config)
        time.sleep(7)


def delete_journals():
    client_list = list(Path(".").glob("client.session_*"))
    filtered_client_list = list(filter(lambda cl: "journal" in str(cl), client_list))
    for journal in filtered_client_list:
        try:
            os.remove(journal)
        except Exception as exp:
            pass


def clean_up_files(files):
    for file in files:
        try:
            os.remove(file)
        except OSError:
            pass


def print_logo_and_info(info):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print(info)


def main():
    print_logo_and_info("")

    # Чистим файлы перед началом работы
    clean_up_files([VALID_LINK])
    delete_journals()

    config_ini_path = Path(CONFIG_FILE)
    config_ini = configparser.ConfigParser()

    if config_ini_path.is_file() is not True:
        config_ini["Api"] = {}
        config_ini["Api"]["device"] = platform.node()
        config_ini["Api"]["app_version"] = "1.0.0"
        config_ini["Api"]["system"] = platform.system() + " " + platform.release()
        config_ini["Settings"] = {"links_validator_counter": 0, "chat_validator_counter": 0}
    else:
        config_ini.read(CONFIG_FILE)

    config_yaml_path = Path(CLIENTS_SESSIONS_INFO)

    if config_yaml_path.is_file() is not True:
        config_yaml = {"clients": []}
        config_ini["Settings"] = {"links_validator_counter": 0, "chat_validator_counter": 0}
    else:
        config_yaml = read_yaml(config_yaml_path)

    for counter_name in ["links_validator_counter", "chat_validator_counter"]:
        if int(config_ini["Settings"][counter_name]) == 0:
            for client in config_yaml["clients"]:
                client["success_" + counter_name] = 0
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
    get_accounts_from_sessions(api_id, api_hash, proxy, config_yaml, config_ini)
    if len(CLIENTS_POOL) == 0:
        while True:
            set_client(api_id, api_hash, proxy, len(CLIENTS_POOL) + 1, config_yaml, True, config_ini)
            answer = input("Хотите ввести ещё один аккаунт? Д/н ")
            if answer.lower() == "н":
                break

    if len(CLIENTS_POOL) == 0:
        print("Аккаунты для работы не созданы")
        sys.exit(1)

    print("Подключение к базе данных...")

    if command == 1:
        clear()
        tprint("{:>30}".format("Dragen SOFT"))
        print()

        print("### НАСТРОЙКА РЕЖИМА ###")
        mode = int(
            input("[1] - Хотите ввести список чатов?\n[2] - Хотите работать с чатами на вашем "
                  "аккаунте?\n"))
        status_members = input("\nКого вывести в список?\n1 - Пользователи онлайн\n2 - Были в сети недавно\n3 - Были в "
                               "сети менее 7 дней назад\n4 - Все пользователи группы\n")
        if mode == 1:
            links_for_processing = prepare_links(read_file(PATH))
            already_handled_links_count = config_yaml["clients"][0]["handled_links_validator_counter"]
            while True:
                error_links = get_chat_members(links_for_processing[already_handled_links_count:], 0,
                                               STATUS[status_members], config_yaml, config_ini)
                if len(error_links) == 0:
                    break
                links_for_processing = error_links
        elif mode == 2:
            for client in CLIENTS_POOL:
                get_chat_members_by_chat_id(client, STATUS[status_members], config_yaml, config_ini)

    for client in CLIENTS_POOL:
        client.stop()

    input("Программа завершена введите Enter для завершения: ")


if __name__ == '__main__':
    main()
