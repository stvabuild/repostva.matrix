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

host = 'https://www.sunporno.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevas" , action="lista", url=host +"/most-recent/"))
    itemlist.append(item.clone(title="Popular" , action="lista", url=host + "/most-viewed/date-last-week/"))
    itemlist.append(item.clone(title="Mejor valorada" , action="lista", url=host + "/top-rated/date-last-week/"))
    itemlist.append(item.clone(title="Mas largas" , action="lista", url=host + "/long-movies/date-last-month/"))
    itemlist.append(item.clone(title="PornStars" , action="catalogo", url=host + "/pornstars/most-viewed/1/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/channels/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/%s/" % (host, texto)
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
    patron = '<div class="thumb-container with-title moviec.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '<a title="([^"]+)".*?'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle in matches:
        scrapedplot = ""
        scrapedurl = "%s/most-recent/" %scrapedurl
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = '<div class="starec">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<img class="thumb" src="([^"]+)"  alt="([^"]+)".*?'
    patron += '<p class="videos">(\d+)</p>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl, scrapedthumbnail, scrapedtitle, cantidad in matches:
        scrapedplot = ""
        scrapedtitle = "%s (%s)"  %(scrapedtitle, cantidad)
        itemlist.append(item.clone(action="lista", title=scrapedtitle, url=scrapedurl,
                              fanart=scrapedthumbnail, thumbnail=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data,'<li><a class="pag-next" href="(.*?)">Next &gt;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist    


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    data = scrapertools.find_single_match(data,'class="thumbs-container">(.*?)<div class="clearfix">')
    patron  = '<p class="btime">([^<]+)<(.*?)'
    patron += '<img width=.*?'
    patron += 'src="([^"]+)" class="thumb.*?'
    patron += 'title="([^"]+)".*?'
    patron += 'href="([^"]+)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for duracion,calidad,scrapedthumbnail,scrapedtitle,scrapedurl in matches:
        url = scrapedurl
        title = "[COLOR yellow]%s[/COLOR] %s" % (duracion, scrapedtitle)
        if ">HD<" in calidad:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (duracion, scrapedtitle)
        thumbnail = scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title , url=url, thumbnail=thumbnail,
                              fanart=scrapedthumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data,'<li><a class="pag-next" href="(.*?)">Next &gt;</a>')
    if next_page!="":
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<video src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        scrapedurl = scrapedurl.replace("https:", "http:")
        scrapedurl += "|Referer=%s" % host
        itemlist.append(item.clone(action="play", title="Directo", url=scrapedurl))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron  = '<video src="([^"]+)"'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl  in matches:
        scrapedurl = scrapedurl.replace("https:", "http:")
        scrapedurl += "|Referer=%s" % host
        itemlist.append(item.clone(action="play", contentTitle=item.title, url=scrapedurl))
    return itemlist