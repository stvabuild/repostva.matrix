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

host = 'http://www.veporno.net'  # http://www.veporno.net    https://www.fxporn.net http://www.gameofporn.net


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/videos/1"))
    itemlist.append(item.clone(title="Top" , action="lista", url=host + "/top-videos"))
    itemlist.append(item.clone(title="New PornStar" , action="catalogo", url=host + "/pornstars"))
    itemlist.append(item.clone(title="Top PornStar" , action="catalogo", url=host + "/pornstars?sort=rank"))

    itemlist.append(item.clone(title="Sitios" , action="categorias", url=host + "/categories"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/porn/%s" % (host, texto)
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
    soup = create_soup(item.url).find('div', class_='box')
    matches = soup.find_all('li')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.a['style']
        thumbnail = scrapertools.find_single_match(thumbnail, 'url\(([^\)]+)')
        itemlist.append(item.clone(action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail ))
    next_page = soup.find('p', class_='sayfalama').find('a', class_='active')
    if next_page:
        next_page = next_page.find_next_sibling("a")['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='content')
    matches = soup.find_all('li')
    for elem in matches:
        url = elem.a['href']
        title = elem.text
        url = urlparse.urljoin(host,url)
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url, fanart=thumbnail, thumbnail=thumbnail ))
    return sorted(itemlist, key=lambda i: i.title)


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}).data
    else:
        data = httptools.downloadpage(url).data
        data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    return soup


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if "/star/" in item.url:
        matches = soup.find('div', class_='videos').find_all('li')
    else:
        matches = soup.find('div', class_='box').find_all('li', class_='dvd-new')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        if elem.find('img'):
            thumbnail = elem.img['src']
        else:
            thumbnail = elem.a['style']
            thumbnail = scrapertools.find_single_match(thumbnail, 'url\(([^\)]+)')
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, contentTitle=title, fanart=thumbnail, thumbnail=thumbnail ))
    next_page = soup.find('p', class_='sayfalama').find('a', class_='active')
    if next_page:
        next_page = next_page.find_next_sibling("a")
        if next_page:
            next_page = next_page['href']
            next_page = urlparse.urljoin(item.url,next_page)
            itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    matches =scrapertools.find_single_match(data,'onClick="toplay\((.*?)\)')
    matches = matches.replace("'", "")
    link = matches.split(",")
    url = "%s/ajax.php?page=video_play&thumb=%s&theme=%s&video=%s&id=%s&catid=%s&tip=%s&server=%s" % (host,link[0],link[1],link[2],link[3],link[4],link[5],link[6])
    headers = {'Referer': item.url, 'X-Requested-With': 'XMLHttpRequest'}
    data = httptools.downloadpage(url, headers=headers).data
    url = scrapertools.find_single_match(data,'<iframe src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    matches =scrapertools.find_single_match(data,'onClick="toplay\((.*?)\)')
    matches = matches.replace("'", "")
    link = matches.split(",")
    url = "%s/ajax.php?page=video_play&thumb=%s&theme=%s&video=%s&id=%s&catid=%s&tip=%s&server=%s" % (host,link[0],link[1],link[2],link[3],link[4],link[5],link[6])
    headers = {'Referer': item.url, 'X-Requested-With': 'XMLHttpRequest'}
    data = httptools.downloadpage(url, headers=headers).data
    url = scrapertools.find_single_match(data,'<iframe src="([^"]+)"')
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
