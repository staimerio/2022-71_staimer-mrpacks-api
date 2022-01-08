# Retic
from retic import env, App as app

# Requests
import requests

# Constants

def remote_upload(
    url,
    description_upload,
    filename,
    credential,
):
    """Upload files

    """

    """Prepare payload for the request"""
    _payload = {
        u"url": url,
        u"description_upload": description_upload,
        u"filename": filename,
    }
    _headers={
        u"credential": credential,
    }

    """Download torrents"""
    _result = requests.post(
        URL_TORRENTS_REMOTE_UPLOAD,
        json=_payload,
        headers=_headers
    )
    """Check if the response is valid"""
    if _result.status_code != 200:
        """Return error if the response is invalid"""
        raise Exception(_result.text)
    """Get json response"""
    _result_json = _result.json()
    """Return data"""
    return _result_json
