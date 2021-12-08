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
from bs4 import BeautifulSoup

host = 'http://porn4days.biz/'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "newest/page1"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "popullar/page1"))
    itemlist.append(item.clone(title="Canal" , action="canal", url=host + "paysitelist"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "tags"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/page1/?s=%s" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def canal(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='col-lg-3')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text
        url = urlparse.urljoin(host,url)
        thumbnail = ""
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='col-lg-3')
    for elem in matches:
        url = elem.a['href']
        thumbnail = elem.img['src']
        title = elem.img['alt']
        url = urlparse.urljoin(host,url)
        thumbnail = urlparse.urljoin(host,thumbnail)
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
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
    matches = soup.find_all('div', class_='col-lg-3')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        time = elem.find('div', class_='timer')
        if time:
            time = time.text.strip()
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        url = urlparse.urljoin(host,url)
        thumbnail = urlparse.urljoin(host,thumbnail)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', rel='next')
    if next_page:
        next_page = next_page['href']
        if "/?s=" in item.url and not"/search/" in next_page:
            next_page = "/search%s" %next_page
        next_page = urlparse.urljoin(host,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    videos = scrapertools.find_multiple_matches(data, '\("#playerframe"\).attr\("src", "([^"]+)"')
    for elem in videos:
        url = elem
        if url:
            itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    data = httptools.downloadpage(item.url).data
    videos = scrapertools.find_multiple_matches(data, '\("#playerframe"\).attr\("src", "([^"]+)"')
    for elem in videos:
        url = elem
        if url:
            itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
