"""Services for novels controller"""

# Retic
from retic import env, App as app

# Requests
import requests

# Time
from time import sleep

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

# Constants
WEBSITE_LIMIT_LATEST = app.config.get('WEBSITE_LIMIT_LATEST')

URL_MUYSEXY_LATEST = app.apps['backend']['muysexy']['base_url'] + \
    app.apps['backend']['muysexy']['latest']
URL_MUYSEXY_POST = app.apps['backend']['muysexy']['base_url'] + \
    app.apps['backend']['muysexy']['posts']
URL_SENDFILES_WEB = app.config.get('URL_SENDFILES_WEB')
WEBSITE_URL = app.config.get('WEBSITE_URL')
WEBSITE_POST_TYPE = app.config.get('WEBSITE_POST_TYPE')


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
        """Define the url"""
        _url_base = URL_MUYSEXY_POST
        """Get all chapters of the novels without ids that exists"""
        _publication = get_mirrors_from_website(
            url_base=_url_base,
            url=_item['url'],
        )
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
    _upload = zip.zip_images(
        item['images'],
        description_upload,
        item['slug'],
        credential
    )
    # _upload={
    #     'valid':True,
    #     'data':{            
    #         'description':'Para más contenido visítanos en MrPacks.com',
    #         'credential':None,
    #         'folder':116452,
    #         'platform':1,
    #         'code':'1d9c99e470cd11ec99360242ac120004',
    #         'items':[]
    #     }
    # }
    if _upload['valid'] is False:
        return None

    _content = """
        <p style="text-align: center;">{0} Pack XXX .</p>
        <img class="aligncenter wp-image-2815" src="{1}" alt="{0}" />
        <p style="text-align: center;">DESCARGA AQUI:</p>
        <p style="text-align: center;">
            <a href="{2}/#/downloads/{3}" target="_blank" rel="noopener noreferrer">
                <img class="alignnone size-full wp-image-5541" src="/wp-content/uploads/2021/11/mega-1-1.png" alt="{0}" width="300" height="60" />
            </a>
        </p>
    """.format(
        title,
        item['images'][0],
        URL_SENDFILES_WEB,
        _upload['data']['code'],
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
        _title = "Pack de {0} gratis completo".format(_item['title'])
        _cover = images.upload_images_from_urls(
            urls=[_item['cover']],
        )
        _cover_url=_cover['data']['images'][-1]['link']
        """Generate content"""
        _content = build_post_content(
            _item, 
            description_upload, 
            _cover_url, 
            _title,
            credential
        )
        _item['genres'].append('Packs')
        _categories=[
            {
                u"name": _genre,
                u"slug": slugify(_genre),
            } for _genre in _item['genres']
        ]
        """Create the post"""
        _post = wordpress.create_post(
            title=_title,
            slug=_item['slug'],
            content=_content,
            categories=_categories,
            headers=headers,
            featured_media_url=_cover_url,
            post_type=WEBSITE_POST_TYPE
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
    credential
):
    _items = get_items_from_website(
        limit=limit,
        page=page,
    )

    if _items['valid'] is False:
        return []
    _builded_items = build_items_to_upload(
        _items['data']['items'],
        headers,
        limit_publish
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
):
    _created_posts = upload_items(
        limit,
        headers,
        limit_publish,
        page=page,
        description_upload=description_upload,
        credential=credential
    )
    print("*********len(_items)*********")
    """Check if almost one item was published"""
    if(len(_created_posts) == 0):
        """Find in database"""
        _session = app.apps.get("db_sqlalchemy")()
        _item = _session.query(Scrapper).\
            filter(Scrapper.key == WEBSITE_URL, Scrapper.type == constants.TYPES['images']).\
            first()

        print("*********if _item is None*********")
        if _item is None:
            print("*********_item = Scrapper*********")
            _item = Scrapper(
                key=WEBSITE_URL,
                type=constants.TYPES['images'],
                value=page+1
            )
            """Save chapters in database"""
            _session.add(_item)
            _session.flush()
            """Save in database"""        

        _created_posts = upload_items(
            limit,
            headers,
            limit_publish,
            page=_item.value,
            description_upload=description_upload,
            credential=credential
        )

        if(len(_created_posts) == 0):
            print("*********_item.value = *********")
            _item.value = str(int(_item.value)+1)

        _session.commit()
        _session.close()

    _data_respose = {
        u"items":  _created_posts
    }
    return success_response(
        data=_data_respose
    )
