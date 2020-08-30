#!/usr/bin/env python

""" Like tweets
"""

import argparse
import json
import logging
import queue
import random
import string
import threading
import time

import tweepy

from listener import Listener

logger = logging.getLogger(__name__)
logging.basicConfig(
    format='%(asctime)s %(levelname)-8s %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S',
    level=logging.INFO)


def get_args():
    """Parse user args, get config file path"""
    parser = argparse.ArgumentParser(description='NeedNewMusicBot app')
    parser.add_argument('config_filename', help='Path to config JSON file.')
    parser.add_argument('phrases_filename', help='Phrases to look for')
    parser.add_argument('-w', '--wait_time', help='Seconds to wait', type=int, default=301)
    return parser.parse_args()


def log_exception(exc):
    logger.warning('Exception: %s, type %s', str(exc), type(exc))


def load_auth_config(config_fname):
    """Read the config file and parse the JSON"""
    with open(config_fname, 'r') as config_file:
        return json.load(config_file)


def action_loop(api, action_queue, wait_time):

    while True:
        status = action_queue.get(block=True)

        try:
            api.retweet(status.id)
            logger.info('Retweeted: %s', status.text)
        except Exception as exc:
            log_exception(exc)
        
        time.sleep(wait_time)


def get_api(config_filename):
    config = load_auth_config(config_filename)
    auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
    auth.set_access_token(config['access_token'], config['access_token_secret'])
    return tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True), auth


def run(api, auth, phrases_fname, action_queue):
    """Run the main logic"""
    listener = Listener(api, phrases_fname, action_queue)
    stream = tweepy.Stream(auth, listener)
    stream.filter(track=['need new music', 'need new tunes', 'send new music'])


def main():
    """Main app outer loop"""
    args = get_args()
    api, auth = get_api(args.config_filename)
    action_queue = queue.LifoQueue()

    threading.Thread(target=action_loop, args=(
        api,
        action_queue,
        args.wait_time)).start()

    # Keep the app running when it periodically hangs
    while True:
        try:
            run(api, auth, args.phrases_filename, action_queue)
        except Exception as exc:
            log_exception(exc)
            time.sleep(args.wait_time)


if __name__ == '__main__':
    main()
