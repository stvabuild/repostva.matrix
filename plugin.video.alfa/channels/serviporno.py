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
from core.item import Item
from platformcode import logger

host = "https://www.serviporno.com"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="videos", title="Útimos videos", url=host))
    itemlist.append(item.clone(action="videos", title="Más vistos", url=host + "/mas-vistos/"))
    itemlist.append(item.clone(action="videos", title="Más votados", url=host + "/mas-votados/"))
    itemlist.append(item.clone(action="chicas", title="Chicas", url=host + "/pornstars/"))
    itemlist.append(item.clone(action="categorias", title="Canal", url=host + "/sitios/"))
    itemlist.append(item.clone(action="categorias", title="Categorias", url= host + "/categorias/"))

    itemlist.append(item.clone(action="search", title="Buscar", last=""))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = '%s/search/?q=%s' % (host, texto)
    try:
        return videos(item)
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="wrap-box-escena.*?'
    patron += 'data-src="([^"]+)".*?'
    patron += '<h4.*?<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for thumbnail, url, title in matches:
        url = urlparse.urljoin(item.url, url)
        itemlist.append(item.clone(action='videos', title=title, url=url, thumbnail=thumbnail, plot=""))
    # Paginador   "Página Siguiente >>"
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn-pagination">Siguiente')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def chicas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="box-chica">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src=\'([^\']+.jpg)\'.*?'
    patron += '<h4><a href="[^"]+">([^<]+)</a></h4>.*?'
    patron += '<a class="total-videos".*?>([^<]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for url, thumbnail, title, videos in matches:
        url = urlparse.urljoin(item.url, url)
        title = "%s (%s)" % (title, videos)
        itemlist.append(item.clone(action='videos', title=title, url=url, thumbnail=thumbnail, fanart=thumbnail))
    # Paginador 
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn-pagination">Siguiente')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="chicas", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def videos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '(?s)<div class="wrap-box-escena">.*?'
    patron += '<div class="box-escena">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+.jpg)".*?'
    patron += '<h4><a href="[^"]+">([^<]+)</a></h4>.*?'
    patron += '<div class="duracion">([^"]+) min</div>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url, thumbnail, title,duration in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (duration, title)
        url = urlparse.urljoin(item.url, url)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, contentTitle = title, url=url, 
                             thumbnail=thumbnail, fanart=thumbnail))
    # Paginador
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="btn-pagination">Siguiente')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="videos", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, "sendCdnInfo.'([^']+)")
    url = url.replace("&amp;", "&")
    itemlist.append(item.clone(action="play", title="Directo", url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    url = scrapertools.find_single_match(data, "sendCdnInfo.'([^']+)")
    url = url.replace("&amp;", "&")
    itemlist.append(item.clone(action="play", url=url))
    return itemlist