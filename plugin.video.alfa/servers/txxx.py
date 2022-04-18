# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
from core import httptools
from core import scrapertools
from platformcode import logger, config


def test_video_exists(page_url):
    logger.info("(page_url='%s')" % page_url)
    if ".tube/" in page_url:
        page_url = page_url.replace(".tube/", ".com/")
    global server, vid
    server = scrapertools.find_single_match(page_url, '([A-z0-9-]+).com')
    vid = scrapertools.find_single_match(page_url, r'(?:embed/|videos/|video-|video/)([0-9]+)')
    vid2 = vid[:-3] +"000"
    if len(vid) <= 6:
        vid1= "0"
    else:
        vid1 = vid[:-6] + "000000"
    url = "https://%s.com/api/json/video/86400/%s/%s/%s.json" %(server,vid1,vid2,vid)
    headers = {'Referer': page_url}
    data = httptools.downloadpage(url, headers=headers).json
    if data['video']['status_id'] == "5":
        return False, config.get_localized_string(70449) % "TXXX"
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    logger.info("url=" + page_url)
    video_urls = []
    if ".tube/" in page_url:
        page_url = page_url.replace(".tube/", ".com/")
    url = "https://%s.com/api/videofile.php?video_id=%s&lifetime=8640000" % (server, vid)
    headers = {'Referer': page_url}
    data = httptools.downloadpage(url, headers=headers).json
    for elem in data:
        url = elem['video_url']
        quality = elem['format']
        quality = scrapertools.find_single_match(quality, '_([A-z]+).mp4')
        url = dec_url(url)
        if not url.startswith("http"):
            url = "https://%s.com/%s" % (server, url)
        media_url = httptools.downloadpage(url, only_headers=True).url
        video_urls.append(["[%s] %s" %(server,quality), media_url])
    return video_urls


def dec_url(txt):
    #truco del mendrugo
    # if not PY3:
        # txt = txt.decode('unicode-escape').encode('utf8')
    # else:
        # txt = txt.encode('utf8').decode('unicode-escape')
    txt = txt.replace('А', 'A').replace('В', 'B').replace('С', 'C').replace('Е', 'E').replace('М', 'M').replace('~', '=').replace(',','/')
    import base64
    url = base64.b64decode(txt)
    url = url.decode("utf8")
    return url
