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

host = 'https://www.pornky.com'   #   'https://www.tubxxporn.com'  https://www.pornktube.porn  'https://www.joysporn.com/'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/latest-updates/"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/most-popular/"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/top-rated/"))
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
    soup = create_soup(item.url) 
    matches = soup.find_all('div', class_='item')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('h2').text
        thumbnail = elem.img['src']
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    matches = soup.find_all('div', class_='video')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.a['title']
        thumbnail = elem.img['src']
        stime = elem.find('div', class_='duration').text.strip()
        if stime:
            title = "[COLOR yellow]%s[/COLOR] %s" % (stime,stitle)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('div', class_='pages')
    if next_page:
        next_page = next_page.find('span').find_next_sibling('a')['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', id='player')
    id= matches["data-id"]
    server = matches["data-n"]
    data = matches['data-q']
    for elem in data.split(","):
        elem = elem.split(";")
        quality = elem[0]
        pal = elem[-1]
        num = elem[-2]
        vid = int(int(id)/1000)*1000
        # /cqlvid/  /wqlvid/
        url = "https://s%s.stormedia.info/whpvid/%s/%s/%s/%s/%s_%s.mp4"   % (server, num, pal,vid, id,id, quality)
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', id='player')
    id= matches["data-id"]
    server = matches["data-n"]
    data = matches['data-q']
    for elem in data.split(","):
        elem = elem.split(";")
        quality = elem[0]
        pal = elem[-1]
        num = elem[-2]
        vid = int(int(id)/1000)*1000
        # /cqlvid/  /wqlvid/
        url = "https://s%s.stormedia.info/whpvid/%s/%s/%s/%s/%s_%s.mp4"   % (server, num, pal,vid, id,id, quality)
        itemlist.append([quality, url])
    return itemlist
