# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channels import filtertools
from channels import autoplay
from channelselector import get_thumb



IDIOMAS = {'latino': 'LAT', 'subtitulado': 'VOSE'}
list_language = list(IDIOMAS.values())
list_quality = ['CAM', '360p', '480p', '720p', '1080p']
list_servers = ['vidlox', 'fembed', 'vidcolud', 'streamango', 'openload']


host = 'http://pelisfox.tv'


def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)
    itemlist = []

    itemlist.append(item.clone(title="Ultimas",
                               action="lista",
                               thumbnail=get_thumb('last', auto=True),
                               url=host + '/estrenos/'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host,
                               thumbnail=get_thumb('genres', auto=True),
                               seccion='generos'
                               ))

    itemlist.append(item.clone(title="Por Año",
                               action="seccion",
                               url=host + '/peliculas/2019/',
                               thumbnail=get_thumb('year', auto=True),
                               seccion='anios'
                               ))

    itemlist.append(item.clone(title="Por Actor",
                               action="seccion",
                               url=host + '/actores/',
                               thumbnail=get_thumb('actors', auto=True),
                               seccion='actor'
                               ))

    itemlist.append(item.clone(title="Buscar",
                               action="search",
                               url=host + '/api/suggest/?query=',
                               thumbnail=get_thumb('search', auto=True)
                               ))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def lista(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)

    if item.seccion != 'actor':
        patron = '(?s)<li class="item-serie.*?href="([^"]+).*?title="([^"]+).*?data-src="([^"]+).*?<span '
        patron += 'class="s-title">.*?<p>([^<]+)'
    else:
        patron = '(?s)<li>.*?<a href="(/pelicula/[^"]+)".*?<figure>.*?data-src="([^"]+)".*?p class="title">([^<]+).*?'
        patron += 'year">([^<]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedurl, scrapedtitle, scrapedthumbnail, scrapedyear in matches:
        url = host + scrapedurl
        if item.seccion != 'actor':
            thumbnail = scrapedthumbnail
            contentTitle = scrapedtitle
        else:
            thumbnail = scrapedtitle
            contentTitle = scrapedthumbnail
        plot = ''
        year = scrapedyear
        title = contentTitle + ' (' + year + ')'
        itemlist.append(
            Item(channel=item.channel,
                 action='findvideos',
                 title=title,
                 url=url,
                 thumbnail=thumbnail,
                 plot=plot,
                 contentTitle=contentTitle,
                 infoLabels={'year': year}
                 ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    # Paginacion

    if itemlist != []:
        actual_page = scrapertools.find_single_match(data, '<a class="active item" href=".*?">(.*?)<\/a>')
        if actual_page:
            next_page_num = int(actual_page) + 1
            next_page = scrapertools.find_single_match(data,
                                                       '<li><a class=" item" href="(.*?)\?page=.*?&limit=.*?">Siguiente')
            next_page_url = host + next_page + '?page=%s' % next_page_num
            if next_page != '':
                itemlist.append(Item(channel=item.channel,
                                     action="lista",
                                     title='Siguiente >>>',
                                     url=next_page_url,
                                     thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                                     ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    if item.seccion == 'generos':
        patron = '<a href="(\/peliculas\/[\D].*?\/)" title="Películas de .*?>(.*?)<\/a>'
    elif item.seccion == 'anios':
        patron = '<li class=.*?><a href="(.*?)">(\d{4})<\/a> <\/li>'
    elif item.seccion == 'actor':
        patron = '<li><a href="(.*?)".*?div.*?<div class="photopurple" title="(.*?)">.*?data-src="([^"]+)'
    matches = scrapertools.find_multiple_matches(data, patron)
    if item.seccion != 'actor':
        for scrapedurl, scrapedtitle in matches:
            if not PY3:
                title = scrapedtitle.decode('utf-8')
            else:
                title = scrapedtitle
            thumbnail = ''
            fanart = ''
            url = host + scrapedurl

            itemlist.append(
                Item(channel=item.channel,
                     action="lista",
                     title=title,
                     contentTitle=item.title,
                     url=url,
                     thumbnail=thumbnail,
                     fanart=fanart
                     ))
    else:
        for scrapedurl, scrapedname, scrapedthumbnail in matches:
            fanart = ''
            title = scrapedname
            url = host + scrapedurl

            itemlist.append(Item(channel=item.channel,
                                 action="lista",
                                 title=title,
                                 contentTitle=item.title,
                                 url=url,
                                 thumbnail=scrapedthumbnail,
                                 fanart=fanart,
                                 seccion=item.seccion
                                 ))
        # Paginacion

        if itemlist != []:
            next_page = scrapertools.find_single_match(data, '<li><a class=" item" href="(.*?)&limit=.*?>Siguiente <')
            next_page_url = host + next_page
            if next_page != '':
                itemlist.append(item.clone(action="seccion",
                                           title='Siguiente >>>',
                                           url=next_page_url,
                                           thumbnail='https://s16.postimg.cc/9okdu7hhx/siguiente.png'
                                           ))

    return itemlist


def busqueda(item):
    logger.info()
    itemlist = []
    headers = {'referer':host, 'X-Requested-With': 'XMLHttpRequest',
               'Accept': 'application/json, text/javascript, */*; q=0.01'}
    dict_data = httptools.downloadpage(item.url, headers=headers).json
    resultados = dict_data['data']['m']

    for resultado in resultados:
        title = resultado['title']
        thumbnail = 'https://static.pelisfox.tv/' + '/' + resultado['cover']
        plot = resultado['synopsis']
        url = host + resultado['slug'] + '/'

        itemlist.append(item.clone(title=title,
                                   thumbnail=thumbnail,
                                   plot=plot,
                                   url=url,
                                   action='findvideos',
                                   contentTitle=title
                                   ))
    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "%20")
    item.url = item.url + texto

    if texto != '':
        return busqueda(item)
    else:
        return []


def findvideos(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    links = scrapertools.find_single_match(data, '<script>var.*?_SOURCE.?=\s?(.*?);')
    links = links.replace('null', '"null"')
    links = links.replace('false', '"false"').replace('true', '"true"')
    links = eval(links)
    for link in links:
        language = link['lang']
        quality = link['quality']
        url = link['source'].replace('\\/', '/')
        sub = link['srt']

        if config.get_setting('unify'):
            title = ''
        else:
            title = ' [%s] [%s]' % (quality, language)

        itemlist.append(Item(channel=item.channel, action='play', title='%s'+title, url=url, quality=quality,
                             language=IDIOMAS[language], subtitle=sub, infoLabels=item.infoLabels))

    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    if config.get_videolibrary_support() and len(itemlist) > 0 and item.extra != 'findvideos':
        itemlist.append(
            Item(channel=item.channel,
                 title='[COLOR yellow]Añadir esta pelicula a la videoteca[/COLOR]',
                 url=item.url,
                 action="add_pelicula_to_library",
                 extra="findvideos",
                 contentTitle=item.contentTitle
                 ))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    # categoria='peliculas'
    try:
        if categoria in ['peliculas','latino']:
            item.url = host + '/estrenos/'
        elif categoria == 'infantiles':
            item.url = host + '/peliculas/animacion/'
        elif categoria == 'terror':
            item.url = host + '/peliculas/terror/'
        item.extra = 'peliculas'
        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def play(item):
    item.thumbnail = item.contentThumbnail
    return [item]
