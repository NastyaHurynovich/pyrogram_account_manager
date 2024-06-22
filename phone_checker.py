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
from pyrogram.errors import UsernameNotOccupied, UsernameInvalid
from pyrogram.errors.exceptions.flood_420 import FloodWait, Flood, FloodTestPhoneWait
from pyrogram.types import InputPhoneContact

LINKS_FOR_PROCESSING_PATH = "./base.txt"
VALID_NUMBERS = "существующие номера.txt"
VALID_LINKS = "существующие ссылки.txt"
All_HANDLE_LINKS = "проверенные ссылки.txt"
ALL_HANDLE_NUMBERS = "проверенные номера.txt"
CLIENTS_SESSIONS_INFO = "./exe_info.yml"
ERRORS_LOG = "errors.txt"
CONFIG_FILE = "./config.ini"
CLIENTS_POOL = []
BANNED_ACCOUNTS = []
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


def print_status(name, count, timer):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print()
    CLIENTS_LOG[name] = [count, timer]

    for key, info in CLIENTS_LOG.items():
        print("Имя/id аккаунта: " + str(key))
        print("Количество проверенных номеров/ссылок:", info[0])
        if info[1] is not None:
            print("Ожидание:", info[1], "секунд(а/ы)")
        else:
            print("Ожидание...")
        print()


def get_accounts_from_sessions(api_id, api_hash, proxy, config_yaml, config_ini):
    client_list = list(Path(".").glob("client.session_*"))
    filtered_client_list = list(filter(lambda cl: "journal" not in str(cl), client_list))
    for client_counter in range(1, len(filtered_client_list) + 1):
        set_client(api_id, api_hash, proxy, client_counter, config_yaml, config_ini)


def set_client(api_id, api_hash, proxy, name, config_yaml, config_ini):
    try:
        client = Client(f"client.session_{name}", api_hash=api_hash, api_id=api_id,
                        proxy=proxy, device_model=config_ini["Api"]["device"],
                        system_version=config_ini["Api"]["system"] + " v" + config_ini["Api"]["app_version"])
        client.start()
        if len(config_yaml["clients"]) == 0:
            config_yaml["clients"].append(
                {"id": client.me.id, "handled_links_validator_counter": 0, "success_links_validator_counter": 0,
                 "handled_phones_validator_counter": 0, "success_phones_validator_counter": 0})
            write_yaml(CLIENTS_SESSIONS_INFO, config_yaml)
        CLIENTS_POOL.append(client)
        BANNED_ACCOUNTS.append(-1)
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
    proxy_mode = int(input("\nПрокси протокол:\n[1] - socks5 \n[2] - http\nВведите число, "
                           "соответствующее выбранной опции: "))
    if proxy_mode == 1:
        proxy["scheme"] = "socks5"
    elif proxy_mode == 2:
        proxy["scheme"] = "http"
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
    command = int(input("[1] - чекер по номерам телефонов\n[2] - чекер по чатам\nВведите команду: "))
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


