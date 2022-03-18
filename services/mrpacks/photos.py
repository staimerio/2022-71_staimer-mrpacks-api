"""Services for novels controller"""

# Retic
from retic import env, App as app

# Requests
import requests

# Base64
import base64

# bs4
from bs4 import BeautifulSoup

# Services
from retic.services.responses import success_response, error_response
from services.general.general import get_node_item
from retic.services.general.urls import slugify

# Models
# from models import Hentai, HentaiPost, Chapter, Image

# Constants
WEBSITE_YEAR = app.config.get('MRPACKS_YEAR')


class MrPacks(object):

    def __init__(self):
        """Set the variables"""
        self.year = app.config.get("MRPACKS_YEAR")
        self.url_base = app.config.get("MRPACKS_URL_API_BASE")
        self.site = app.config.get("MRPACKS_SITE")
        self.host = app.config.get("MRPACKS_HOST")
        self.langname = app.config.get("MRPACKS_LANGNAME")

    def get_item_info(self, id):
        r_download_page = requests.get("{0}?p={1}".format(self.url_base, id))
        _soup = BeautifulSoup(r_download_page.content, 'html.parser')
        """Get info about the item"""
        _info = self.get_data_post(_soup)
        _links = self.get_data_links(_soup)
        if not _info:
            """Return error if data is invalid"""
            return error_response(
                msg="Item not found."
            )
        """Set the data response"""
        _data_response = {
            **_info,
            **_links,
        }
        return success_response(
            data=_data_response
        )

    def get_data(self, page, service):
        _urls = []
        _mirrors = []

        _rows = page.find_all("tr")
        if(len(_rows) < 2):
            return None
        _rows.pop(0)

        for _item in _rows:
            _mirrors.append(self.get_url_torrent(_item, service))
        return _mirrors

    def get_data_item(self, _soup, service):
        _panel_descarga = _soup.find(class_="links_table")

        if not _panel_descarga:
            return None
        return self.get_data(_panel_descarga, service)

    def get_url_torrent(self, item, service):

        _url_torrent = item.find("a", href=True)['href']
        _url_torrent = _url_torrent.split('url=')[-1]

        r_download_page = requests.get(_url_torrent)
        _soup = BeautifulSoup(r_download_page.content, 'html.parser')
        _url = _soup.find(id="link", href=True)['href']

        _title = ""

        _columns = item.find_all("td")

        _quality = _columns[1].text
        _lang = _columns[2].text
        _size = _columns[3].text
        return {
            u'server': service,
            u'url': _url,
            u'title': _title,
            u'quality': _quality,
            u'lang': _lang,
            u'size': _size,
        }

    def get_data_post(self, _soup):
        _images = []
        _single = _soup.find(class_="s-post-main")
        _cover_raw = _single.find(class_='wp-post-image')
        _content = _soup.find(class_='s-post-content')
        _cover = _cover_raw.attrs['data-lazy-src'] if 'data-lazy-src' in _cover_raw.attrs else _cover_raw['src']

        _images_raw = _content.find_all(class_='aligncenter')

        for _image_raw in [_images_raw.pop()]:
            _url = _image_raw.attrs['data-lazy-src'] if 'data-lazy-src' in _image_raw.attrs else _image_raw['src']
            if "grupo" in _url:
                continue
            _images.append(_url)

        _title = _soup.find("h1").text
        _title = _title.replace("Pack de ", "").replace(
            " gratis completo", "").replace(" {0}".format(WEBSITE_YEAR), "")

        _genres_box = _soup.find(class_="bb-tags")
        _genres = [_genre.text.strip()
                   for _genre in _genres_box.find_all("a", href=True)] if _genres_box else []

        _categories_box = _soup.find(class_="s-post-cat-links")
        _categories = [_category.text.strip()
                       for _category in _categories_box.find_all("a", href=True)]

        if not _categories:
            _categories = ["Packs XXX"]
        return {
            'title': _title,
            'cover': _cover,
            'genres': _genres,
            'categories': _categories,
            "images": _images,
        }

    def get_data_links(self, _soup):
        _links = []
        _links_raw = _soup.find_all(class_="download-link", href=True)
        for _link_raw in _links_raw:
            _blink = _link_raw.attrs['href'].split('api/?urlb64=')[-1]
            _links.append(base64.b64decode(_blink).decode('utf-8'))

        return {
            'links': _links,
        }


def get_instance():
    """Get an MTLNovel instance from a language"""
    return MrPacks()


def get_data_items_raw(instance, page=0):
    """GET Request to url"""
    _url = "{0}/page/{1}".format(instance.url_base, page)
    _req = requests.get(_url)
    """Format the response"""
    _soup = BeautifulSoup(_req.content, 'html.parser')
    _data_raw = _soup.find(id='post-items')
    return _data_raw.find_all(class_='post')


def get_data_item_json(instance, item):
    try:
        """Find the a element"""
        _data_item = item.find('a', href=True)
        """Get url"""
        _url = _data_item['href']
        """Check that the url exists"""
        _title = item.find('h2').text.replace("Pack de ", "").replace(
            " gratis completo", "").replace(" {0}".format(WEBSITE_YEAR), "")
        return get_node_item(item['class'][3].split('post-')[-1], _url, _title, instance.year, instance.host, instance.site)
    except Exception as e:
        return None


def get_list_json_items(instance, page, limit=100):
    """Declare all variables"""
    _items = list()
    """Get article html from his website"""
    _items_raw = get_data_items_raw(instance, page)
    for _item_raw in _items_raw:
        _item_data = get_data_item_json(instance, _item_raw)
        """Check if item exists"""
        if not _item_data:
            continue
        """If lang is different than en(english), add lang to slug"""
        _title = "{0}-{1}".format(_item_data['title'], instance.langname)
        """Slugify the item's title"""
        _item_data['slug'] = slugify(_title)
        """Add item"""
        _items.append(_item_data)
        """Validate if has the max"""
        if len(_items) >= limit:
            break
    """Return items"""
    return _items


def get_latest(limit=10, page=1):
    """Settings environment"""
    instance = get_instance()
    """Request to hitomi web site for latest novel"""
    _items_raw = get_list_json_items(
        instance, page, limit)
    """Validate if data exists"""
    if not _items_raw:
        """Return error if data is invalid"""
        return error_response(
            msg="Files not found."
        )
    """Response data"""
    return success_response(
        data=_items_raw
    )


def get_info_post(id):
    """Settings environment"""
    instance = get_instance()
    """Request to hitomi web site for latest novel"""
    _result = instance.get_item_info(id)
    """Validate if data exists"""
    if not _result['valid']:
        """Return error if data is invalid"""
        return error_response(
            msg="Files not found."
        )
    """Response data"""
    return _result
