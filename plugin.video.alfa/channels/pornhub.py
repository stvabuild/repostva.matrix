# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

from core import httptools
from core import servertools
from core import scrapertools
from core.item import Item
from platformcode import logger
from bs4 import BeautifulSoup

host = 'https://pornhub.com'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="lista", title="Novedades", fanart=item.fanart,
                         url="%s/video?o=cm" %host))
    itemlist.append(item.clone(action="lista", title="Mas visto", fanart=item.fanart,
                         url="%s/video?o=mv" %host))
    itemlist.append(item.clone(action="lista", title="Mejor valorado", fanart=item.fanart,
                         url="%s/video?o=tr" %host))
    itemlist.append(item.clone(action="lista", title="Mas largo", fanart=item.fanart,
                         url="%s/video?o=lg" %host))
    itemlist.append(item.clone(action="catalogo", title="Canal", fanart=item.fanart,
                         url= "%s/channels?o=tr" % host))
    itemlist.append(item.clone(action="catalogo", title="PornStar", fanart=item.fanart,
                         url= "%s/pornstars?o=t" % host))
    itemlist.append(item.clone(action="categorias", title="Categorias", fanart=item.fanart,
                         url= "%s/categories" % host))
    itemlist.append(item.clone(action="search", title="Buscar", fanart=item.fanart))
    return itemlist


def search(item, texto):
    logger.info()

    item.url = "%s/video/search?search=%s&o=mr" % (host, texto)
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
    soup = create_soup(item.url)
    if "channels" in item.url:
        matches = soup.find_all('div', class_='channelsWrapper')
    else:
        matches = soup.find('ul', class_='popular-pornstar').find_all('div', class_='wrap')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.img['alt']
        thumbnail = elem.img['data-thumb_url']
        cantidad = elem.find('span', class_='videosNumber')
        if "channels" in url:
            cantidad = elem.find(string='Videos').parent.text.replace("Videos", "")
            url = urlparse.urljoin(item.url, url + "/videos?o=da")
        else:
            cantidad = elem.find('span', class_='videosNumber').text.split(' Videos')[0]
            url = urlparse.urljoin(item.url, url + "/videos?o=cm")
        title = "%s (%s)" % (stitle,cantidad)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail))
        # Paginador
    next_page = soup.find('li', class_='page_next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='category-wrapper')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.a['data-mxptext']
        thumbnail = elem.img['data-thumb_url']
        cantidad = elem.find('span', class_='videoCount').text.strip()
        if "?" in url:
            url = urlparse.urljoin(item.url, url + "&o=cm")
        else:
            url = urlparse.urljoin(item.url, url + "?o=cm")
        title = "%s %s" % (stitle,cantidad)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail))
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
    if "/pornstar/" in item.url:
        matches = soup.find('ul', id='mostRecentVideosSection').find_all('div', class_='phimage')
    elif "channels" in item.url:
        matches = soup.find('ul', id='showAllChanelVideos').find_all('div', class_='phimage')
    else:
        matches = soup.find('div', class_='gridWrapper').find_all('div', class_='phimage')
    for elem in matches:
        url = elem.a['href']
        stitle = elem.a['title']
        if not elem.find('div', class_='thumbTextPlaceholder'):
            thumbnail = elem.img['data-thumb_url']
        stime = elem.find('var', class_='duration').text
        quality = elem.find('span', class_='hd-thumbnail')
        premium = elem.find('i', class_='premiumIcon')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s"% (stime,quality.text,stitle)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (stime,stitle)
        url = urlparse.urljoin(item.url, url)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        if not premium and not elem.find('div', class_='thumbTextPlaceholder'):
            itemlist.append(item.clone(action=action, title=title, contentTitle = title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail))
    next_page = soup.find('li', class_='page_next')
    if next_page:
        next_page = next_page.a['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info(item)
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s" , contentTitle=item.title, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist


def play(item):
    logger.info(item)
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s" , contentTitle=item.title, url=item.url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    return itemlist

