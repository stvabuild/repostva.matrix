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
from channels import filtertools
from channels import autoplay

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['gounlimited']

host = 'http://www.veporno.net'  #  https://www.fxporn.net      http://www.veporns.com    


def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/month"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/top-videos"))
    itemlist.append(item.clone(title="PornStar" , action="catalogo", url=host + "/pornstars"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories"))
    itemlist.append(item.clone(title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/porn/%s/" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def catalogo(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li><a href="([^"]+)" class="thumb" title="([^"]+)".*?'
    patron += 'image:url\(([^\)]+)\).*?'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        title=scrapedtitle
        thumbnail = scrapedthumbnail
        url = scrapedurl
        itemlist.append(item.clone(action="lista2", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = scrapertools.find_single_match(data, '<a class="active".*?<a class="" href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<ul style="margin-top:-10px;"><li><a href="([^"]+)" title="([^"]+) Porn Videos"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle in matches:
        title = scrapedtitle
        thumbnail = ""
        url = urlparse.urljoin(host,scrapedurl)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return sorted(itemlist, key=lambda i: i.title)

def lista2(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li><img class="small_video_img" src="([^"]+)".*?'
    patron += '<a href="([^"]+)" class="thumb" title="([^"]+)">.*?'
    patron += '>([^<]+)<'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedthumbnail,scrapedurl,scrapedtitle,time in matches:
        title = "[COLOR yellow]%s[/COLOR] %s" % (time, scrapedtitle)
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<a class="active".*?<a class="" href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista2", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = '<li class="dvd-new".*?<a href="([^"]+)".*?'
    patron += 'title="([^"]+)".*?image:url\(([^")]+)\)"'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail in matches:
        title = scrapedtitle.strip()
        thumbnail = scrapedthumbnail
        url = urlparse.urljoin(item.url,scrapedurl)
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
                              # porstar paginacion
    next_page = scrapertools.find_single_match(data, '<a class="active".*?<a class="" href="([^"]+)">')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    patron = 'onClick="toplay\((.*?)\).*?>Mirror'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url in matches:
        url = url.replace("'", "").split(",")
        url = "%s/ajax.php?page=video_play&thumb=%s&theme=%s&video=%s&id=%s&catid=%s&tip=%s&server=%s" %(host,url[0],url[1],url[2],url[3],url[4],url[5],str(url[6]))
        headers = {"X-Requested-With":"XMLHttpRequest"}
        data = httptools.downloadpage(url, headers=headers).data
        url = scrapertools.find_single_match(data, '<iframe src="([^"]+)"')
        if not url:
            url = scrapertools.find_single_match(data, "<iframe src='([^']+)'")
        itemlist.append(item.clone(action="play", title= "%s", contentTitle= item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

