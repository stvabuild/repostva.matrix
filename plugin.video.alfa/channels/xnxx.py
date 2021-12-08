# -*- coding: utf-8 -*-
#------------------------------------------------------------
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

host = 'https://www.xnxx.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Popular" , action="lista", url=host + "/hits/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/%s" % (host, texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|\\", "", data)
    patron = '"i":"([^"]+)".*?'
    patron += '"u":"([^"]+)".*?'
    patron += '"tf":"([^"]+)".*?'
    patron += '"n":"([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,title,cantidad in matches:
        title = "%s (%s)" %(title, cantidad)
        url = scrapedurl.replace("\/" , "/")
        url = urlparse.urljoin(item.url,scrapedurl)
        thumbnail = scrapedthumbnail.replace("\/" , "/")
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div id="video_\d+".*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'data-src="([^"]+)".*?'
    patron += 'title="([^"]+)".*?'
    patron += '>([^<]+)<span class="video-hd">.*?'
    patron += '</span>([^<]+)</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime,quality in matches:
        title = '[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s' % (scrapedtime,quality,scrapedtitle)
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, quality=quality,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li><a href="([^"]+)" class="no-page next">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist