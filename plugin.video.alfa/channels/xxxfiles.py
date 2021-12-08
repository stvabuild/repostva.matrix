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

host = 'https://www.xxxfiles.com'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/latest-updates/"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/most-popular/"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/top-rated/"))
    itemlist.append(item.clone(title="PornStar" , action="catalogo", url=host + "/models/most-viewed/"))
    itemlist.append(item.clone(title="Canal" , action="canal", url=host + "/sites/"))

    itemlist.append(item.clone(title="Categorias" , action="categorias", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s/" % (host,texto)
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
    matches = soup.find('div', class_='main__row').find_all('div', class_='main__row')
    for elem in matches:
        url = elem.find('div', class_='block-related__bottom').a['href']
        title = elem.find('h2').text.strip()
        url = urlparse.urljoin(item.url,url)
        thumbnail = ""
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', string='Next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="canal", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist
    

def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find('div', class_='letter-block').find_all('div', class_='letter-block__item')
    for elem in matches:
        url = elem.a['href']
        title = elem.find('span').text
        url = urlparse.urljoin(item.url,url)
        thumbnail = ""
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail , plot=plot) )
    return itemlist

def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='thumb')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        url = urlparse.urljoin(item.url,url)
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('a', string='Next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    matches = soup.find_all('div', class_='thumb item')
    for elem in matches:
        url = elem.a['href']
        thumbnail = elem.img['src']
        stime = elem.find('span', class_='thumb__duration').text.strip()
        stitle = elem.find('div', class_='thumb__title').text.strip()
        quality = elem.find('span', class_='thumb__bage').text.strip()
        pornstars = elem.find('div', class_='thumb-models').find_all('a')
        for x , value in enumerate(pornstars):
            pornstars[x] = value.text.strip()
        pornstar = ' & '.join(pornstars)
        if not "Suggest" in pornstar:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] [COLOR cyan]%s[/COLOR] %s" % (stime,quality,pornstar,stitle)
        else:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (stime,quality,stitle)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
    next_page = soup.find('a', string='Next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('source', type='video/mp4')
    for elem in matches:
        url = elem['src']
        quality = elem['label']
        itemlist.append(item.clone(action="play", title=quality, url=url) )
    return itemlist[::-1]


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('source', type='video/mp4')
    for elem in matches:
        url = elem['src']
        quality = elem['label']
        itemlist.append(['.mp4 %s' %quality, url])
    return itemlist[::-1]
