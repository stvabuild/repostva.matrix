# -*- coding: utf-8 -*-
# ------------------------------------------------------------
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://www.xozilla.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas", action="lista", url=host + "/latest-updates/"))
    itemlist.append(item.clone(title="Popular", action="lista", url=host + "/most-popular/"))
    itemlist.append(item.clone(title="Mejor valorada", action="lista", url=host + "/top-rated/"))

    itemlist.append(item.clone(title="PornStar", action="categorias", url=host + "/models/"))
    itemlist.append(item.clone(title="Canal", action="categorias", url=host + "/channels/"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s/?sort_by=post_date&from_videos=1" % (host, texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a class="item" href="([^"]+)" title="([^"]+)">.*?'
    patron += '<img class="thumb" src="([^"]+)".*?'
    patron += '(.*?)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle, scrapedthumbnail, cantidad in matches:
        scrapedplot = ""
        scrapedurl += "1/" 
        cantidad = scrapertools.find_single_match(cantidad, '(\d+) videos</div>')
        if cantidad:
            scrapedtitle= "%s (%s)" % (scrapedtitle, cantidad)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, fanart=scrapedthumbnail, plot=scrapedplot))
    if not "models" in item.url:
        itemlist.sort(key=lambda x: x.title)

    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    page = scrapertools.find_single_match(item.url, '([^"]+)\d+')
    if next_page != "#videos" and next_page != "":
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    if next_page == "#videos":
        next_page = scrapertools.find_single_match(data, ':(\d+)">Next</a>')
        next_page = "%s%s/" %(page, next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<a href="([^"]+)" class="item.*?'
    patron += 'data-original="([^"]+)".*?'
    patron += 'alt="([^"]+)".*?'
    patron += '<div class="duration">(.*?)</div>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, duracion in matches:
        url = scrapedurl
        title = "[COLOR yellow]%s[/COLOR] %s" % (duracion, scrapedtitle)
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                             fanart=thumbnail, plot=plot, contentTitle=contentTitle))
    next_page = scrapertools.find_single_match(data, '<li class="next"><a href="([^"]+)"')
    page = scrapertools.find_single_match(item.url, '([^"]+)\d+')
    if not "#" in next_page:
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    else:
        next_page = scrapertools.find_single_match(data, ':(\d+)">Next</a>')
        next_page = "%s%s/" %(page, next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def findvideos(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if "kt_player" in data:
        url = item.url
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if "kt_player" in data:
        url = item.url
    itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist