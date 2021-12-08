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

host = 'http://hellporno.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas" , action="lista", url=host + "/?page=1"))
    # itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/?q=%s" % (host, texto)
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
    data = scrapertools.find_single_match(data,'<div class="container">(.*?)<div id="aside">')
    patron  = '<a href="([^"]+)">.*?'
    patron += '<img src="([^"]+)" alt="([^"]+) - Porn videos">.*?'
    patron += '<span>(\d+) videos</span>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,cantidad in matches:
        scrapedplot = ""
        scrapedtitle = "%s (%s)" % (scrapedtitle,cantidad)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail , plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<a href="([^"]+)" class="next">Next page &raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias" , title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="video-thumb"><a href="([^"]+)" class="title".*?>([^"]+)</a>.*?'
    patron += '<span class="time">([^<]+)</span>.*?'
    patron += '<video muted poster="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,duracion,scrapedthumbnail  in matches:
        url = scrapedurl
        title = "[COLOR yellow]%s[/COLOR] %s" % (duracion,scrapedtitle)
        contentTitle = title
        thumbnail = scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail, plot=plot, contentTitle = contentTitle))
    next_page = scrapertools.find_single_match(data,'<a href="([^"]+)" class="next">Next page &raquo;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data,'<source data-fluid-hd src="([^"]+)/?br=\d+"')
    if scrapedurl=="":
        scrapedurl = scrapertools.find_single_match(data,'<source src="([^"]+)/?br=\d+"')
    itemlist.append(item.clone(action="play", title="mp4", url=scrapedurl))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    scrapedurl = scrapertools.find_single_match(data,'<source data-fluid-hd src="([^"]+)/?br=\d+"')
    if scrapedurl=="":
        scrapedurl = scrapertools.find_single_match(data,'<source src="([^"]+)/?br=\d+"')
    itemlist.append(item.clone(action="play", title=scrapedurl, url=scrapedurl))
    return itemlist