from datetime import datetime
from handler import Torrent


def test_torrent(monkeypatch):

    t = Torrent(
        {
            'pub_date': 'Thu, 08 Sep 2016 18:49:44 +0000',
        }
    )

    assert t.published == datetime(2016, 9, 8, 18, 49, 44)
