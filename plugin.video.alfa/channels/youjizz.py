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

host = 'https://www.youjizz.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas", action="lista", url=host + "/newest-clips/1.html"))
    itemlist.append(item.clone(title="Popular", action="lista", url=host + "/most-popular/1.html"))
    itemlist.append(item.clone(title="Mejor valorada", action="lista", url=host + "/top-rated-week/1.html"))
    itemlist.append(item.clone(title="Categorias", action="categorias", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/recent_%s-1.html" % (host, texto)
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
    data = scrapertools.find_single_match(data, '>Trending <(.*?)</ul>')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<li><a href="([^"]+)">([^"]+)</a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedtitle in matches:
        scrapedplot = ""
        scrapedthumbnail = ""
        scrapedurl = urlparse.urljoin(item.url, scrapedurl)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                             thumbnail=scrapedthumbnail, plot=scrapedplot))
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="video-item">.*?'
    patron += 'href="([^"]+)".*?'
    patron += 'data-original="([^"]+)"(.*?)'
    patron += '<div class="video-title">.*?'
    patron += '>([^<]+)</a>.*?'
    patron += '<span class="time">([^<]+)<'
    matches = re.compile(patron, re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, quality, scrapedtitle, duracion in matches:
        url = urlparse.urljoin(item.url, scrapedurl)
        if 'HD' in quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (duracion, scrapedtitle)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (duracion, scrapedtitle)
        contentTitle = title
        if not scrapedthumbnail.startswith("https"):
            scrapedthumbnail = "http:%s" % scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=scrapedthumbnail,
                             plot=plot, quality=quality, contentTitle=contentTitle))
    next_page = scrapertools.find_single_match(data, '<li><a class="pagination-next" href="([^"]+)">Next &raquo;</a>')
    if next_page != "":
        next_page = urlparse.urljoin(item.url, next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'var dataEncodings(.*?)var')
    patron = '"quality":"(\d+)","filename":"([^"]+)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,url in matches:
        if ".mp4?" in url: serv= "mp4"
        else: serv="m3u8"
        if not url.startswith("https"):
            url = "https:%s" % url.replace("\\", "")
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data, 'var dataEncodings(.*?)var')
    patron = '"quality":"(\d+)","filename":"([^"]+)",'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,url in matches:
        if ".mp4?" in url: serv= "mp4"
        else: serv="m3u8"
        if not url.startswith("https"):
            url = "https:%s" % url.replace("\\", "")
        itemlist.append(['%sp [%s]' %(quality,serv), url])
    return itemlist
