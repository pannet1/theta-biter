"""
description:
    contains all the constants
    creates yml files and necessary folders
    for project
"""

from os import path
from traceback import print_exc
from pprint import pprint
import requests
import json

"""
    description:
        import our  custom logger from toolkit
"""
try:
    from toolkit.logger import Logger
except ModuleNotFoundError:
    __import__("os").system("pip install git+https://github.com/pannet1/toolkit")
    __import__("time").sleep(5)
    from toolkit.logger import Logger

from toolkit.fileutils import Fileutils

O_FUTL = Fileutils()
S_DATA = "../data/"
F_SWITCH = S_DATA + "switch.txt"
S_LOG = S_DATA + "log.txt"
if not O_FUTL.is_file_exists(S_LOG):
    """
    description:
        create data dir and log file
        if did not if file did not exists
    input:
         file name with full path
    """
    print("creating data dir")
    O_FUTL.add_path(S_LOG)


def yml_to_obj(arg=None):
    """
    description:
        creates empty yml file for credentials
        and also copies project specific settings
        to data folder
    """
    if not arg:
        # return the parent folder name
        parent = path.dirname(path.abspath(__file__))
        print(f"{parent=}")
        grand_parent_path = path.dirname(parent)
        print(f"{grand_parent_path=}")
        folder = path.basename(grand_parent_path)
        # reverse the words seperated by -
        lst = folder.split("-")
        file = "_".join(reversed(lst))
        file = "../../" + file + ".yml"
    else:
        file = S_DATA + arg

    flag = O_FUTL.is_file_exists(file)

    if not flag and arg:
        print(f"using default {file=}")
        O_FUTL.copy_file("../", "../data/", "settings.yml")
    elif not flag and arg is None:
        print(f"fill the {file=} file and try again")
        __import__("sys").exit()

    return O_FUTL.get_lst_fm_yml(file)


def read_yml():
    try:
        O_CNFG = yml_to_obj()
        O_SETG = yml_to_obj("settings.yml")
    except Exception as e:
        print(e)
        print_exc()
        __import__("sys").exit(1)
    else:
        return O_CNFG, O_SETG


O_CNFG, O_SETG = read_yml()
print("broker credentials" + "\n" + "*****************")
pprint(O_CNFG)

print("settings " + "\n" + "*****************")
pprint(O_SETG)


def set_logger():
    """
    description:
        set custom logger's log level
        display or write to file
        based on user choice from settings
    """
    level = O_SETG["log"]["level"]
    if O_SETG["log"]["show"] == False:
        return Logger(level)
    return Logger(level, S_LOG)


logging = set_logger()

if not O_FUTL.is_file_exists(F_SWITCH):
    print(f"{F_SWITCH} not found")

with open(F_SWITCH, "w") as f:
    f.write("0")


def send_messages(message):
    try:
        url = "http://localhost:8000/send_message"

        # The message data you want to send in JSON format
        data = {"content": message}

        # Send the POST request with the JSON payload
        requests.post(
            url, headers={"Content-Type": "application/json"}, data=json.dumps(data)
        )

    except Exception as e:
        # Print the response
        print(f"{e} problem in send messages")
