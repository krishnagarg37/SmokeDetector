# -*- coding: utf-8 -*-

import sys
import os
from datetime import datetime
from html.parser import HTMLParser
from html import unescape
from hashlib import md5
from configparser import NoOptionError, RawConfigParser
from helpers import environ_or_none, log
import threading
# noinspection PyCompatibility
import regex
import subprocess as sp
import platform
from flovis import Flovis


def git_commit_info():
    try:
        data = sp.check_output(['git', 'log', '-1', '--pretty=%h%n%H%n%an%n%s'], stderr=sp.STDOUT).decode('utf-8')
    except sp.CalledProcessError as e:
        raise OSError("Git error:\n" + e.output) from e
    short_id, full_id, author, message = data.strip().split("\n")
    return {'id': full_id[:7], 'id_full': full_id, 'author': author, 'message': message}


def git_status():
    try:
        return sp.check_output(['git', 'status'], stderr=sp.STDOUT).decode('utf-8').strip()
    except sp.CalledProcessError as e:
        raise OSError("Git error:\n" + e.output) from e


# This is needed later on for properly 'stripping' unicode weirdness out of git log data.
# Otherwise, we can't properly work with git log data.
def strip_escape_chars(line):
    line = str(line)
    ansi_escape = regex.compile(r'(\x9B|\x1B\[)[0-?]*[ -\/]*[@-~]')
    return ansi_escape.sub('', line).strip('=\r\r\x1b>\n"')


# noinspection PyClassHasNoInit,PyDeprecation,PyUnresolvedReferences
class GlobalVars:
    false_positives = []
    whitelisted_users = []
    blacklisted_users = []
    blacklisted_usernames = []
    blacklisted_websites = []
    bad_keywords = []
    watched_keywords = {}
    ignored_posts = []
    auto_ignored_posts = []
    startup_utc = datetime.utcnow().strftime("%H:%M:%S")
    latest_questions = []
    api_backoff_time = 0
    deletion_watcher = None

    metasmoke_last_ping_time = datetime.now()
    not_privileged_warning = \
        "You are not a privileged user. Please see " \
        "[the privileges wiki page](https://charcoal-se.org/smokey/Privileges) for " \
        "information on what privileges are and what is expected of privileged users."

    experimental_reasons = {  # Don't widely report these
        "potentially bad keyword in answer",
        "potentially bad keyword in body",
        "potentially bad keyword in title",
        "potentially bad keyword in username",
        "potentially bad NS for domain in title",
        "potentially bad NS for domain in body",
        "toxic body detected",
        "toxic answer detected",
    }

    parser = HTMLParser()
    parser.unescape = unescape

    code_privileged_users = None
    censored_committer_names = {"3f4ed0f38df010ce300dba362fa63a62": "Undo1"}

    commit = git_commit_info()
    if md5(commit['author'][0].encode('utf-8')).hexdigest() in censored_committer_names:
        commit['author'] = censored_committer_names[md5(commit['author'][0].encode('utf-8')).hexdigest()]

    commit_with_author = "`{}` (*{}*: {})".format(
        commit['id'],
        commit['author'][0] if type(commit['author']) in {list, tuple} else commit['author'],
        commit['message'])

    on_master = "HEAD detached" not in git_status()

    s = ""
    s_reverted = ""
    apiquota = -1
    bodyfetcher = None
    se_sites = []
    why_data = []
    notifications = []
    listen_to_these_if_edited = []
    multiple_reporters = []
    api_calls_per_site = {}

    standby_message = ""
    standby_mode = False

    api_request_lock = threading.Lock()

    num_posts_scanned = 0
    post_scan_time = 0
    posts_scan_stats_lock = threading.Lock()

    config = RawConfigParser()

    if os.path.isfile('config') and "pytest" not in sys.modules:
        config.read('config')
        log('debug', "Configuration loaded from \"config\"")
    else:
        config.read('config.ci')
        if "pytest" in sys.modules and os.path.isfile('config'):  # Another config found while running in pytest
            log('debug', "Running in pytest, force load config from \"config.ci\"")
        else:
            log('debug', "Configuration loaded from \"config.ci\"")

    # environ_or_none defined in helpers.py
    bot_name = environ_or_none("SMOKEDETECTOR_NAME") or "SmokeDetector"
    bot_repository = environ_or_none("SMOKEDETECTOR_REPO") or "//github.com/Charcoal-SE/SmokeDetector"
    chatmessage_prefix = "[{}]({})".format(bot_name, bot_repository)

    site_id_dict = {}
    post_site_id_to_question = {}

    location = config.get("Config", "location")

    metasmoke_ws = None

    try:
        chatexchange_u = config.get("Config", "ChatExchangeU")
        chatexchange_p = config.get("Config", "ChatExchangeP")
    except NoOptionError:
        chatexchange_u = None
        chatexchange_p = None

    try:
        metasmoke_host = config.get("Config", "metasmoke_host")
    except NoOptionError:
        metasmoke_host = None
        log('info', "metasmoke host not found. Set it as metasmoke_host in the config file. "
            "See https://github.com/Charcoal-SE/metasmoke.")

    try:
        metasmoke_key = config.get("Config", "metasmoke_key")
    except NoOptionError:
        metasmoke_key = ""
        log('info', "No metasmoke key found, which is okay if both are running on the same host")

    try:
        metasmoke_ws_host = config.get("Config", "metasmoke_ws_host")
    except NoOptionError:
        metasmoke_ws_host = ""
        log('info', "No metasmoke websocket host found, which is okay if you're anti-websocket")

    try:
        github_username = config.get("Config", "github_username")
        github_password = config.get("Config", "github_password")
    except NoOptionError:
        github_username = None
        github_password = None

    try:
        perspective_key = config.get("Config", "perspective_key")
    except NoOptionError:
        perspective_key = None

    try:
        flovis_host = config.get("Config", "flovis_host")
    except NoOptionError:
        flovis_host = None

    if flovis_host is not None:
        flovis = Flovis(flovis_host)
    else:
        flovis = None
