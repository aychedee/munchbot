from random import choice

from torrent import Torrents


def get_munch_bot():
    if not getattr(get_munch_bot, '_bot_instance', None):
        get_munch_bot._bot_instance = MunchBot()
    return get_munch_bot._bot_instance


class MunchBot(object):

    def __init__(self):
        self._torrents = Torrents()

    def instruct(self, instruction):
        tokens = [t.lower() for t in instruction.split()]
        if tokens[0] in ('help', 'instructions', '?', 'hello'):
            return self._message('help', 'happy')

        if tokens[0] in ('torrents',) and not self._torrents:
            return self._message('no_torrents', 'crazed')

        if tokens[0] in ('torrents',) and self._torrents:
            return {
                'text': '\n'.join(
                    [
                        '{0.pub_date} -- <{0.s3_url}|{0.name}>'.format(t) for
                            t in self._torrents.most_recent()
                    ]
                ),
                'face': self.EMOJIS['smirky']
            }

        return {
            'text': choice(self.MESSAGES['random']),
            'face': choice(self.EMOJIS.values())
        }

    def _message(self, message, face):
        return {
            'text': self.MESSAGES[message],
            'face': self.EMOJIS[face]
        }

    EMOJIS = {
        'normal': ':cat:',
        'crazed': ':scream_cat:',
        'flirty': ':kissing_cat:',
        'sad': ':crying_cat_face:',
        'happy': ':smiley_cat:',
        'pouty': ':pouting_cat:',
        'smirky': ':smirk_cat:',
        'big_laugh': ':joy_cat:'
    }

    MESSAGES = {
        'help': (
        'I can do the following things:\n'
        '  `torrents` Show you the latest 20 torrents I\'ve found\n'
        '  `torrents 56` Show you the latest 56 torrents I\'ve found\n'
        '  `torrents crayon` Show you torrents that have "crayon" in the name\n'
        ),
        'no_torrents': 'Sorry, I don\'t have any!',
        'random': [
            'Arigato',
            'Mmmm....',
            'Where\'s my toy?',
            'I see boring people',
            'Is it dinner time yet?',
            'When IS breakfast?'
        ]
    }
