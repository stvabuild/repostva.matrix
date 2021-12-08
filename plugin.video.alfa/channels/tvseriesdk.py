# -*- coding: utf-8 -*-
# -*- Channel TVSeriesdk -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

host = 'http://www.tvseriesdk.com/'


def mainlist(item):
    logger.info()

    itemlist = list()
    itemlist.append(item.clone(title="Ultimos", action="last_episodes", url=host))
    itemlist.append(item.clone(title="Todas", action="list_all", url=host))
    itemlist.append(item.clone(title="Buscar", action="search", url='http://www.tvseriesdk.com/index.php?s='))

    return itemlist


def get_source(url):
    logger.info()
    data = httptools.downloadpage(url).data
    data = re.sub(r'"|\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def list_all(item):
    logger.info()
    global i
    templist = []
    data = get_source(item.url)

    patron = '<li class=cat-item cat-item-\d+><a href=(.*?) title=(.*?)>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if len(matches) > 10:
        if item.next_page != 10:
            url_next_page = item.url
            matches = matches[:10]
            next_page = 10
            item.i = 0
        else:
            patron = matches[item.i:][:10]
            next_page = 10

            url_next_page = item.url

    for scrapedurl, scrapedplot, scrapedtitle in matches:
        url = scrapedurl
        plot = scrapedplot
        contentSerieName = scrapedtitle
        title = contentSerieName

        templist.append(item.clone(action='episodios',
                                   title=title,
                                   url=url,
                                   thumbnail='',
                                   plot=plot,
                                   contentErieName=contentSerieName
                                   ))
    itemlist = serie_thumb(templist)
    #  Paginación
    if url_next_page:
        itemlist.append(item.clone(title="Siguiente >>", url=url_next_page, next_page=next_page, i=item.i))
    return itemlist


def last_episodes(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = '<div class=pelis>.*?<a href=(.*?) title=(.*?)><img src=(.*?) alt='
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle, scrapedthumbnail in matches:
        url = scrapedurl
        title = scrapedtitle
        thumbnail = scrapedthumbnail

        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail
                                   ))
    return itemlist


def episodios(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    patron = '<a href=(.*?) class=lcc>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    n_ep = 1
    for scrapedurl, scrapedtitle in matches[::-1]:
        url = scrapedurl
        scrapedtitle = re.sub(r'Capítulo \d+', '', scrapedtitle)
        title = '1x%s - %s' % (n_ep, scrapedtitle)
        itemlist.append(
            item.clone(action='findvideos', title=title, url=url, contentEpisodeNumber=n_ep, contentSeasonNumber='1'))
        n_ep += 1
    return itemlist


def serie_thumb(itemlist):
    logger.info()
    for item in itemlist:
        data = get_source(item.url)
        item.thumbnail = scrapertools.find_single_match(data, '<div class=sinope><img src=(.*?) alt=')
    return itemlist


def search_list(item):
    logger.info()
    itemlist = []

    data = get_source(item.url)
    patron = 'img title.*?src=(.*?) width=.*?class=tisearch><a href=(.*?)>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumb, scrapedurl, scrapedtitle in matches:
        title = scrapedtitle
        url = scrapedurl
        thumbnail = scrapedthumb
        itemlist.append(item.clone(title=title, url=url, thumbnail=thumbnail, action='findvideos'))
    # Pagination < link
    next_page = scrapertools.find_single_match(data, '<link rel=next href=(.*?) />')
    if next_page:
        itemlist.append(Item(channel=item.channel, action="search_list", title='>> Pagina Siguiente', url=next_page,
                             thumbnail = get_thumb('thumb_next.png')))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    if texto != '':
        return search_list(item)
    else:
        return []


def findvideos(item):
    logger.info()
    itemlist = []
    servers = {'netu': 'http://hqq.tv/player/embed_player.php?vid=',
               'open': 'https://openload.co/embed/',
               'netv': 'http://goo.gl/',
               'gamo': 'http://gamovideo.com/embed-',
               'powvideo': 'http://powvideo.net/embed-',
               'play': 'http://streamplay.to/embed-',
               'vido': 'http://vidoza.net/embed-',
               'net': 'http://hqq.tv/player/embed_player.php?vid=',
               'ntu': 'http://hqq.tv/player/embed_player.php?vid='
               }
    data = get_source(item.url)
    noemitido = scrapertools.find_single_match(data, '<p><img src=(http://darkiller.com/images/subiendo.png) border=0\/><\/p>')
    patron = 'id=tab\d+.*?class=tab_content><script>(.*?)\((.*?)\)<\/script>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not noemitido:
        for server, video_id in matches:
            if server not in ['gamo', 'powvideo', 'play', 'vido', 'netv']:
                url = servers[server] + video_id
            elif server == 'netv':
                url = get_source(servers[server] + video_id)
            else:
                url = servers[server] + video_id + '.html'

            itemlist.extend(servertools.find_video_items(data=url))
        for videoitem in itemlist:
            videoitem.channel = item.channel
            videoitem.title = item.title + ' (%s)' % videoitem.server
            videoitem.action = 'play'
    else:
        itemlist.append(item.clone(title = 'Este capitulo aun no esta disponible', action='', url=''))
    return itemlist
