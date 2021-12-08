# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from core.item import Item
from platformcode import config, logger
from core import httptools
from core import scrapertools
from core import servertools


host = 'http://www.pelisxporno.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="lista", title="Novedades", url= host + "/?order=date"))
    itemlist.append(item.clone(action="categorias", title="Categorías", url=host + "/categorias/"))
    itemlist.append(item.clone(action="search", title="Buscar"))
    return itemlist


def search(item, texto):
    logger.info("")
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
        


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<li class="cat-item cat-item-.*?"><a href="([^"]+)".*?>([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="video.*?'
    patron += '<a href="([^"]+)" title="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += 'duration.*?>([^<]+)<'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, duration in matches:
        if duration:
            scrapedtitle = "[COLOR yellow]%s[/COLOR] %s" % (duration,scrapedtitle)
        itemlist.append( Item(channel=item.channel, action="play", title=scrapedtitle, contentTitle=scrapedtitle, url=scrapedurl,
                                   fanart=scrapedthumbnail, thumbnail=scrapedthumbnail))
    next_page = scrapertools.find_single_match(data, '<a class="nextpostslink" rel="next" href="([^"]+)"')
    if next_page:
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def play(item):
    logger.info(item)
    itemlist = servertools.find_video_items(item.clone(url = item.url, contentTitle = item.title))
    return itemlist
