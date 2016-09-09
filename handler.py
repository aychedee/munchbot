from random import choice
import xml.etree.ElementTree as ET

from vendored import boto3, requests


CAT_EMOJIS = [
    ':cat:',
    ':scream_cat:',
    ':kissing_cat:',
    ':crying_cat:',
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


class KVStore(object):

    def __init__(self):
        self._store = boto3.resource('dynamodb').Table('munchBotKeyStore')

    def __getattr__(self, name):
        self.name = self._store.get_item(Key={'id': name})['Item']['value']
        return self.name

    def put(self, key, value):
        self._store.put_item(Item={'id': key, 'value': value})


kv_store = KVStore()


def munch(event, context):

    if event['method'] == 'POST':
        body = event['body']
        if body['type'] == 'url_verification':
            if body['token'] == kv_store.munch_bot_key:
                return {'challenge': body['challenge']}
            return {'message': 'token not valid'}

    if event['body']['type'] == 'event_callback':
        msg_event = event['body']['event']
        if msg_event.get('subtype') != 'bot_message':
            response = requests.post(
                SLACK_URL + 'chat.postMessage',
                data=dict(
                    token=kv_store.munch_bot_access_token,
                    channel=msg_event['channel'],
                    text=choice(MUNCH_PHRASES),
                    icon_emoji=choice(CAT_EMOJIS)
                )
            )
            print response.content

    else:
        return {
            'message': 'Endpoint hit!',
            'event': event,
            'last_accessed': kv_store.last_accessed
        }


def oauth(event, context):

    print event, context
    response = requests.post(
        'https://slack.com/api/oauth.access',
        data=dict(
            client_id=kv_store.oauth_client_id,
            client_secret=kv_store.oauth_client_secret,
            code=event['query']['code'],
        )
    )

    print response.content

    return 'hello, that seemed to work'


def gather(event, context):
    print event, context
    table = boto3.resource('dynamodb').Table('torrents')

    response = requests.get('http://extratorrent.cc/rss.xml?type=popular&cid=4')

    feed = ET.fromstring(response.content)
    for movie in feed[0].findall('item'):
        table.put_item(
            Item={
                'title': movie.find('title').text,
                'size': movie.find('size').text,
                'seeders': movie.find('seeders').text,
                'torrent': movie.find('enclosure').attrib['url'],
                'pub_date': movie.find('pubDate').text
            }
        )

    return 'ok'
