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

host = 'https://pornone.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/newest/"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/views/month/"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/rating/month/"))
    itemlist.append(item.clone(title="Mas comentado" , action="lista", url=host + "/comments/month/"))
    itemlist.append(item.clone(title="Mas metraje" , action="lista", url=host + "/longest/month/"))
    itemlist.append(item.clone(title="Female" , action="lista", url=host + "/female/newest/"))
    itemlist.append(item.clone(title="Shemale" , action="lista", url=host + "/shemale/newest/"))
    itemlist.append(item.clone(title="Gay" , action="lista", url=host + "/gay/newest/"))
    itemlist.append(item.clone(title="PornStar" , action="categorias", url=host + "/pornstars/"))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search?q=%s&sort=newest&page=1" % (host,texto)
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
    if "pornstars" in item.url:
        matches = soup.find_all('div', class_='star')
    else:
        matches = soup.find('div', id='cats-show').find_all('div', class_='categories')[-1]
        matches = matches.find_all('a')
    for elem in matches:
        if "pornstars" in item.url:
            url = elem.a['href']
        else:
            url = elem['href']
        title = elem.img['alt'].replace('category ', '')
        thumbnail = elem.img['src']
        cantidad = elem.find('span', class_='videos')
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        url = urlparse.urljoin(item.url,url)
        url += "newest/"
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
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
    matches = soup.find_all(class_='time')
    for elem in matches:
        elem = elem.find_parent('a')
        url = elem['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        time = elem.find('span', class_='time').text.strip()
        quality = elem.find('span', class_='is-hd')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', class_='next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    if "search" in item.url:
        next_page = soup.find('span', class_='next')
        if next_page:
            page = scrapertools.find_single_match(item.url, '(.*?)&page=')
            next_page = next_page['onclick']
            next_page = re.sub("\D", "", next_page)
            next_page = "%s&page=%s" %(page, next_page)
            itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).video
    matches = soup.find_all('source')
    for elem in matches:
        url = elem['src']
        quality = elem['label']
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    return itemlist


def play(item):
    logger.info()
    video_urls = []
    soup = create_soup(item.url).video
    matches = soup.find_all('source')
    for elem in matches:
        url = elem['src']
        quality = elem['label']
        video_urls.append(['%s' %quality, url])
    video_urls.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    return video_urls