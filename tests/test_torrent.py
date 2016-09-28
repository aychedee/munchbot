from datetime import datetime
from torrent import Torrent


def test_torrent(monkeypatch):

    t = Torrent(
        {
            'pub_date': 'Thu, 08 Sep 2016 18:49:44 +0000',
            'title': 'The.Movie.Title.2016'
        }
    )

    assert t.published == datetime(2016, 9, 8, 18, 49, 44)
    assert t.name == 'The Movie Title 2016'
