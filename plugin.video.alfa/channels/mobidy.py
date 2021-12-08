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

from channels import autoplay
from platformcode import config, logger, platformtools
from core.item import Item
from core import httptools, scrapertools, jsontools, tmdb
from core import servertools, channeltools
from channels import filtertools

from bs4 import BeautifulSoup
from channelselector import get_thumb

host = 'https://www.espapelis.com'     # https://www.movidy.mob
api= host + "/wp-admin/admin-ajax.php"

SERVER = {'uqload.com': 'Uqload' , 'uptobox.com': 'Uptobox',
          'streamsb.net': 'Streamsb', 'dood.so': 'Doodstream', 
          'fastplay.to': 'Fastplay', 'pelistop.co' : 'Streamsb'
         }


IDIOMAS = {"es": "CAST", "mx": "LAT", "lat": "LAT", "en": "VOSE"}

list_language = list(IDIOMAS.values())
list_quality = []
list_servers = list(SERVER.values())

__channel__='mobidy'

parameters = channeltools.get_channel_parameters(__channel__)
unif = parameters['force_unify']


def mainlist(item):
    logger.info()
    itemlist = []
    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(item.clone(title="Peliculas" , action="lista", type="movie", 
                               post="action=action_load_pagination_home&number=18&paged=1&postype=movie", thumbnail=get_thumb("movies", auto=True)))
    itemlist.append(item.clone(title="Genero" , action="categorias", url= host +"/peliculas/", thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(item.clone(title="Buscar...", action="search", thumbnail=get_thumb("search", auto=True)))
    
    autoplay.show_option(item.channel, itemlist)
    return itemlist


def search(item, texto):
    logger.info()
    try:
        texto = texto.replace(" ", "+")
        item.url = "%s/?s=%s" % (host, texto)
        if texto != "":
            return lista(item)
        else:
            return []
    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def categorias(item):
    logger.info()
    itemlist = []
    soup = get_source(item.url, soup=True).find('div', class_='filter-genres')
    matches= soup.find_all('li')
    for elem in matches:
        # id = elem.input['value']
        # post = "action=action_filter&number=10&paged=1&genre[]=%s" %id
        title = elem.text.strip()
        name = scrapertools.slugify(title).lower()
        url = "%s/category/%s" %(host, name.decode("utf8"))
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=get_thumb("movies", auto=True)) )
    return itemlist


def get_source(url, soup=False, json=False, unescape=False, **opt):
    logger.info()
    data = httptools.downloadpage(url, **opt)
    if json:
        data = data.json
    else:
        data = data.data
        data = scrapertools.unescape(data) if unescape else data
        data = BeautifulSoup(data, "html5lib", from_encoding="utf-8") if soup else data
    return data


def lista(item):
    logger.info()
    itemlist = []
    if item.post:
        soup = get_source(api, soup=True, post=item.post)
        numitem = 0
    else:
        soup = get_source(item.url, soup=True)
    matches= soup.find_all('article')
    for elem in matches:
        if item.post:
            numitem += 1
        url = elem.a['href']
        thumbnail = elem.img['src']
        title = elem.h2.text.strip()
        contentTitle = title
        year = '-'
        if not config.get_setting('unify') and not channeltools.get_channel_parameters(__channel__)['force_unify']:
            if year != "-":
                title = "%s [COLOR cyan](%s)[/COLOR]" % (title,year)
        else:
            title = title
        itemlist.append( Item(channel=item.channel, action = "findvideos", url = url, title=title, contentTitle = contentTitle,
                        thumbnail=thumbnail, infoLabels={"year": year}))
    tmdb.set_infoLabels(itemlist, True)
    next_page = soup.find('a', class_='nextpostslink')
    if next_page:
        next_page = next_page['href']
        next_page = urlparse.urljoin(item.url,next_page)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    elif item.post and numitem == 18:
        next_page = scrapertools.find_single_match(item.post, "&paged=(\d+)")
        next_page = int(next_page) + 1
        next_page = re.sub(r"&paged=\d+", "&paged={0}".format(next_page), item.post)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", post=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    soup = get_source(item.url, soup=True)
    matches=soup.find('div', class_='servers-options').find_all('li')
    for elem in matches:
        url = elem['data-playerid']
        title = elem.text.strip()
        if "HD" in title:
            quality = "HD"
        flag = elem.img['src']
        lang = scrapertools.find_single_match(flag, "(\w+).png")
        lang = IDIOMAS.get(lang, lang)
        server = scrapertools.find_single_match(url, "https://(.*?)/")
        server = SERVER.get(server,server)
        itemlist.append(item.clone(action="play", title=title, url=url, server=server, language=lang, quality=quality))
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)
    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra !='findvideos' and not "/episodios/" in item.url :
        itemlist.append(item.clone(action="add_pelicula_to_library", 
                             title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]', url=item.url,
                             extra="findvideos", contentTitle=item.contentTitle)) 
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    logger.debug("ITEM: %s" % item)
    itemlist = servertools.get_servers_itemlist([item.clone(url=item.url, server="")])
    itemlist = servertools.get_servers_itemlist(itemlist)
    return itemlist
