"""Services for novels controller"""

# Retic
from retic import env, App as app

# Requests
import requests

# Time
from time import sleep

# Time
from datetime import datetime
# Services
from retic.services.responses import success_response, error_response
from retic.services.general.urls import slugify
# services
from services.wordpress import wordpress
from services.images import images
from services.zip import zip

# Models
from models import Scrapper
import services.general.constants as constants
import services.mrpacks.photos as photos

# Constants
WEBSITE_LIMIT_LATEST = app.config.get('WEBSITE_LIMIT_LATEST')

URL_MUYSEXY_LATEST = app.apps['backend']['muysexy']['base_url'] + \
    app.apps['backend']['muysexy']['latest']
URL_MUYSEXY_POST = app.apps['backend']['muysexy']['base_url'] + \
    app.apps['backend']['muysexy']['posts']
URL_SENDFILES_WEB = app.config.get('URL_SENDFILES_WEB')
WEBSITE_URL = app.config.get('WEBSITE_URL')
WEBSITE_POST_TYPE = app.config.get('WEBSITE_POST_TYPE')
WEBSITE_YEAR = app.config.get('MRPACKS_YEAR')


def get_items_from_origin(limit, page, origin=None):
    if origin == constants.ORIGIN['muysexy']:
        return get_items_from_website(limit, page)
    elif origin == constants.ORIGIN['mrpacks']:
        _items = photos.get_latest(
            limit=limit,
            page=page,
        )
        return success_response(data={u'items': _items['data']})
    else:
        return get_items_from_website(limit, page, origin)


def get_items_from_website(limit, page):
    """Prepare the payload"""
    _payload = {
        u"limit": limit,
        u"page": page
    }
    """Get all novels from website"""
    _result = requests.get(URL_MUYSEXY_LATEST, params=_payload)
    """Check if the response is valid"""
    if _result.status_code != 200:
        """Return error if the response is invalid"""
        raise Exception(_result.text)
    """Get json response"""
    _result_json = _result.json()
    """Return novels"""
    return _result_json


def get_publication_from_origin(url, id, origin):
    if origin == constants.ORIGIN['muysexy']:
        """Get all chapters of the novels without ids that exists"""
        return get_mirrors_from_website(
            url_base=URL_MUYSEXY_POST,
            url=url,
        )
    elif origin == constants.ORIGIN['mrpacks']:
        _publication = photos.get_info_post(
            id=id
        )
        return _publication['data']
    else:
        return None


def get_mirrors_from_website(url_base, url):
    """Prepare the payload"""
    _payload = {
        u"url": url,
    }
    """Get all chapters from website"""
    _info = requests.get(url_base, params=_payload)
    """Check if the response is valid"""
    if _info.status_code != 200:
        """Return error if the response is invalid"""
        return None
    """Get json response"""
    _info_json = _info.json()
    """Return chapters"""
    return _info_json.get('data')


def build_items_to_upload(
    items,
    headers,
    limit_publish,
    origin,
):
    """Define all variables"""
    _items = []
    """For each novel do the following"""
    for _item in items:
        """Find novel in db"""
        _oldpost = wordpress.search_post_by_slug(
            _item['slug'], headers=headers, post_type=WEBSITE_POST_TYPE
        )
        if _oldpost:
            continue

        _publication = get_publication_from_origin(
            _item['url'], _item['id'] if 'id' in _item else None, origin)
        """Check if it has any problem"""
        if not _publication:
            continue

        """Set data"""
        _data = {
            **_item,
            **_publication,
        }
        """Add novel to list"""
        _items.append(_data)
        """Check the limit"""
        if len(_items) >= limit_publish:
            break
    return _items


def build_post_content(item, description_upload, cover_url, title, credential):
    _links_str = ""
    _download_img = "/descargar-pack-xxx-mega.png"
    if 'links' not in item or not item['links']:
        _upload = zip.zip_images(
            item['images'],
            description_upload,
            item['slug'],
            credential
        )
        if _upload['valid'] is False:
            return None
        _links_str = """
            <p style="text-align: center;">
            <a href="{1}/#/downloads/{2}" target="_blank" rel="noopener noreferrer">
                    <img class="alignnone size-full wp-image-5541" src="{3}" alt="{0}" title="{0}" width="300" height="60" />
                </a>
            </p>
            """.format(
            title,
            URL_SENDFILES_WEB,
            _upload['data']['code'],
            _download_img
        )
    else:
        for _link in item['links']:
            _links_str = """
            <p style="text-align: center;">
                <a href="{1}" target="_blank" rel="noopener noreferrer">
                    <img class="alignnone size-full wp-image-5541" src="{2}" alt="{0}" title="{0}" width="300" height="60" />
                </a>
            </p>
            """.format(
                title,
                _link,
                _download_img
            )
    if _links_str == "":
        return None
    _content = """
        <p style="text-align: center;">{0} Pack XXX.</p>
        <img class="aligncenter wp-image-2815" src="{1}" alt="{0}" title="{0}" />
        <p style="text-align: center;">DESCARGA AQUI:</p>
        {2}
    """.format(
        title,
        item['images'][0],
        _links_str,
    )

    return _content


