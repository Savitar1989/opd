import re, logging, requests, time
logger = logging.getLogger(__name__)

def parse_hungarian_address(address: str) -> str:
    if not address:
        return ''
    addr = address.strip()
    addr = re.sub(r'\s+', ' ', addr)
    return addr

def shorten_url(url: str) -> str:
    try:
        r = requests.get('https://tinyurl.com/api-create.php', params={'url': url}, timeout=5)
        if r.status_code == 200 and r.text.startswith('http'):
            return r.text.strip()
    except Exception as e:
        logger.error('shorten_url error: %s', e)
    return url
