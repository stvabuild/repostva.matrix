# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import logger

host = 'http://tubehentai.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Novedades", action="lista", url=host + "/most-recent/"))
    itemlist.append(item.clone(title="Mas visto", action="lista", url=host + "/most-viewed/"))
    itemlist.append(item.clone(title="Mejor valorado", action="lista", url=host + "/top-rated/"))

    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = "%s/search/%s/" % (host, texto)
    try:
        return lista(item)
    # Se captura la excepciÛn, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<a href="((?:http|https)://tubehentai.com/video/[^"]+)" title="([^"]+)".*?'
    patron += '<span>([^<]+)</span>.*?'
    patron += '<img src="([^"]+)"'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,duration,scrapedthumbnail in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (duration, scrapedtitle)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=scrapedurl, 
                             fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, contentTitle = title))
    next_page = scrapertools.find_single_match(data,'<a href=\'([^\']+)\' class="next"')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url = ""
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+\.mp4)"')
    if not url:
        url = scrapertools.find_single_match(data, '<div class="videohere".*?src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    url = ""
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, '<source src="([^"]+\.mp4)"')
    if not url:
        url = scrapertools.find_single_match(data, '<div class="videohere".*?src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist