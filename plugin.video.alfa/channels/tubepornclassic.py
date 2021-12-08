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

from core import jsontools as json
from platformcode import config, logger
from core import scrapertools
from core.item import Item
from core import servertools
from core import httptools

host = 'https://tubepornclassic.com'
url_api = host + "/api/json/videos/14400"


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(title="Nuevos" , action="lista", url=url_api + "/str/latest-updates/60/..1.all...json"))
    itemlist.append(item.clone(title="Mas vistos" , action="lista", url=url_api + "/str/most-viewed/60/..1.all..day.json"))
    itemlist.append(item.clone(title="Mejor valorado" , action="lista", url=url_api + "/str/top-rated/60/..1.all..day.json"))
    itemlist.append(item.clone(title="PornStar" , action="catalogo", url=host + "/api/json/models/86400/str/filt........../most-popular/65/1.json"))
    itemlist.append(item.clone(title="Categorias" , action="categoria", url=host + "/api/json/categories/14400/str.all.en.json"))
    itemlist.append(item.clone(title="Buscar", action="search"))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = "%s/api/videos.php?params=259200/str/relevance/60/search..1.all..&s=%s&sort=latest-updates" % (host, texto)
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
    headers = {'Referer': host }
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    JSONData = json.load(data)
    for Video in  JSONData["models"]:
        dir =  Video["dir"]
        title = Video["title"]
        thumbnail = Video["img"]
        id = dir[:2]
        url = host + "/api/json/model/3600/%s/%s.json" %(id,dir)
        itemlist.append(item.clone(action="actriz", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    pages = JSONData["total_count"]
    pages = round(int(pages)/65.0)
    Actual = int(scrapertools.find_single_match(item.url, '65/(\d+)'))
    if pages > Actual:
        url = item.url.replace("%s.json" % str(Actual), "%s.json" % str(Actual + 1))
        itemlist.append(item.clone(action="catalogo", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=url))
    return itemlist


def actriz(item):
    logger.info()
    itemlist = []
    headers = {'Referer': host }
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    id = scrapertools.find_single_match(data, '"model_id":"(\d+)"')
    url = url_api + "/str/latest-updates/42/model.%s.1.all...json" %id
    actress_item =(item.clone(action="", url=url))
    itemlist = lista(actress_item)
    return itemlist


def categoria(item):
    logger.info()
    itemlist = []
    headers = {'Referer': host }
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    JSONData = json.load(data)
    for Video in  JSONData["categories"]:
        dir =  Video["dir"]
        title = Video["title"]
        cantidad =  Video["total_videos"]
        title = "%s (%s)" %(title, cantidad)
        url = url_api + "/str/latest-updates/60/categories.%s.1.all..day.json" %dir
        thumbnail = ""
        itemlist.append(item.clone(action="lista", title=title, url=url,
                              fanart=thumbnail, thumbnail=thumbnail, plot="") )
    return itemlist


def lista(item):
    logger.info()
    itemlist = []
    headers = {'Referer': host }
    data = httptools.downloadpage(item.url, headers=headers).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|<br/>", "", data)
    JSONData = json.load(data)
    for Video in  JSONData["videos"]:
        id = Video["video_id"]
        dir =  Video["dir"]
        title = Video["title"]
        thumbnail = Video["scr"]
        time =  Video["duration"]
        quality =  Video["props"]
        if quality:
            quality ="HD"
        else:
            quality = ""
        url = "%s/videos/%s/%s/" %(host, id,dir)
        title = "[COLOR yellow]%s[/COLOR] [COLOR red]%s[/COLOR] %s" % (time, quality, title)
        plot = ""
        action = "play"
        if logger.info() == False:
            action = "findvideos"
        itemlist.append(item.clone(action=action, title=title, url=url,
                              thumbnail=thumbnail, fanart=thumbnail, plot=plot, contentTitle = title))
    pages = JSONData["total_count"]
    if "model" in item.url:
        pages = round(int(pages)/40.0)
    else:
        pages = round(int(pages)/60.0)
    Actual = int(scrapertools.find_single_match(item.url, '\.(\d+)\.all'))
    if pages > Actual:
        url = item.url.replace(".%s.all" % str(Actual), ".%s.all" % str(Actual + 1))
        itemlist.append(item.clone(action="lista", title="[COLOR blue]Página Siguiente >>[/COLOR]", url=url))
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def play(item):
    logger.info()
    itemlist = []
    itemlist.append(item.clone(action="play", title= "%s", contentTitle = item.title, url=item.url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist
