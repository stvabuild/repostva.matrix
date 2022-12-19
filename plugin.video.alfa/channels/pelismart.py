# -*- coding: utf-8 -*-

import sys, base64
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import time
if PY3:
    import urllib.parse as urlparse
else:
    import urlparse
from channelselector import get_thumb
from channels import autoplay
from channels import filtertools
from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger


IDIOMAS = {'Latino': 'Latino'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['fembed', 'streamtape', 'doodstream']

canonical = {
             'channel': 'pelismart', 
             'host': config.get_setting("current_host", 'pelismart', default=''), 
             'host_alt': ["https://smartpeli.com/"], 
             'host_black_list': ["https://pelismart.tv/"], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]
__channel__ = canonical['channel']

encoding = None

try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
except:
    __modo_grafico__ = True

max_result = 14


def mainlist(item):
    logger.info()
    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []
    itemlist.append(Item(channel = item.channel, title = "Estrenos", action = "peliculas", url = host + "genero/estrenos", thumbnail = get_thumb("newest", auto = True)))
    itemlist.append(Item(channel = item.channel, title = "Por género", action = "generos", url = host, extra = "Genero", thumbnail = get_thumb("genres", auto = True) ))
    itemlist.append(Item(channel = item.channel, title = ""))
    itemlist.append(Item(channel = item.channel, title = "Buscar", action = "search", url = host, thumbnail = get_thumb("search", auto = True)))
    autoplay.show_option(item.channel, itemlist)
    return itemlist

def peliculas(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, encoding=encoding, canonical=canonical).data
    data = data.replace("&nbsp;","")
    patron  = '(?is)col-mt-5.*?href="([^"]+)'
    patron += '.*?title="([^"]+)'
    patron += '.*?under-title">([^<]+)'
    patron += '.*?src="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedcontentTitle, scrapedthumbnail in matches:
        idioma = "Latino"
        #scrapedthumbnail = scrapedurl
        #scrapedcontentTitle = scrapedurl
        scrapedyear = "-"
        item.infoLabels['year'] = scrapedyear
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = scrapertools.htmlclean(scrapedtitle),
                                   contentTitle = scrapedcontentTitle,
                                   thumbnail = scrapedthumbnail,
                                   url = scrapedurl,
                                   contentType="movie",
                                   language = idioma
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    url_pagina = scrapertools.find_single_match(data, """blog-pager-older-link.*?href='([^']+)""")
    if url_pagina:
        mr = scrapertools.find_single_match(url_pagina, "&max-results=\w+")
        if not url_pagina.endswith("&"): url_pagina += "&"
        url_pagina = url_pagina.replace(mr,"") + "max-results=%s" %max_result
        pagina = "Pagina siguiente"
        itemlist.append(Item(channel = item.channel, action = "peliculas", title = pagina, url = url_pagina))
    return itemlist


def findvideos(item):
    itemlist = []
    matches = []
    data = httptools.downloadpage(item.url, encoding=encoding).data
    patron  = '(?is)#embed.*?src="([^"]+)'
    patron += '.*?(?is)class="([^"]+)'
    matchesurl = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedlang in matchesurl:
        title = scrapedurl
        url = httptools.downloadpage(scrapedurl, follow_redirects=False).headers.get('location', '')
        if  "pelisplus.icu" in url:
            data = httptools.downloadpage(url).data
            matches = scrapertools.find_multiple_matches(data, '"1" data-video="([^"]+)')
            u1 = scrapertools.find_single_match(data, "file: '([^']+)")
            if u1: matches.append(u1)
        else:
            matches = [url]
        for url1 in matches:
            server = ""
            if "damedamehoy" in url1:
                url, id = url1.split("#")
                new_url = "https://damedamehoy.xyz/details.php?v=%s" % id
                v_data = httptools.downloadpage(new_url).json
                url1 = ""
                if v_data["file"]:
                    url1 = [v_data["file"]]
            elif "peliscloud.net" in url1:
                dominio = urlparse.urlparse(url1)[1]
                id = scrapertools.find_single_match(url1, 'id=(\w+)')
                tiempo = int(time.time())
                url1 = "https://" + dominio + "/playlist/" + id + "/%s.m3u8" %tiempo
                data = httptools.downloadpage(url1).data
                url = scrapertools.find_single_match(data, '/hls/\w+/\w+') + "?v=%s" %tiempo
                url1 = "https://" + dominio + url
                data = httptools.downloadpage(url).data
                server = "oprem"
            elif "zplayer" in url1:
                url1 += "|%s" %item.url
            if not url1 or "netu" in url1: continue
            itemlist.append(item.clone(
                            action = "play",
                            language = scrapedlang,
                            title = "%s [" + scrapedlang + "]",
                            server = server,
                            url = url1
                        ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    
    # Requerido para FilterTools
    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay
    autoplay.start(itemlist, item)

    if itemlist and item.contentChannel != "videolibrary":
        itemlist.append(Item(channel=item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))

        # Opción "Añadir esta película a la videoteca de KODI"
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle = item.contentTitle
                                 ))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria in ['peliculas','latino']:
            item.url = host
        elif categoria == 'infantiles':
            item.url = host + 'category/animacion/'
        elif categoria == 'terror':
            item.url = host + 'category/torror/'
        itemlist = peliculas(item)
        if "Pagina" in itemlist[-1].title:
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "?s=" + texto
    item.extra = "busca"
    if texto != '':
        return sub_search(item)
    else:
        return []


def sub_search(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, encoding=encoding).data
    data = data.replace("&nbsp;","")
    patron  = '(?is)class="col-xs-2".*?href="([^"]+)'
    patron += '.*?title="([^"]+)'
    patron += '.*?src="([^"]+)'
    patron += '.*?main-info-list">Pel.*?cula de (\w+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear in matches:
        idioma = "Latino"
        scrapedyear = scrapedyear
        if not scrapedyear: scrapedyear = "-"
        item.infoLabels['year'] = scrapedyear
        itemlist.append(item.clone(channel = item.channel,
                                   action = "findvideos",
                                   title = scrapertools.htmlclean(scrapedtitle),
                                   contentTitle = scrapedtitle,
                                   thumbnail = scrapedthumbnail,
                                   url = scrapedurl,
                                   contentType="movie",
                                   language = idioma
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, __modo_grafico__)
    url_pagina = scrapertools.find_single_match(data, """blog-pager-older-link.*?href='([^']+)""")
    if url_pagina:
        mr = scrapertools.find_single_match(url_pagina, "&max-results=\w+")
        if not url_pagina.endswith("&"): url_pagina += "&"
        url_pagina = url_pagina.replace(mr,"") + "max-results=%s" %max_result
        pagina = "Pagina siguiente"
        itemlist.append(Item(channel = item.channel, action = "peliculas", title = pagina, url = url_pagina))
    return itemlist


def generos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, encoding=encoding).data
    patron   = '(?is)menu-item menu-item-type-taxonomy menu-item-object-category.*?href="([^"]+)'
    patron  += '.*?>([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle in matches:
        if scrapedtitle.lower() in ["estrenos"]: continue
        itemlist.append(Item(channel = item.channel,
                             action = "peliculas",
                             title = scrapedtitle.capitalize(),
                             url = scrapedurl
                             ))
    return itemlist
    

def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
