# -*- coding: utf-8 -*-
#------------------------------------------------------------

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re
import os

from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import httptools
from bs4 import BeautifulSoup

host = ''
canonical = {
             'channel': 'sexofilm', 
             'host': config.get_setting("current_host", 'sexofilm', default=''), 
             'host_alt': ["http://sexofilm.com"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]

# SOLOS LOS LINKS DE 2020, todo lo anterior sin videos
# TIMELIG

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Peliculas" , action="lista", url=host + "/xtreme-adult-wing/adult-dvds/"))
    itemlist.append(Item(channel=item.channel, title="Parody" , action="lista", url=host + "/keywords/parodies/"))
    itemlist.append(Item(channel=item.channel, title="Canal" , action="categorias", url=host))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url =host + "/?s=%s" % texto
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
    if item.title == "Canal" :
        data = scrapertools.find_single_match(data,'>Best Porn Studios</a>(.*?)</ul>')
    else:
        data = scrapertools.find_single_match(data,'<div class="nav-wrap">(.*?)<ul class="sub-menu">')
        itemlist.append(Item(channel=item.channel, action="lista", title="Big tit", url="%s/?s=big+tits" %host))
    patron  = '<a href="([^<]+)">([^<]+)</a>'
    matches = re.compile(patron,re.DOTALL).findall(data)
    for scrapedurl,scrapedtitle  in matches:
        itemlist.append(Item(channel=item.channel, action="lista", title=scrapedtitle, url=scrapedurl) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all("article", class_=re.compile(r"^post-\d+"))
    for elem in matches:
        url = elem.a['href']
        title = elem.h2.text.strip()
        thumbnail = elem.img['data-src']
        title = title.replace(" Porn DVD", "").replace("Permalink to ", "").replace(" Porn Movie", "")
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, contentTitle = title, url=url,
                                   fanart=thumbnail, thumbnail=thumbnail, plot=plot) )
    next_page = soup.find('a', class_='nextpostslink')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    url = ""
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'<div class="entry-inner">(.*?)<h4>')
    url = scrapertools.find_single_match(data,'<source src=\'([^\']+)\'')
    if not url:
        url = scrapertools.find_single_match(data,'<source src="([^"]+)"')
    if not url:
        itemlist = servertools.find_video_items(Item(channel=item.channel, url = item.url))
    if url:
        itemlist.append(Item(channel=item.channel, action="play", title= "Directo", url=url, contentTitle = item.title, timeout=40))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    url = ""
    data = httptools.downloadpage(item.url).data
    data = scrapertools.find_single_match(data,'<div class="entry-inner">(.*?)<h4>')
    url = scrapertools.find_single_match(data,'<source src=\'([^\']+)\'')
    if not url:
        url = scrapertools.find_single_match(data,'<source src="([^"]+)"')
    if not url:
        itemlist = servertools.find_video_items(Item(channel=item.channel, url = item.url))
    if url:
        itemlist.append(Item(channel=item.channel, action="play", title= url, url=url, contentTitle = item.title, timeout=45))
    return itemlist