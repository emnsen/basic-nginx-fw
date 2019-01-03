#!/usr/bin/env python

import gzip
import json
import os
import sys
import socket
import re
import glob
import subprocess
from datetime import datetime

CLEAN_STATUS = {
    'logs': False,
    'results': False,
    'ips': False
}
ACCESS_LOG_FILE = "/var/log/nginx/<access_log_file_name>.log"
BASE_PATH = os.getcwd()
BOT_AGENTS = [
    'googlebot',
    'google\-sitemaps',
    'feedfetcher\-google',
    'mediapartners\-google',
    'yahoo\-blogs',
    'yahoo\-verticalcrawler',
    'yahoofeedseeker',
    'yahooseeker\-testing',
    'yahooseeker',
    'yahoo\-mmcrawler',
    'yahoo!_mindset',
    'yandex',
    'slurp',
    'msnbot\-media',
    'msnbot',
    'bingbot',
    'adidxbot',
    'bingpreview',
    'duckduckbot',
    'baiduspider'
]
BOT_HOSTS = [
    'google',
    'yahoo',
    'msn',
    'yandex',
    'duckduck'
    'baidu'
    'bing'
]
BOT_AGENT_PATTERNS = [re.compile(BOT_AGENT) for BOT_AGENT in BOT_AGENTS]
BOT_HOST_PATTERNS = [re.compile(BOT_HOST) for BOT_HOST in BOT_HOSTS]
LINE_FORMAT = re.compile(r"""(?P<ipaddress>\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}) - - \[(?P<dateandtime>\d{2}\/[a-z]{3}\/\d{4}:\d{2}:\d{2}:\d{2} (\+|\-)\d{4})\] ((\"(GET|POST) )(?P<url>.+)(http\/1\.1")) (?P<statuscode>\d{3}) (?P<bytessent>\d+) (["](?P<refferer>(\-)|(.+))["]) (["](?P<useragent>.+)["])""", re.IGNORECASE)
REQUEST_PER_MINUTE_LIMIT = 50
REQUEST_COUNTER_INDEX = 0


def is_real_bot(user_agent, ip):
    is_bot = any(BOT_AGENT_PATTERN.search(user_agent.lower()) for BOT_AGENT_PATTERN in BOT_AGENT_PATTERNS)

    if not is_bot:
        return False

    try:
        response = socket.gethostbyaddr(ip)

        is_bot = any(BOT_HOST_PATTERN.search(response[0]) for BOT_HOST_PATTERN in BOT_HOST_PATTERNS)

        if not is_bot:
            return False

        return True
    except Exception:
        return False


def parse_log(file):
    start_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    outstanding_requesters = {'block': {}, 'start_time': start_time}
    result = {}
    num_requests = 0

    # --------------------------------------------------------------------------------------------------------------
    print("[get_outstanding_requesters] \tRead file content")
    # --------------------------------------------------------------------------------------------------------------
    with open(file, 'r') as lines:
        for line in lines:
            line = str(line)
            data = re.search(LINE_FORMAT, line)
            if data:
                datadict = data.groupdict()
                ip = datadict["ipaddress"]
                datetimestring = datadict["dateandtime"]
                url = datadict["url"]
                bytessent = datadict["bytessent"]
                referrer = datadict["refferer"]
                user_agent = datadict["useragent"]
                status = datadict["statuscode"]
                method = data.group(6)
                time_key = datetimestring.rsplit(':', 1)[0]
                request_key = time_key + '-' + ip

                if request_key in result.keys():
                    result[request_key][REQUEST_COUNTER_INDEX] += 1
                else:
                    result[request_key] = [1, 0, user_agent]

                num_requests += 1

    # --------------------------------------------------------------------------------------------------------------
    print("[get_outstanding_requesters] \tKeep only outstanding requesters")
    # --------------------------------------------------------------------------------------------------------------
    now_timestamp_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    for k, v in result.items():
        k = k.split('-')[-1]

        if (REQUEST_PER_MINUTE_LIMIT >= 0 and v[REQUEST_COUNTER_INDEX]) > REQUEST_PER_MINUTE_LIMIT:
            if is_real_bot(v[2], k):
                continue

            if k not in outstanding_requesters['block'].keys() or (
                        outstanding_requesters['block'][k]['max_req_per_min'] < v[REQUEST_COUNTER_INDEX]
            ):
                outstanding_requesters['block'][k] = {
                    'max_req_per_min': v[REQUEST_COUNTER_INDEX],
                    'updated_at': now_timestamp_str
                }

    outstanding_requesters['total_requests'] = num_requests

    finish_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    outstanding_requesters['finish_time'] = finish_time

    result_file = "{}/results/{}.json".format(BASE_PATH, file.replace('{}/logs/'.format(BASE_PATH), ''))
    with open(result_file, 'w') as outfile:
        json.dump(outstanding_requesters, outfile, sort_keys=True, indent=4)


def create_dir(dir_name):
    if not os.path.exists(dir_name):
        os.makedirs(dir_name)


def write_ips(date_time):
    ips = []
    results = "{}/results/*.json".format(BASE_PATH)

    for file in glob.glob(results):
        with open(file) as data:
            d = json.load(data)
            [ips.append(v) for v in d['block'].keys()]

    ips_file = "{}/ips/{}.ips".format(BASE_PATH, date_time)
    with open(ips_file, "a") as f:
        [f.write("{} \n".format(ip)) for ip in ips]

    return ips_file


if __name__ == '__main__':
    DATE_TIME = datetime.now().strftime("%Y-%m-%d-%H-%M")
    create_dir('{}/ips'.format(BASE_PATH))
    create_dir('{}/logs'.format(BASE_PATH))
    create_dir('{}/results'.format(BASE_PATH))

    logfilter_file = "{}/logfilter.sh".format(BASE_PATH)
    logfilter_log_file = "{}/logs/{}.log".format(BASE_PATH, DATE_TIME)
    subprocess.call([logfilter_file, logfilter_log_file, ACCESS_LOG_FILE])

    logs = "{}/logs/*.log".format(BASE_PATH)
    files = glob.glob(logs)
    for file in files:
        parse_log(file)

    ips_files = write_ips(DATE_TIME)

    run_file = "{}/run.sh".format(BASE_PATH)
    subprocess.call([run_file, ips_files])

    if CLEAN_STATUS['logs']:
        FILES = "{}/logs/*.log".format(BASE_PATH)
        [os.remove(file) for file in glob.glob(FILES)]

    if CLEAN_STATUS['results']:
        LOGS_DIR = "{}/results/*.json".format(BASE_PATH)
        [os.remove(file) for file in glob.glob(LOGS_DIR)]

    if CLEAN_STATUS['ips']:
        LOGS_DIR = "{}/ips/*.ips".format(BASE_PATH)
        [os.remove(file) for file in glob.glob(LOGS_DIR)]
