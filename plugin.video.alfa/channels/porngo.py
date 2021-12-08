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

host = 'https://www.porngo.com'

def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host + "/latest-updates/"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=host + "/most-popular/month/"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=host + "/top-rated/month/"))
    itemlist.append(item.clone(title="PornStar" , action="pornstar", url=host + "/models/"))
    itemlist.append(item.clone(title="Canal" , action="canal", url=host))
    itemlist.append(item.clone(title="Categoria" , action="categoria", url=host + "/categories/"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%s/search/%s/" % (host, texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categoria(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='letter-items')
    matches = soup.find_all('div', class_='letter-block__item')
    for elem in matches:
        url = elem.a['href']
        title = elem.a.text.strip()
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return itemlist


def canal(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('ul', class_='nav-menu underline')
    matches = soup.find_all('a', class_='nav-menu__link')
    logger.debug(matches)
    for elem in matches:
        url = elem['href']
        title = elem.text.strip()
        thumbnail = ""
        if not "/sites/" in url:
            url = urlparse.urljoin(item.url,url)
            itemlist.append(item.clone(action="lista", title=title, url=url,
                                  fanart=thumbnail, thumbnail=thumbnail, plot="") )
    
    itemlist.append(item.clone(title="SEXMEX" , action="lista", url=host + "/categories/sexmex/"))
    itemlist.append(item.clone(title="FTV Girls" , action="lista", url=host + "/categories/ftvgirls.com/"))
    itemlist.append(item.clone(title="[COLOR blue]TODOS >>[/COLOR]" , action="catalogo", url=host + "/sites/"))
    return itemlist


def catalogo(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='main__row')
    matches = soup.find_all('div', class_='main__row')
    for elem in matches:
        title = elem.find('div', class_='headline__box').text.strip()
        url = elem.find('div', class_='block-related__bottom')
        cantidad = url.text.strip().replace("Show all ", "")
        url = url.a['href']
        if cantidad:
            title = "%s (%s)" % (title,cantidad)
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = soup.find('a', class_='pagination__link', string='Next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def pornstar(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('div', class_='thumb')
    for elem in matches:
        url = elem.a['href']
        title = elem.a['title']
        thumbnail = elem.img['src']
        cantidad = elem.find('span', class_='thumb__duration').text.strip()
        if cantidad:
            title = "%s (%s)" % (title,cantidad)
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    next_page = soup.find('a', class_='pagination__link', string='Next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="pornstar", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
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
    matches = soup.find_all('div', class_='item')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        time = elem.find('span', class_='thumb__duration').text.strip()
        quality = elem.find('span', class_='thumb__bage')
        reparto = elem.find('div', class_='thumb-models').find_all('a')
        actriz = []
        plot = ""
        for elem in reparto:
            if not "Suggest" in elem.text:
                actriz.append(elem.text)
        actriz = ", ".join(actriz)
        if actriz:
            plot=actriz
            actriz = "%s -" %actriz
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s %s" % (time,quality.text,actriz,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s %s" % (time,actriz,title)
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                                   fanart=thumbnail, contentTitle=title, plot=plot))
    next_page = soup.find('a', class_='pagination__link', string='Next')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('video')
    matches = soup.find_all('source')
    for elem in matches:
        url = elem['src']
        if elem['label']:
            quality = elem['label']
        else:  # Si unica resolucion
            quality= scrapertools.find_single_match(url, '.*?_(\d+)m.mp4/')
            quality += "p"
        itemlist.append(item.clone(action="play", title= quality, quality= quality, url=url))
        # itemlist.append(['%s' % quality, url])
    return itemlist[::-1]


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('video')
    matches = soup.find_all('source')
    for elem in matches:
        url = elem['src']
        if elem['label']:
            quality = elem['label']
        else:  # Si unica resolucion
            quality= scrapertools.find_single_match(url, '.*?_(\d+)m.mp4/')
            quality += "p"
        itemlist.append(['%s' % quality, url])
    return itemlist[::-1]

