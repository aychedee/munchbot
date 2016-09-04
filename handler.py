from datetime import datetime
from vendored import boto3



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
    kv_store.put('last_accessed', datetime.now().strftime('%Y-%m-%d %H:%M'))

    print event, context

    if event['type'] == 'url_verification':
        if event['token'] == kv_store.munch_bot_key:
            return {'challenge': event['challenge']}
        return {'message': 'token not valid'}

    return {
        'message': 'Endpoint hit!',
        'event': event,
        'last_accessed': kv_store.last_accessed
    }
