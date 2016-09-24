from datetime import datetime
import urllib
from random import choice
import tempfile
from threading import Thread
import xml.etree.ElementTree as ET

from vendored import boto3, requests
import kvstore

s3 = boto3.client('s3')

CAT_EMOJIS = [
    ':cat:',
    ':scream_cat:',
    ':kissing_cat:',
    ':crying_cat_face:',
    ':pouting_cat:',
    ':smirk_cat:'
]

MUNCH_PHRASES = [
    'Arigato',
    'Mmmm....',
    'Where\'s my toy?',
    'I see boring people',
    'Is it dinner time yet?',
    'When IS breakfast?'
]

SLACK_URL = 'https://slack.com/api/'

TORRENT_URL = u'https://s3.amazonaws.com/munch.aychedee.com/torrents/{}.torrent'


class Torrent(object):

    def __init__(self, data):
        self.published = datetime.strptime(
                data['pub_date'][:25],
            '%a, %d %b %Y %H:%M:%S'
        )
        self.pub_date = data['pub_date']
        self.title = data['title']
        try:
            self.quoted_title = urllib.quote_plus(self.title, safe='()~')
        except KeyError:
            self.quoted_title = self.title
        self.s3_url = TORRENT_URL.format(self.quoted_title)




def munch(event, context):

    if event['method'] == 'POST':
        body = event['body']
        if body['type'] == 'url_verification':
            if body['token'] == kvstore.get_instance().munch_bot_key:
                return {'challenge': body['challenge']}
            return {'message': 'token not valid'}

    if event['body']['type'] == 'event_callback':
        msg_event = event['body']['event']
        if msg_event.get('subtype') != 'bot_message':
            if 'torrent' in msg_event.get('text'):
                table = boto3.resource('dynamodb').Table('torrents')
                torrents =  sorted(
                    [Torrent(t) for t in table.scan()['Items']],
                    key=lambda t: t.published,
                )
                response_text = '\n'.join(
                    [
                        '{0.pub_date} -- {0.title}\n{0.s3_url}'.format(t) for
                            t in torrents
                    ]
                )
            else:
                response_text = choice(MUNCH_PHRASES)

            response = requests.post(
                SLACK_URL + 'chat.postMessage',
                data=dict(
                    token=kvstore.get_instance().munch_bot_access_token,
                    channel=msg_event['channel'],
                    text=response_text,
                    icon_emoji=choice(CAT_EMOJIS)
                )
            )
            print response.content

    else:
        return {
            'message': 'Endpoint hit!',
            'event': event,
            'last_accessed': kvstore.get_instance().last_accessed
        }


def oauth(event, context):

    print event, context
    response = requests.post(
        'https://slack.com/api/oauth.access',
        data=dict(
            client_id=kvstore.get_instance().oauth_client_id,
            client_secret=kvstore.get_instance().oauth_client_secret,
            code=event['query']['code'],
        )
    )

    print response.content

    return 'hello, that seemed to work'


def get_and_put_torrent(url, title):
    r = requests.get(url)
    with tempfile.NamedTemporaryFile() as f:
        # Only doing this because s.upload_fileobj missing at the moment
        f.write(r.content)
        f.flush()

        s3.upload_file(
            f.name,
            'munch.aychedee.com',
            'torrents/' + title + '.torrent'
        )


def gather(event, context):
    print event, context
    table = boto3.resource('dynamodb').Table('torrents')

    response = requests.get('http://extratorrent.cc/rss.xml?type=popular&cid=4')

    torrents = []
    feed = ET.fromstring(response.content)
    for movie in feed[0].findall('item'):
        torrent_url = movie.find('enclosure').attrib['url']
        title = movie.find('title').text
        torrents.append((torrent_url, title))
        table.put_item(
            Item={
                'title': title,
                'size': movie.find('size').text,
                'seeders': movie.find('seeders').text,
                'torrent': torrent_url,
                'pub_date': movie.find('pubDate').text
            }
        )

    threads = [
        Thread(
            target=get_and_put_torrent,
            args=(t[0], t[1])) for t in torrents]

    for t in threads:
        t.start()

    for t in threads:
        t.join()

    return 'ok'
