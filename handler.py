import tempfile
from threading import Thread
import xml.etree.ElementTree as ET

from vendored import boto3, requests
import kvstore
from bot import get_munch_bot

s3 = boto3.client('s3')
SLACK_URL = 'https://slack.com/api/'


def munch(event, context):
    print event

    if event['method'] == 'POST':
        body = event['body']
        if body['type'] == 'url_verification':
            if body['token'] == kvstore.get_instance().munch_bot_key:
                return {'challenge': body['challenge']}
            return {'message': 'token not valid'}

    if event['body']['type'] == 'event_callback':
        msg_event = event['body']['event']
        if msg_event.get('subtype') != 'bot_message':
            reply = get_munch_bot().instruct(msg_event.get('text'))

            api_response = requests.post(
                SLACK_URL + 'chat.postMessage',
                data=dict(
                    token=kvstore.get_instance().munch_bot_access_token,
                    channel=msg_event['channel'],
                    text=reply['text'],
                    icon_emoji=reply['face']
                )
            )
            print api_response.content

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
