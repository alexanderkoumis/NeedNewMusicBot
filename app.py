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

WHITELISTED_ERRORS_LOOP = [
    'No status found with that ID',
]

WHITELISTED_ERRORS_MAIN = [
    'No status found with that ID',
    'Connection reset by peer'
]


def get_args():
    """Parse user args, get config file path"""
    parser = argparse.ArgumentParser(description='NeedNewMusicBot app')
    parser.add_argument('config_filename', help='Path to config JSON file.')
    parser.add_argument('phrases_filename', help='Phrases to look for')
    parser.add_argument('-w', '--wait_time', help='Seconds to wait', type=int, default=301)
    return parser.parse_args()

def load_auth_config(config_fname):
    """Read the config file and parse the JSON"""
    with open(config_fname, 'r') as config_file:
        return json.load(config_file)

def action_loop(api, action_queue, wait_time):
    logger.info('Launching action_loop')
    while True:
        try:
            time.sleep(wait_time)

            if action_queue.empty():
                continue

            status = action_queue.get()
            api.retweet(status.id)
            logger.info(f'Liked Tweet: {status.text}')

            reply_text = generate_reply_text(links_fname, tweet_message)
        except Exception as exc:
            if is_exception_whitelisted(WHITELISTED_ERRORS_LOOP, exc):
                logger.warning(f'Whitelisted error in start_like_loop, ignoring: {str(exc)}')
                continue
            raise


def get_api(config_filename):
    config = load_auth_config(config_filename)
    auth = tweepy.OAuthHandler(config['consumer_key'], config['consumer_secret'])
    auth.set_access_token(config['access_token'], config['access_token_secret'])
    return tweepy.API(auth, wait_on_rate_limit=True, wait_on_rate_limit_notify=True), auth


def run(api, auth, phrases_fname, action_queue):
    """Run the main logic"""
    listener = Listener(api, phrases_fname, action_queue)
    stream = tweepy.Stream(auth, listener)
    stream.filter(track=['need new music'])


def is_exception_whitelisted(whitelisted_errors, exception):
    for whitelisted_error in whitelisted_errors:
        if whitelisted_error in str(exception):
            return True
    return False


def main():
    """Main app outer loop"""
    args = get_args()
    api, auth = get_api(args.config_filename)
    action_queue = queue.Queue()

    threading.Thread(target=action_loop, args=(
        api,
        action_queue,
        args.wait_time,
        args.links_filename,
        TWEET_MESSAGE)).start()

    # Keep the app running when it periodically hangs
    while True:
        try:
            logger.info('Launching main loop')
            run(api, auth, args.phrases_filename, action_queue)
        except Exception as exc:
            # Trying to figure out what kind of exception this throws 
            logger.warning('Exception type in main(): {}, exception: {}'.format(
                type(exc), str(exc)))
            if is_exception_whitelisted(WHITELISTED_ERRORS_MAIN, exc):
                logger.warning(f'Whitelisted error in main, reconnect quickly')
                time.sleep(30)
                continue
            else:
                logger.warning('Not whitelisted, sleeping for 10 mintues')
                time.sleep(600)

if __name__ == '__main__':
    main()
