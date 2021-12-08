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

host = 'https://www.fapcandy.com'  # 'https://www.streamate.com
cat = "https://member.naiadsystems.com/search/v3/categories?domain=fapcandy.com&shouldIncludeTransOnStraightSkins=false"
api = "https://member.naiadsystems.com/search/v3/performers?domain=fapcandy.com&from=0&size=100&filters=gender:f,ff,mf,tm2f,g;online:true&genderSetting=f"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Chicas" , action="categorias", url=cat, chicas = True))
    itemlist.append(item.clone(title="Chicos" , action="categorias", url=cat))
    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = naiadsystems(item.url)
    if item.chicas:
        data = data["groups"][0]
        filter = "gender:f,ff,mf,tm2f,g"
        
    else:
        data = data["groups"][1]
        filter = "gender:m,mm,tf2m,g"
    for elem in data["categories"]:
        name = elem["name"]
        cantidad = elem["liveCount"]
        thumbnail = ""
        title = "%s (%s)" % (name,cantidad)
        if "allgirls" in name or "allguys" in name:
            cat = filter
        else:
            cat = "category:%s;%s" % (name, filter)
        url = "https://member.naiadsystems.com/search/v3/performers?domain=fapcandy.com&from=0&size=40&filters=%s;online:true&genderSetting=f" % cat
        itemlist.append(item.clone(action="lista", title=title, url=url, thumbnail=thumbnail, fanart=thumbnail ))
    return itemlist


def naiadsystems(url, post=None):
    logger.info()
    UA = 'Mozilla/5.0 (X11; Linux i686) AppleWebKit/535.1 ' + \
         '(KHTML, like Gecko) Chrome/13.0.782.99 Safari/535.1'
    headers = {"platform": "SCP",
               "smtid": "ffffffff-ffff-ffff-ffff-ffffffffffffG0000000000000",
               "smeid": "ffffffff-ffff-ffff-ffff-ffffffffffffG0000000000000",
               "smvid": "ffffffff-ffff-ffff-ffff-ffffffffffffG0000000000000",
               "User-Agent": UA}
    if post:
        data = httptools.downloadpage(url, post=post,  headers=headers).json
    else:
        data = httptools.downloadpage(url, headers=headers).json

    return data


def lista(item):
    logger.info()
    itemlist = []
    data = naiadsystems(item.url)
    total = data['totalResultCount']
    for elem in data['performers']:
        thumbnail = "http://m1.nsimg.net/media/snap/{0}.jpg".format(elem['id'])
        name = elem['nickname']
        age = elem['age']
        country = elem['country']
        quality = 'HD' if elem['highDefinition'] else ''
        title = "%s [%s] (%s)" %(name,age,country)
        url = " https://manifest-server.naiadsystems.com/live/s:%s.json?last=load&format=mp4-hls" % name
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url, thumbnail=thumbnail,
                                   fanart=thumbnail, contentTitle=title ))
    page = scrapertools.find_single_match(item.url, '&from=(\d+)')
    page = int(page)
    if total > page  and (total - page) > 40:
        page += 40
        next_page = re.sub(r"&from=\d+", "&from={0}".format(page), item.url)
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=next_page) )
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    data = data["formats"]["mp4-hls"]
    for elem in data["encodings"]:
        quality = elem["videoHeight"]
        url = elem["location"]
        itemlist.append(item.clone(action="play",url=url, title=quality, quality=quality))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).json
    data = data["formats"]["mp4-hls"]
    for elem in data["encodings"]:
        quality = elem["videoHeight"]
        url = elem["location"]
        itemlist.append(['%sp' %quality, url])
    itemlist.sort(key=lambda item: int( re.sub("\D", "", item[0])))
    # autoplay.start(itemlist, item)
    return itemlist


