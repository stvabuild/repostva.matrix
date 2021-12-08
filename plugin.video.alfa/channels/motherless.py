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
from core import servertools
from core.item import Item
from core import httptools

host = 'https://motherless.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host +"/videos/recent"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/videos/viewed"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/videos/commented"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/videos?term=%s&size=0&range=0&sort=date" % (host, texto)
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
    if PY3 and isinstance(data, bytes):
        data = data.decode('utf-8')
    data = scrapertools.find_single_match(data, '<div class="menu-categories-tab"(.*?)<div class="menu-categories-tab"')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|\\", "", data)
    patron = '<a href="([^"]+)" class="[^"]+">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle 
        url = urlparse.urljoin(item.url,scrapedurl)
        url = "%s/videos" % url
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return itemlist



def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if PY3 and isinstance(data, bytes):
        data = data.decode('utf-8')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="thumb.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<span class="size">([^<]+)<.*?'
    patron += 'src="([^"]+.jpg)".*?'
    patron += 'alt="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,time,scrapedthumbnail,scrapedtitle in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="pop" rel="next"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if PY3 and isinstance(data, bytes):
        data = data.decode('utf-8')
    url = scrapertools.find_single_match(data, 'fileurl = \'([^,\']+)\'')
    itemlist.append(item.clone(action="play",title="Directo", url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    if PY3 and isinstance(data, bytes):
        data = data.decode('utf-8')
    url = scrapertools.find_single_match(data, 'fileurl = \'([^,\']+)\'')
    itemlist.append(item.clone(action="play", url=url))
    return itemlist