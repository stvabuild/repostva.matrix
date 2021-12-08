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

host = 'https://pornvibe.org'

# no se ven HD, falla pagina?

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/all-videos/"))
    itemlist.append(item.clone(title="Canal" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
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
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="item-cat.*?'
    patron += '<img src="([^"]+)" alt="([^"]+)".*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<p>([^<]+)Videos posted<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for thumbnail,scrapedtitle,scrapedurl,cantidad in matches:
        title = "%s (%s)" %(scrapedtitle,cantidad)
        url = urlparse.urljoin(host,scrapedurl)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return sorted(itemlist, key=lambda i: i.title)


def stitle(title, url):
    logger.info()
    t = title.split()
    long = len(t)-1
    url = scrapertools.find_single_match(url, '.org/([^/]+)')
    url2 = url.split('-')[long:]
    t2=""
    for elem in url2:
        t2 += "%s " % elem.capitalize()
    stitle = "%s %s" %(title, t2) 
    return stitle


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data= scrapertools.find_single_match(data, '<head>(.*?)>Next &raquo')
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="item large-\d+.*?'
    patron += 'src="([^"]+)".*?'
    patron += '<div class="video-stats clearfix">(.*?)<span class="sl-wrapper">(.*?)<div class="post-des">.*?'
    patron += '<a href="([^"]+)">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,quality,time,scrapedurl,scrapedtitle in matches:
        if "..." in scrapedtitle:
            scrapedtitle = scrapertools.find_single_match(scrapedtitle, '(.*?&#8211;)')
            scrapedtitle = stitle(scrapedtitle,scrapedurl)
        quality = scrapertools.find_single_match(quality, '<h6>([^<]+)</h6>')
        quality = ""  # Solo ofrece videolinks SD
        time = scrapertools.find_single_match(time, '<span>([^<]+)</span>')
        title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time,quality, scrapedtitle)
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle=title))
    next_page = scrapertools.find_single_match(data, '<a class="next page-numbers" href="([^"]+)"')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = 'src="([^"]+)" type="video/mp4"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = 'src="([^"]+)" type="video/mp4"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist