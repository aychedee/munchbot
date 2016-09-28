import boto3
from datetime import datetime
import urllib



class Torrent(object):
    TORRENT_URL = (
        u'https://s3.amazonaws.com/'
        u'munch.aychedee.com/torrents/{}.torrent'
    )

    def __init__(self, data):
        self.published = datetime.strptime(
                data['pub_date'][:25],
            '%a, %d %b %Y %H:%M:%S'
        )
        self.pub_date = data['pub_date'][:25]
        self.title = data['title']
        try:
            self.quoted_title = urllib.quote_plus(self.title, safe='()~')
        except KeyError:
            self.quoted_title = self.title
        self.s3_url = self.TORRENT_URL.format(self.quoted_title)

    @property
    def name(self):
        return self.title.replace('.', ' ')


class Torrents(object):
    '''A lazy, self populating container for torrent objects'''

    def __init__(self):
        self.db_table = boto3.resource(
            'dynamodb', 'us-east-1').Table('torrents')
        self._torrents = []

    def most_recent(self, number=20):
        return self.items[-number-1:-1]

    @property
    def items(self):
        if not self._torrents:
            self._torrents = sorted(
                [
                    Torrent(t) for t in self.db_table.scan()['Items']
                ],
                key=lambda t: t.published
            )
        return self._torrents

    def __nonzero__(self):
        return bool(self.items)

