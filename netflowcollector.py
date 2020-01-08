import argparse
import gzip
import json
import logging
import os
import sys
import time
from collections import defaultdict

from colors import color
import dotenv
import redis

# python-netflow-v9-softflowd expects main.py to be the main entrypoint, but we only need
# get_export_packets() iterator:
sys.path.append(os.path.dirname(os.path.realpath(__file__)) + '/pynetflow')
from pynetflow.main import get_export_packets

from lookup import PROTOCOLS, REDIS_HASH_TRAFFIC_PER_PROTOCOL


logging.basicConfig(format='%(asctime)s | %(levelname)s | %(message)s',
                    datefmt='%Y-%m-%d %H:%M:%S', level=logging.DEBUG)
logging.addLevelName(logging.DEBUG, color("DBG", 7))
logging.addLevelName(logging.INFO, "INF")
logging.addLevelName(logging.WARNING, color('WRN', fg='red'))
logging.addLevelName(logging.ERROR, color('ERR', bg='red'))
log = logging.getLogger("{}.{}".format(__name__, "base"))


REDIS_HOST = os.environ.get('REDIS_HOST', '127.0.0.1')
r = redis.Redis(host=REDIS_HOST)


REDIS_PREFIX = 'netflow'


def process_netflow(netflow_port):
    for ts, client, export in get_export_packets('0.0.0.0', NETFLOW_PORT):
        data = defaultdict(int)
        for flow in export.flows:
            protocol = flow.data['PROTOCOL']
            in_bytes = flow.data['IN_BYTES']

            protocol_str = PROTOCOLS.get(protocol, f'?{protocol}')
            data[protocol_str] += in_bytes

        for k, v in data.items():
            r.hincrby(f'{REDIS_PREFIX}_{REDIS_HASH_TRAFFIC_PER_PROTOCOL}', k, v)


if __name__ == "__main__":
    dotenv.load_dotenv()
    NETFLOW_PORT = int(os.environ.get('NETFLOW_PORT', 2055))
    try:
        process_netflow(NETFLOW_PORT)
    except KeyboardInterrupt:
        log.info("KeyboardInterrupt -> exit")
        pass
