# Retic
from retic import env, App as app

# Requests
import requests

# Constants
URL_IMAGES_REMOTE = app.apps['backend']['images']['base_url'] + \
    app.apps['backend']['images']['images_remote']
COVER_IMG_WIDTH = app.config.get('COVER_IMG_WIDTH', callback=int)
COVER_IMG_HEIGHT = app.config.get('COVER_IMG_HEIGHT', callback=int)


def upload_images_from_urls(
    urls,
    width=COVER_IMG_WIDTH,
    height=COVER_IMG_HEIGHT,
    watermark_code=None,
    headers=None,
    left_crop=None, top_crop=None, right_crop=None, bottom_crop=None,
):
    """Upload images from url

    :param urls: Urls of the images to upload
    :param width: New Widht of the images
    :param height: New Height of the images
    """

    """Prepare payload for the request"""
    _payload = {
        u"urls": urls,
        u"width": width,
        u"height": height,
        u"watermark_code": watermark_code,
        u"headers": headers,
        u"left_crop": left_crop,
        u"top_crop": top_crop,
        u"right_crop": right_crop,
        u"bottom_crop": bottom_crop,
    }

    """Upload images"""
    _images = requests.post(
        URL_IMAGES_REMOTE,
        json=_payload,
    )
    """Check if the response is valid"""
    if _images.status_code != 200:
        """Return error if the response is invalid"""
        raise Exception(_images.text)
    """Get json response"""
    _images_json = _images.json()
    """Return data"""
    return _images_json
