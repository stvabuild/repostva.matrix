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

host = 'https://pornktube.vip'     # https://www.pornktu.be/videos/ https://www.tubxxporn.com   'https://www.pornky.com'  'https://www.joysporn.com/'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/latest-updates/"))
    itemlist.append(item.clone(title="Popular" , action="lista", url=host + "/most-popular/"))
    itemlist.append(item.clone(title="Mejor valorada" , action="lista", url=host + "/top-rated/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/?q=%s" % (host,texto)
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
    patron = '<div class="cat">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    patron += '>([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,thumbnail,scrapedtitle in matches:
        title = scrapedtitle
        url = scrapedurl
        thumbnail += "|Referer=%s" % host
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail, fanart=thumbnail, plot=plot) )
    return sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<div class="vid_info">.*?'
    patron += '<a href="([^"]+)".*?'
    patron += 'src="([^"]+)" alt="([^"]+)".*?'
    patron += '<div class="vlength">([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedthumbnail,scrapedtitle,scrapedtime in matches:
        title = '[COLOR yellow] %s [/COLOR] %s' % (scrapedtime , scrapedtitle)
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a href="([^"]+)" class="mpages">Next')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    id,s,data,t,server = scrapertools.find_single_match(data, '<div id="player" data-id="(\d+)" data-s="(\d+)" data-q="([^"]+)" data-t="(\d+)" data-n="(\d+)"')
    # s= 113 t=224 fapmedia.com/whpvid/         anterior 
    patron = '&nbsp;([A-z0-9]+);\d+;(\d+);([^,"]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,number,key in matches:
        nt = int(int(id)/1000)
        n = str(nt*1000)
        url = "http://s%s.stormedia.info/whpvid/%s/%s/%s/%s/%s_%s.mp4"   % (server, number, key,n, id, id, quality)
        # url = "http://s%s.stormedia.info/whpvid/%s/%s/%s/%s/%s_%s.mp4" % (server,number,key,n,id,id,quality)
        url= url.replace("_720p", "")
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    id,s,data,t,server = scrapertools.find_single_match(data, '<div id="player" data-id="(\d+)" data-s="(\d+)" data-q="([^"]+)" data-t="(\d+)" data-n="(\d+)"')
    # s= 113 t=224 fapmedia.com/whpvid/         anterior 
    patron = '&nbsp;([A-z0-9]+);\d+;(\d+);([^,"]+)'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for quality,number,key in matches:
        nt = int(int(id)/1000)
        n = str(nt*1000)
        url = "http://s%s.stormedia.info/whpvid/%s/%s/%s/%s/%s_%s.mp4"   % (server, number, key,n, id, id, quality)
        # url = "http://s%s.stormedia.info/whpvid/%s/%s/%s/%s/%s_%s.mp4" % (server,number,key,n,id,id,quality)
        url= url.replace("_720p", "")
        itemlist.append(['%s' %quality, url])
    return itemlist