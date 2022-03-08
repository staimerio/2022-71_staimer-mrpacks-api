# Retic
from retic import Request, Response, Next, App as app

# Services
from services.mrpacks import mrpacks
from retic.services.validations import validate_obligate_fields
from retic.services.responses import success_response, error_response

# Constants
WEBSITE_LIMIT_LATEST = app.config.get('WEBSITE_LIMIT_LATEST')
WEBSITE_PAGES_LATEST = app.config.get('WEBSITE_PAGES_LATEST')
DESCRIPTION_UPLOAD = app.config.get('DESCRIPTION_UPLOAD')
STORAGE_CREDENTIALS_DEFAULT = app.config.get('STORAGE_CREDENTIALS_DEFAULT')
WEBSITE_ORIGIN = app.config.get('WEBSITE_ORIGIN')

def publish_latest(req: Request, res: Response, next: Next):
    _headers = {}

    """Validate obligate params"""
    _validate = validate_obligate_fields({
        u'wp_login': req.param('wp_login'),
        u'wp_admin': req.param('wp_admin'),
        u'wp_username': req.param('wp_username'),
        u'wp_password': req.param('wp_password'),
        u'wp_url': req.param('wp_url'),
    })

    """Check if has errors return a error response"""
    if _validate["valid"] is False:
        return res.bad_request(
            error_response(
                "The param {} is necesary.".format(_validate["error"])
            )
        )

    # """Validate obligate params"""
    _headers = {
        u'oauth_consumer_key': app.config.get('WP_OAUTH_CONSUMER_KEY'),
        u'oauth_consumer_secret': app.config.get('WP_OAUTH_CONSUMER_SECRET'),
        u'oauth_token': app.config.get('WP_OAUTH_TOKEN'),
        u'oauth_token_secret': app.config.get('WP_OAUTH_TOKEN_SECRET'),
        u'base_url': app.config.get('WP_BASE_URL'),
        u'without_oauth_session': '1',
    }

    limit_publish=req.param(
        'limit_publish', app.config.get('WEBSITE_LIMIT_PUBLISH'),  callback=int)
    
    """Publish items"""
    result = mrpacks.publish_items(
        req.param('limit', WEBSITE_LIMIT_LATEST,  callback=int),
        headers=_headers,
        limit_publish=limit_publish,
        description_upload=req.param('description_upload', DESCRIPTION_UPLOAD),
        page=req.param('page', WEBSITE_PAGES_LATEST, callback=int),
        credential=req.headers.get('credential', STORAGE_CREDENTIALS_DEFAULT),
        origin=req.param('origin', WEBSITE_ORIGIN)
    )
    """Check if exist an error"""
    if result['valid'] is False:
        return res.bad_request(result)    
    # """Response the data to client"""
    res.ok(result)