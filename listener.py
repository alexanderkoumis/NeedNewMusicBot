import traceback
import logging
import time

from tweepy.streaming import StreamListener


logger = logging.getLogger(__name__)


class Listener(StreamListener):

    def __init__(self, api, phrases_fname, action_queue, *args, **kwargs):
        super(StreamListener, self).__init__(*args, **kwargs)
        self.api = api
        self.phrases_fname = phrases_fname
        self.action_queue = action_queue
        self.already_retweeted = set()


    def on_status(self, status):
        if self.should_retweet(status):
            self.action_queue.put(status)
            self.already_retweeted.add(status.id)


    def should_retweet(self, status):
        return (
            # They are looking for music
            self.phrase_matches(status.text) and
            # Is not a retweet
            not hasattr(status, 'retweeted_status') and
            # Haven't retweeted yet
            status.id not in self.already_retweeted
        )


    def phrase_matches(self, text):
        for phrase in self.load_phrases():
            if phrase.lower() in text.strip().lower():
                return True
        return False


    def load_phrases(self):
        with open(self.phrases_fname, 'r') as phrases_file:
            return phrases_file.read().splitlines()


    def on_error(self, status_code):
        if status_code == 420:
            logger.error('Getting rate limited, chilling out')
            time.sleep(60)
        else:
            logger.warning(f'Error code {status_code}')
