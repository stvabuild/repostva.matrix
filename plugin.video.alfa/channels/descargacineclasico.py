# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urllib                                               # Es muy lento en PY2.  En PY3 es nativo
else:
    import urllib                                                               # Usamos el nativo de PY2 que es más rápido

import re

from channelselector import get_thumb
from platformcode import logger, config
from core import scrapertools, httptools
from core import servertools
from core import tmdb
from core.item import Item
from lib import unshortenit
from bs4 import BeautifulSoup

canonical = {
             'channel': 'descargacineclasico', 
             'host': config.get_setting("current_host", 'descargacineclasico', default=''), 
             'host_alt': ["https://descargacineclasico.net"], 
             'host_black_list': [], 
             'CF': False, 'CF_test': False, 'alfa_s': True
            }
host = canonical['host'] or canonical['host_alt'][0]


def mainlist(item):
    logger.info()
    itemlist = []
    itemlist.append(Item(channel=item.channel, title="Últimas agregadas", action="agregadas",
                         url=host, viewmode="movie_with_plot", thumbnail=get_thumb('last', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Listado por género", action="porGenero",
                         url=host, thumbnail=get_thumb('genres', auto=True)))
    itemlist.append(Item(channel=item.channel, title="Buscar", action="search", url=host,
                         thumbnail=get_thumb('search', auto=True)))
    return itemlist


def create_soup(url, referer=None, unescape=False):
    logger.info()

    if referer:
        data = httptools.downloadpage(url, headers={'Referer':referer}, canonical=canonical).data
    else:
        data = httptools.downloadpage(url, canonical=canonical).data

    if unescape:
        data = scrapertools.unescape(data)
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")

    return soup


def porGenero(item):
    logger.info()
    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", id="sidebar").find("ul", "columnas")

    for elem in matches.find_all("li"):

        url = elem.a["href"]
        genero = elem.a.text
        if genero == "Erótico" and config.get_setting("adult_mode") == 0:
            continue
        itemlist.append(Item(channel=item.channel, action="agregadas", title=genero, url=url))

    return itemlist


def search(item,texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = host + "?s=" + texto
    try:
        return agregadas(item)
    # Se captura la excepci?n, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def agregadas(item):
    logger.info()
    itemlist = list()

    soup = create_soup(item.url)
    matches = soup.find("div", class_="review-box-container")

    for elem in matches.find_all("div", class_="review-box"):
        url = elem.a["href"]
        title = elem.img["alt"]
        thumbnail = elem.img["src"]
        title = title.replace("Descargar y ver Online", "").replace("Gratis", "").strip()
        year = scrapertools.find_single_match(title, '\(([0-9]{4})')
        plot = elem.p.text
        contentTitle = title.replace("(%s)" %year,"").strip()
        itemlist.append( Item(action="findvideos",
                              channel=item.channel,
                              title=title+"",
                              contentTitle=contentTitle ,
                              infoLabels={'year':year},
                              url=url ,
                              thumbnail=thumbnail,
                              plot=plot,
                              ))
    tmdb.set_infoLabels(itemlist)
    # Paginación
    try:
        next_page = soup.find("a", class_="nextpostslink")["href"]
        itemlist.append( Item(channel=item.channel, action="agregadas", title="Página siguiente >>", url=next_page))
    except:
        pass
    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url, canonical=canonical).data
    data = scrapertools.unescape(data)
    patron = '#div_\d_\D.+?<img id=([^ ]+) .*?<span>.*?</span>.*?<span>(.*?)</span>.*?imgdes.*?imgdes/([^\.]+).*?<a href=([^\s]+)'  #Añado calidad
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedidioma, scrapedcalidad, scrapedserver, scrapedurl in matches:
        if "proximamente" in scrapedurl.lower():
            continue
        scrapedurl = scrapedurl.replace('"','')
        # while True:
        #     loc = httptools.downloadpage(scrapedurl, follow_redirects=False, ignore_response_code = True).headers.get("location", "")
        #     if not loc or "/ad/locked" in loc or not loc.startswith("http"):
        #         break
        #     scrapedurl = loc
        # scrapedurl, c = unshortenit.unshorten_only(scrapedurl)
        # if "dest=" in scrapedurl or "dp_href=" in scrapedurl:
        #     scrapedurl = scrapertools.find_single_match(urllib.unquote(scrapedurl), '(?:dest|dp_href)=(.*)')
        title = item.title + "_" + scrapedidioma + "_"+ scrapedserver + "_" + scrapedcalidad
        itemlist.append( item.clone(action="play",
                                    title=title,
                                    url=scrapedurl) )
    itemlist = servertools.get_servers_itemlist(itemlist)
    tmdb.set_infoLabels(itemlist)
    if itemlist:
        itemlist.append(Item(channel = item.channel))
        itemlist.append(item.clone(channel="trailertools", title="Buscar Tráiler", action="buscartrailer", context="",
                                   text_color="magenta"))
        # Opción "Añadir esta película a la biblioteca de KODI"
        if item.contentChannel != "videolibrary" and config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="green",
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle = item.contentTitle
                                 ))
    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