def check_active_chat(links, pool_number, criteria, period, yaml_config, ini_config):
    print_logo_and_info("")
    errors_links = []
    links_handled_per_client = 0
    curr_client = CLIENTS_POOL[pool_number]
    client_name = get_client_name(curr_client)
    client_config = next(
        (obj for obj in yaml_config["clients"] if obj["id"] == curr_client.me.id),
        None
    )
    for link in links:
        links_handled_per_client += 1
        # Меняем аккаунт каждые 20 каналов из списка или когда встречаем бан за Flood, а также если больше одного
        # аккаунта
        if links_handled_per_client >= 20 and len(CLIENTS_POOL) > 1:
            index = get_not_banned_account(pool_number)
            if index > -1:
                links_handled_per_client = 0
                curr_client = CLIENTS_POOL[index]
                pool_number = index
        try:
            is_valid = check_criteria(curr_client, link, criteria, period)
            if is_valid:
                client_config["success_links_validator_counter"] += 1
                write_file(VALID_LINKS, "@" + link)
            client_config["handled_links_validator_counter"] += 1
        except (FloodWait, Flood, FloodTestPhoneWait) as e:
            BANNED_ACCOUNTS[pool_number] = datetime.now(tz=timezone.utc).timestamp() + e.value + 100
            new_account_index = get_not_banned_account(pool_number)
            if new_account_index > -1:
                curr_client = CLIENTS_POOL[new_account_index]
                pool_number = new_account_index
            else:
                # Не забаненых клиентов не найдено - ждем
                first_on_release = get_sooner_unbanned_account()
                waiting_time = int(BANNED_ACCOUNTS[first_on_release] - datetime.now(tz=timezone.utc).timestamp())
                if waiting_time > 0:
                    print_status(client_name,  ini_config["Settings"]["links_validator_counter"], waiting_time)
                    time.sleep(waiting_time)
                BANNED_ACCOUNTS[first_on_release] = -1
                curr_client = CLIENTS_POOL[first_on_release]
                pool_number = first_on_release
            errors_links.append(link)
            continue
        except (UsernameNotOccupied, UsernameInvalid):
            client_config["handled_links_validator_counter"] += 1
            pass
        except Exception as e:
            errors_links.append(link)
            write_file(ERRORS_LOG, "@" + link)
            write_file(ERRORS_LOG, traceback.format_exc())
            print_status(client_name, ini_config["Settings"]["links_validator_counter"], 25)
            time.sleep(25)
            continue
        except:
            errors_links.append(link)
            print_status(client_name, ini_config["Settings"]["links_validator_counter"], 25)
            time.sleep(25)
            continue
        # Симулируем поведение человека, ждем 10 секунд перед обработкой следующей ссылки
        write_file(All_HANDLE_LINKS, "@" + link)
        ini_config["Settings"]["links_validator_counter"] = str(
            int(ini_config["Settings"]["links_validator_counter"]) + 1)
        print_status(client_name, ini_config["Settings"]["links_validator_counter"], 7)
        write_ini(ini_config)
        write_yaml(CLIENTS_SESSIONS_INFO, yaml_config)
        time.sleep(7)

    return errors_links


def check_by_phone_number(begin_number, end_number, pool_number, country_code, operator_code, yaml_config, ini_config):
    print_logo_and_info("")
    app = CLIENTS_POOL[pool_number]
    phones_handled_per_client = 0
    client_name = get_client_name(app)
    client_config = next(
        (obj for obj in yaml_config["clients"] if obj["id"] == app.me.id),
        None
    )
    for i in range(begin_number, end_number):
        phones_handled_per_client += 1
        if phones_handled_per_client >= 20 and len(CLIENTS_POOL) > 1:
            index = get_not_banned_account(pool_number)
            if index > -1:
                phones_handled_per_client = 0
                app = CLIENTS_POOL[index]
                pool_number = index
        phone_number = str(i).zfill(7)
        full_phone_number = str(country_code) + str(operator_code) + str(phone_number)
        try:
            contacts = app.import_contacts([InputPhoneContact("+" + full_phone_number, full_phone_number)])
            if len(contacts.users) > 0:
                id = contacts.users[0].id
                username = "@" + contacts.users[0].username if contacts.users[0].username is not None else contacts.users[
                                                                                                         0].first_name + " " + \
                                                                                                     contacts.users[
                                                                                                         0].last_name
                client_config["success_phones_validator_counter"] += 1
                write_file(VALID_NUMBERS, "ID: " + str(id) + " имя: " + username + " телефон: " + full_phone_number)
            client_config["handled_phones_validator_counter"] += 1
        except (FloodWait, Flood, FloodTestPhoneWait) as e:
            BANNED_ACCOUNTS[pool_number] = datetime.now(tz=timezone.utc).timestamp() + e.value + 100
            new_account_index = get_not_banned_account(pool_number)
            if new_account_index > -1:
                check_by_phone_number(i, end_number, new_account_index, country_code, operator_code, yaml_config,
                                             ini_config)
                break
            else:
                # Не забаненых клиентов не найдено - ждем
                first_on_release = get_sooner_unbanned_account()
                waiting_time = int(BANNED_ACCOUNTS[first_on_release] - datetime.now(tz=timezone.utc).timestamp())
                if waiting_time > 0:
                    print_status(client_name, ini_config["Settings"]["phones_validator_counter"], waiting_time)
                    time.sleep(waiting_time)
                BANNED_ACCOUNTS[first_on_release] = -1
                check_by_phone_number(i, end_number, first_on_release, country_code, operator_code, yaml_config,
                                      ini_config)
                break
        except Exception as e:
            write_file(ERRORS_LOG, full_phone_number)
            write_file(ERRORS_LOG, traceback.format_exc())
            print_status(client_name, ini_config["Settings"]["phones_validator_counter"], 25)
            time.sleep(25)
        except:
            print_status(client_name, ini_config["Settings"]["phones_validator_counter"], 25)
            time.sleep(25)
        write_file(ALL_HANDLE_NUMBERS, "Аккаунт с телефоном " + full_phone_number + " проверен")
        ini_config["Settings"]["phones_validator_counter"] = str(
            int(ini_config["Settings"]["phones_validator_counter"]) + 1)
        print_status(client_name, ini_config["Settings"]["phones_validator_counter"], 7)
        write_ini(ini_config)
        write_yaml(CLIENTS_SESSIONS_INFO, yaml_config)
        time.sleep(7)


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


