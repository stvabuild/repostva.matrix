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

host = 'https://letsjerk.to'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/?order=newest"))
    itemlist.append(item.clone(title="Mas valorados" , action="lista", url=host + "/?order=rating_month"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/?order=views_month"))
    itemlist.append(item.clone(title="Mas comentado" , action="lista", url=host + "/?order=comments_month"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories"))

    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/?s=%s&s=%s" % (host,texto, texto)
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<a class="th" href="([^"]+)".*?'
    patron += '<div class="taxonomy-name">([^<]+)<.*?'
    patron += '<div class="number">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,cantidad in matches:
        title = "%s (%s)" % (scrapedtitle, cantidad)
        thumbnail = ""
        url = urlparse.urljoin(item.url,scrapedurl)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li style="list-style-type: none;"><a href="([^"]+)" title="([^"]+)".*?'
    patron += 'data-original="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        title = scrapedtitle
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<link rel="next" href="([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url =""
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    data = scrapertools.find_single_match(data, '<div class="video-container">(.*?)</div>')
    patron = '<source title="([^"]+)" src=([^\s]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality, url in matches:
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    if not url:
        url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
        itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    url =""
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    data = scrapertools.find_single_match(data, '<div class="video-container">(.*?)</div>')
    patron = '<source title="([^"]+)" src=([^\s]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality, url in matches:
        itemlist.append(['%sp' %quality, url])
        itemlist.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    if not url:
        url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
        itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
        itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
