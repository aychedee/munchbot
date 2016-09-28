from mock import Mock
import pytest

from bot import MunchBot
import torrent
from test_data import TORRENT_DATA


@pytest.fixture
def mock_boto(monkeypatch):
    mock_boto = Mock()
    monkeypatch.setattr(torrent, 'boto3', mock_boto)


@pytest.fixture
def munchbot(mock_boto):
    mb = MunchBot()
    mb._torrents.db_table.scan.return_value = TORRENT_DATA
    return mb


@pytest.fixture
def munchbot_no_torrents(munchbot):
    munchbot._torrents.db_table.scan.return_value = {'Items': []}
    return munchbot


def test_munch_bot_is_helpful(munchbot):
    mb = munchbot

    for message in ('help', 'instructions', '?', 'hello', 'help me', 'HELP'):
        response = mb.instruct(message)

        assert response['text'] == mb.MESSAGES['help']
        assert response['face'] == mb.EMOJIS['happy']

def test_munch_bot_is_sorry_with_no_torrents(munchbot_no_torrents):
    mb = munchbot_no_torrents

    response = mb.instruct('torrents')

    assert response['text'] == mb.MESSAGES['no_torrents']
    assert response['face'] == mb.EMOJIS['crazed']


def test_munch_bot_returns_torrents(munchbot):
    mb = munchbot

    response = mb.instruct('torrents')

    assert 'Teenage+Mutant+Ninja+Turtles+Out' in response['text']
    assert response['face'] == mb.EMOJIS['smirky']


def test_munch_bot_can_be_unhelpful(munchbot):
    mb = munchbot

    response = mb.instruct('just something random')

    assert response['text'] in mb.MESSAGES['random']
    assert response['face'] in mb.EMOJIS.values()
