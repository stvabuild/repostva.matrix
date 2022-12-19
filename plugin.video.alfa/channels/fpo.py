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

canonical = {
             'channel': 'fpo', 
             'host': config.get_setting("current_host", 'fpo', default=''), 
             'host_alt': ["https://www.fpo.xxx/"], 
             'host_black_list': [], 
             'pattern': ['href="?([^"|\s*]+)["|\s*]\s*rel="?stylesheet"?'], 
             'set_tls': True, 'set_tls_min': True, 'retries_cloudflare': 1, 'cf_assistant': False, 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
                                             
    itemlist.append(Item(channel=item.channel, title="Nuevos" , action="lista", url=host + "latest-updates/?sort_by=post_date&from=01"))
    itemlist.append(Item(channel=item.channel, title="Mas vistos" , action="lista", url=host + "most-popular/?sort_by=video_viewed_month&from=01"))
    itemlist.append(Item(channel=item.channel, title="Mejor valorado" , action="lista", url=host + "top-rated/?sort_by=rating_month&from=01"))
    itemlist.append(Item(channel=item.channel, title="Mas metraje" , action="lista", url=host + "longest/?sort_by=duration&from=01"))
    itemlist.append(Item(channel=item.channel, title="PornStar" , action="categorias", url=host + "models/?sort_by=avg_videos_popularity&from=01"))

    itemlist.append(Item(channel=item.channel, title="Categorias" , action="categorias", url=host + "categories/?sort_by=title"))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "-")
    item.url = "%ssearch/%s/?sort_by=post_date&from=01" % (host,texto)
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
    matches = soup.find_all('a', class_='item')
    for elem in matches:
        url = elem['href']
        title = elem['title']
        if elem.img:
            thumbnail = elem.img['src']
        else:
            thumbnail = ""
        cantidad = elem.find('div', class_='videos')
        if cantidad:
            title = "%s (%s)" % (title,cantidad.text.strip())
        url = urlparse.urljoin(item.url,url)
        url += "?is_hd=&sort_by=post_date&from=01"
        thumbnail = urlparse.urljoin(item.url,thumbnail)
        plot = ""
        itemlist.append(Item(channel=item.channel, action="lista", title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['data-parameters'].replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="categorias", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()
    if referer:
        data = httptools.downloadpage(url, headers={'Referer': referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data
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
        title = elem.a['title']
        thumbnail = elem.img['data-original']
        time = elem.find('span', class_='duration').text.strip()
        quality = elem.find('span', class_='is-hd')
        if quality:
            title = "[COLOR yellow]%s[/COLOR] [COLOR red]HD[/COLOR] %s" % (time,title)
        else:
            title = "[COLOR yellow]%s[/COLOR] %s" % (time,title)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(Item(channel=item.channel, action=action, title=title, url=url,
                             fanart=thumbnail, thumbnail=thumbnail , plot=plot) )
    next_page = soup.find('li', class_='next')
    if next_page:
        next_page = next_page.a['data-parameters'].replace(":", "=").replace(";", "&").replace("+from_albums", "")
        next_page = "?%s" % next_page
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(Item(channel=item.channel, action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    soup = create_soup(item.url).find('div', class_='info')
    matches = soup.find_all('div', class_='item')
    pornstars = matches[2].find_all('a')
    for x , value in enumerate(pornstars):
        pornstars[x] = value.text.strip()
    pornstar = ' & '.join(pornstars)
    pornstar = "[COLOR cyan]%s[/COLOR]" % pornstar
    lista = item.title.split()
    if "HD" in item.title:
        lista.insert (4, pornstar)
    else:
        lista.insert (2, pornstar)
    item.title = ' '.join(lista)
    itemlist.append(Item(channel=item.channel, action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