def get_client_name(app):
    if app.me.first_name is not None:
        client_name = app.me.first_name
        if app.me.last_name is not None:
            client_name = app.me.first_name + " " + app.me.last_name
    else:
        client_name = app.me.id
    return client_name


def delete_journals():
    client_list = list(Path(".").glob("client.session_*"))
    filtered_client_list = list(filter(lambda cl: "journal" in str(cl), client_list))
    for journal in filtered_client_list:
        try:
            os.remove(journal)
        except Exception as exp:
            pass


def print_logo_and_info(text):
    clear()
    tprint("{:>30}".format("Dragen SOFT"))
    print(text)


def stop_clients():
    for client in CLIENTS_POOL:
        client.stop()


def main():
    try:
        os.remove(VALID_NUMBERS)
    except OSError:
        pass
    try:
        os.remove(ALL_HANDLE_NUMBERS)
    except OSError:
        pass
    try:
        os.remove(All_HANDLE_LINKS)
    except OSError:
        pass
    try:
        os.remove(VALID_LINKS)
    except OSError:
        pass

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
        config_ini["Settings"] = {"links_validator_counter": 0, "phones_validator_counter": 0}
    else:
        config_ini.read(CONFIG_FILE)

    config_yaml_path = Path(CLIENTS_SESSIONS_INFO)

    if config_yaml_path.is_file() is not True:
        config_yaml = {"clients": []}
        config_ini["Settings"] = {"links_validator_counter": 0, "phones_validator_counter": 0}
    else:
        config_yaml = read_yaml(config_yaml_path)

    for counter_name in ["phones_validator_counter", "links_validator_counter"]:
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
            set_client(api_id, api_hash, proxy, len(CLIENTS_POOL) + 1, config_yaml, config_ini)
            answer = input("Хотите ввести ещё один аккаунт? Д/н ")
            if answer.lower() == "н":
                break

    if len(CLIENTS_POOL) == 0:
        print_logo_and_info("Аккаунты для работы не созданы")
        time.sleep(2)
        sys.exit(1)

    print("Подключение к базе данных...")

    if command == 1:
        print_logo_and_info("### НАСТРОЙКА РЕЖИМА ###")
        country_code = input("Введите код страны: ")
        operator_code = input("Введите код оператора: ")
        begin_number = int(input("Введите начальный номер: "))
        end_number = int(input("Введите конечный номер: "))
        # 7625816, 7625818
        check_by_phone_number(begin_number, end_number, 0, country_code, operator_code, config_yaml, config_ini)

    elif command == 2:
        print_logo_and_info("### НАСТРОЙКА РЕЖИМА ###")
        count_criteria = request_int("Введите количество сообщений для проверки 'активности' канала? ")
        period = request_int("Введите количество часов, за которые просматриваются сообщения и проверятся 'активность' "
                             "каналов? ")
        links_for_processing = prepare_links(read_file(LINKS_FOR_PROCESSING_PATH))
        while True:
            error_links = check_active_chat(links_for_processing, 0, count_criteria, period, config_yaml,
                                            config_ini)
            if len(error_links) == 0:
                break
            links_for_processing = error_links

    stop_clients()

    input("Программа завершена введите Enter для завершения: ")


if __name__ == '__main__':
    main()
