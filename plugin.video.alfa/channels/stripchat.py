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


IDIOMAS = {'vo': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = ['default']
list_servers = []


host = 'https://stripchat.com'
hosta = 'https://stripchat.com/api/front/models?limit=40&offset=0&sortBy=stripRanking&primaryTag=%s&filterGroupTags=[["%s"]]'
    # 'https://stripchat.com/api/external/v4/widget/?limit=100&modelsCountry=&modelsLanguage=&modelsList=&tag=%s'
cat = 'https://es.stripchat.com/api/front/models?limit=40&primaryTag=girls&filterGroupTags=[[%22BigTits%22]]&sortBy=stripRanking'


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Female" , action="lista", url=hosta %("girls", "")))
    itemlist.append(item.clone(title="Couples" , action="lista", url=hosta % ("couples", "")))
    itemlist.append(item.clone(title="Male" , action="lista", url=hosta % ("men", "")))
    itemlist.append(item.clone(title="Transexual" , action="lista", url=hosta % ("trans", "")))
    itemlist.append(item.clone(title="Categorias" , action="categorias", url=cat))
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


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    for elem in data['liveTagGroups']:
        logger.debug(elem['tags'])
        for list in elem['tags']:
            title = re.sub(r"tagLanguage|autoTag|age|ethnicity|privatePrice|specifics|specific|^do|subculture", "", list) # |bodyType|hairColor
            title = title.capitalize()
            url = hosta %("girls", list)
            thumbnail = ""
            plot = ""
            itemlist.append(item.clone(action="lista", title=title, url=url,
                                  thumbnail=thumbnail , plot=plot) )
    return sorted(itemlist, key=lambda i: i.title)


def lista(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    # logger.debug(data)
    for elem in data['models']:
        logger.debug(elem)
        # url = elem['stream']['url']
        id = elem['id']
        thumbnail = elem['snapshotUrl']
        title = elem['username']
        url = "https://b-hls-03.strpst.com/hls/%s/%s.m3u8" %(id, id)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, thumbnail=thumbnail, url = url,
                               plot=plot, fanart=thumbnail, contentTitle=title ))
                               
    count= data['filteredCount']
    current_page = scrapertools.find_single_match(item.url, ".*?&offset=(\d+)")
    current_page = int(current_page)
    if current_page <= int(count) and (int(count) - current_page) > 40:
        current_page += 40
        next_page = re.sub(r"&offset=\d+", "&offset={0}".format(current_page), item.url)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    # item.url += "|verifypeer=false"
    itemlist.append(item.clone(action="play", title="Directo", url=item.url ))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    # item.url += "|verifypeer=false"
    itemlist.append(item.clone(action="play", title=item.url, contentTitle = item.title, url=item.url, server="Directo" ))
    return itemlist