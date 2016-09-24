from vendored import boto3

_store = None

def get_instance():
    global _store
    if not _store:
        _store = KVStore()
    return _store


class KVStore(object):

    def __init__(self):
        self._store = boto3.resource(
            'dynamodb', 'us-east-1'
        ).Table('munchBotKeyStore')

    def __getattr__(self, name):
        self.name = self._store.get_item(Key={'id': name})['Item']['value']
        return self.name

    def put(self, key, value):
        self._store.put_item(Item={'id': key, 'value': value})
