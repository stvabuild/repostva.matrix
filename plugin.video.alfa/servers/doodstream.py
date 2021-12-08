# -*- coding: utf-8 -*-
# --------------------------------------------------------
# Conector DoodStream By Alfa development Group
# --------------------------------------------------------
import re
import base64
import time
from lib import js2py
from core import httptools
from core import scrapertools
from platformcode import logger

data = ""
host = "https://dood.la"

def test_video_exists(page_url):
    global data
    page_url = page_url.replace('/d/', '/e/')
    logger.info("(page_url='%s')" % page_url)
    #response = httptools.downloadpage(page_url, headers={"referer": host})
    response = httptools.downloadpage(page_url)
    if response.code == 404:
        return False, "[Doodstream] El archivo no existe o ha sido borrado"
    elif not scrapertools.find_single_match(response.data, ("(function\s?makePlay.*?;})")):
        test_video_exists(page_url)
    else:
        data = response.data
    return True, ""


def get_video_url(page_url, premium=False, user="", password="", video_password=""):
    global data
    logger.info("url=" + page_url)
    video_urls = list()
    label = scrapertools.find_single_match(data, r'type:\s*"video/([^"]+)"')
    js_code = scrapertools.find_single_match(data, ("(function\s?makePlay.*?;})"))

    js_code = re.sub(r"\+Date.now\(\)", '', js_code)
    js = js2py.eval_js(js_code)
    makeplay = js() + str(int(time.time()*1000))

    base_url = scrapertools.find_single_match(data, r"\$.get\('(/pass[^']+)'")

    new_data = httptools.downloadpage("%s%s" % (host, base_url), add_referer=True).data
    retries = 0
    while "We are checking your browser" in new_data and retries < 3:
        new_data = httptools.downloadpage("%s%s" % (host, base_url), add_referer=True).data
        retries += 1
    if retries > 3:
        return video_urls

    new_data = re.sub(r'\s+', '', new_data)
    url = new_data + makeplay + "|Referer=%s" % page_url
    video_urls.append(['%s [doodstream]' % label, url])

    return video_urls
