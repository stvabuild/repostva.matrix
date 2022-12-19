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

canonical = {
             'channel': 'tubedupe', 
             'host': config.get_setting("current_host", 'tubedupe', default=''), 
             'host_alt': ["https://tubedupe.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "/latest-updates/"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorados" , action="lista", url=host + "/top-rated/"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "/most-popular/"))
    itemlist.append(Item(channel=item.channel, title="Modelos" , action="categorias", url=host + "/models/?sort_by=model_viewed"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host + "/channels/?sort_by=cs_viewed"))
    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "/categories/?sort_by=avg_videos_popularity"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
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
    patron = '<div class="block-[^"]+">.*?'
    patron += '<a href="([^"]+)".*?title="([^"]+)".*?'
    patron += 'src="([^"]+)".*?'
    if '/models/' in item.url:
        patron += '<span class="strong">Videos</span>(.*?)</div>'
    else:
        patron += '<var class="duree">([^"]+) </var>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    scrapertools.printMatches(matches)
    for scrapedurl,scrapedtitle,scrapedthumbnail,cantidad  in matches:
        scrapedurl = urlparse.urljoin(item.url,scrapedurl)
        if not scrapedurl.startswith("https"):
            scrapedurl = "https:%s" % scrapedurl
        
        cantidad = cantidad.strip()
        scrapedtitle = "%s (%s)" % (scrapedtitle,cantidad)
        scrapedplot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl,
                              thumbnail=scrapedthumbnail,fanart=scrapedthumbnail, plot=scrapedplot) )
    next_page = scrapertools.find_single_match(data, '<li class="active">.*?<a href="([^"]+)" title="Page')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '<div class="block-video.*?'
    patron += '<a href="([^"]+)" class="[^"]+" title="([^"]+)">.*?'
    patron += '<img src="([^"]+)".*?'
    patron += '<var class="duree">(.*?)</var>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle,scrapedthumbnail,scrapedtime in matches:
        url = urlparse.urljoin(item.url,scrapedurl)
        title = "[COLOR yellow]%s[/COLOR] %s" % (scrapedtime, scrapedtitle)
        thumbnail = scrapedthumbnail
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url, thumbnail=thumbnail,
                              fanart=thumbnail,plot=plot, contentTitle = title))
    next_page = scrapertools.find_single_match(data, '<li class="active">.*?<a href="([^"]+)" title="Page')
    if next_page:
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page ) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '(?:video_url|video_alt_url[0-9]*):\s*\'([^\']+)\'.*?'
    patron += '(?:video_url_text|video_alt_url[0-9]*_text):\s*\'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url,quality in matches:
        itemlist.append(Item(channel=item.channel, action="play", title=quality, url=url) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    patron = '(?:video_url|video_alt_url[0-9]*):\s*\'([^\']+)\'.*?'
    patron += '(?:video_url_text|video_alt_url[0-9]*_text):\s*\'([^\']+)\''
    matches = re.compile(patron,re.DOTALL).findall(data)
    for url,quality in matches:
        itemlist.append(['.mp4 %s' %quality, url])
    return itemlist