def publish_item_wp(
    items, headers,
    description_upload,
    credential
):
    """Publish all items but it check if the post exists,
    in this case, it will update the post.

    :param items: List of novel to will publish
    """
    """Define all variables"""
    _published_items = []
    """For each novels do to the following"""
    for _item in items:
        """Generate title"""
        _title = "Pack de {0} gratis completo {1}".format(
            _item['title'], WEBSITE_YEAR)
        _cover = images.upload_images_from_urls(
            urls=[_item['cover']],
        )
        _cover_url = _cover['data']['images'][-1]['link']
        """Generate content"""
        _content = build_post_content(
            _item,
            description_upload,
            _cover_url,
            _title,
            credential
        )
        if not _item['categories']:
            _item['categories'] = ['Packs XXX']
        _categories = [
            {
                u"name": _category,
                u"slug": slugify(_category),
            } for _category in _item['categories']
        ]
        _taxonomy_categories = {
            u'taxonomy': 'category',
            u'items': _categories
        }

        if not _item['genres']:
            _item['genres'].append('Only fans')
        _tags = [
            {
                u"name": _genre,
                u"slug": slugify(_genre),
            } for _genre in _item['genres']
        ]
        _taxonomy_tags = {
            u'taxonomy': 'post_tag',
            u'items': _tags
        }

        _props = {
            u'taxonomy_items': [
                _taxonomy_categories,
                _taxonomy_tags
            ],
            u'featured_media_url': _cover_url,
        }
        """Create the post"""
        _post = wordpress.create_post(
            title=_title,
            slug=_item['slug'],
            content=_content,
            headers=headers,
            post_type=WEBSITE_POST_TYPE,
            props=_props,
        )
        """Check if is a valid post"""
        if not _post or not _post['valid'] or not 'id' in _post['data']:
            """Add post to novel"""
            continue

        _published_items.append(_post['data'])
    """Return the posts list"""
    return _published_items


def upload_items(
    limit,
    headers,
    limit_publish,
    page,
    description_upload,
    credential,
    origin,
):
    _items = get_items_from_origin(
        limit=limit,
        page=page,
        origin=origin,
    )

    if _items['valid'] is False:
        return []
    _builded_items = build_items_to_upload(
        _items['data']['items'],
        headers,
        limit_publish,
        origin=origin,
    )

    if not _builded_items:
        return []

    """Publish or update on website"""
    _created_posts = publish_item_wp(
        _builded_items,
        headers=headers,
        description_upload=description_upload,
        credential=credential
    )
    return _created_posts


def publish_items(
    limit,
    headers,
    limit_publish,
    description_upload,
    page=1,
    credential=None,
    origin=None,
    wp_url=None,
):

    _items = []
    """Find in database"""
    _session = app.apps.get("db_sqlalchemy")()
    _item = _session.query(Scrapper).\
        filter(Scrapper.key == wp_url, Scrapper.type == constants.TYPES['images']).\
        first()

    _date = datetime.now()

    if not _item or (_item.created_at.year != _date.year or _item.created_at.day != _date.day):
        print("*********scrapper_packs_publish*********")
        """Variables"""
        _items = upload_items(
            limit,
            headers,
            limit_publish,
            page=page,
            description_upload=description_upload,
            credential=credential,
            origin=origin,
        )
    
    print("*********len(_items):*********" + str(len(_items)))
    """Check if almost one item was published"""
    if(len(_items) == 0):
        if _item is None:
            print("*********_item = Scrapper*********")
            _item = Scrapper(
                key=wp_url,
                type=constants.TYPES['images'],
                value=page+1
            )
            """Save chapters in database"""
            _session.add(_item)
            _session.flush()

        _items = upload_items(
            limit,
            headers,
            limit_publish,
            page=_item.value,
            description_upload=description_upload,
            credential=credential,
            origin=origin,
        )

        if(len(_items) == 0):
            print("*********_item.value = *********")
            _item.value = str(int(_item.value)+1)

        _session.commit()
        _session.close()

    _data_respose = {
        u"items":  _items
    }
    return success_response(
        data=_data_respose
    )
