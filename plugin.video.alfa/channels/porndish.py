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

from platformcode import config, logger, platformtools
from core import scrapertools
from core import servertools
from core.item import Item
from core import httptools
from bs4 import BeautifulSoup
from channels import filtertools
from channels import autoplay
from lib import alfa_assistant
import ssl

IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = ['gounlimited']

host = 'https://www.porndish.com/'

def mainlist(item):
    if ssl.OPENSSL_VERSION_INFO < (1, 1, 1):
        if not alfa_assistant.open_alfa_assistant():
            platformtools.dialog_ok("Alfa Assistant: Error", "NECESITAS la app Alfa Assistant para ver este canal")
            return
    logger.info()
    itemlist = []
    
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=host))
    itemlist.append(item.clone(title="Canal" , action="sub_menu", url=host))
    itemlist.append(item.clone(title="Buscar", action="search"))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/search/%s" % (host,texto)
    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def sub_menu(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Bangbros" , action="categorias", url=host, id="menu-item-62819"))
    itemlist.append(item.clone(title="Brazzers" , action="categorias", url=host, id="menu-item-817"))
    itemlist.append(item.clone(title="Mofos" , action="categorias", url=host, id="menu-item-1707"))
    itemlist.append(item.clone(title="Pornpros" , action="categorias", url=host, id="menu-item-3774"))
    itemlist.append(item.clone(title="Realitykings" , action="categorias", url=host, id="menu-item-844"))
    itemlist.append(item.clone(title="Sis Loves Me" , action="lista", url=host + "videos4/sislovesme/"))
    itemlist.append(item.clone(title="Teamskeet" , action="categorias", url=host, id="menu-item-1713"))
    itemlist.append(item.clone(title="Networks" , action="categorias", url=host, id="menu-item-23036"))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('li', id=item.id)
    matches = soup.find_all('a')
    # matches = soup.find_all('li', class_='menu-item-object-category')
    for elem in matches:
        url = elem['href']
        title = elem.text
        plot = ""
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    return itemlist



def create_soup(url):
    logger.info()
    data = ""
    if ssl.OPENSSL_VERSION_INFO >= (1, 1, 1):
        response = httptools.downloadpage(url, ignore_response_code=True)
        if response.sucess:
            data = response.data
    elif alfa_assistant.open_alfa_assistant():
        data = alfa_assistant.get_source_by_page_finished(url, 5, closeAfter=True)
        if not data:
            platformtools.dialog_ok("Alfa Assistant: Error", "ACTIVE la app Alfa Assistant para continuar")
            data = alfa_assistant.get_source_by_page_finished(url, 5, closeAfter=True)
            if not data:
                return False
        data = alfa_assistant.find_htmlsource_by_url_pattern(data, url)
        if isinstance(data, dict):
            data = data.get('source', '')
            if not data:
                return False
    if data:
        soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
        return soup
    
    return False
    


def lista(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    matches = soup.find_all('article', class_='entry-tpl-grid')
    for elem in matches:
        url = elem.a['href']
        title = elem.img['alt']
        thumbnail = elem.img['src']
        plot = ""
        itemlist.append(item.clone(action="findvideos", title=title, contentTitle=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot=plot,))
    try:
        if "search" in item.url:
            next_page = soup.find('a', class_='next')['href']
        else:
            next_page = soup.find('link', rel='next')['href']
            # next_page = soup.find('a', class_='g1-load-more')['data-g1-next-page-url']
    except:
        next_page = None
    if next_page:
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page.strip()))
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url)
    if not soup:
        return itemlist
    soup = soup.find('div', class_='entry-content')
    matches = soup.find_all('p')
    for elem in matches:
        url = elem.find('iframe')
        if url:
            url= url['src']
            itemlist.append(item.clone(action="play", title= "%s" , contentTitle=item.title, url=url)) 
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize()) 
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language, list_quality)
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    return itemlist

