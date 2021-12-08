# -*- coding: utf-8 -*-
# -*- Channel SeriesMetro -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re

from bs4 import BeautifulSoup
from channels import autoplay, filtertools
from core import httptools, scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

host = 'https://seriesmetro.net/'
unify = config.get_setting('unify')

list_quality = []
list_servers = ['cinemaupload']

full_title = config.get_setting('full_title', 'seriesmetro')

def create_soup(url, referer=None, unescape=False):
    logger.info()

    data = httptools.downloadpage(url, headers=referer).data
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    if unescape:
        data = scrapertools.unescape(data)

    return soup

def setting_channel(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return ret

def mainlist(item):
    logger.info()

    autoplay.init(item.channel, list_servers, list_quality)

    itemlist =[]

    itemlist.append(Item(channel=item.channel, title="Últimas Series",
                         action="list_all", url=host+'series/',
                         thumbnail=get_thumb('last', auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Últimos Capitulos",
                         action="new_episodes", url=host+'ultimos-capitulos/',
                         thumbnail=get_thumb('new_episodes', auto=True)))
    
    '''itemlist.append(Item(channel=item.channel, title="Más Vistas",
                         action="list_all", url=host,
                         thumbnail=get_thumb('more watched', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Generos", action="section",
                         thumbnail=get_thumb('genres', auto=True)))'''

    itemlist.append(Item(channel=item.channel, title="Alfabetico", action="section",
                         thumbnail=get_thumb('alphabet', auto=True)))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + '?s=',
                         thumbnail=get_thumb('search', auto=True)))

    itemlist.append(Item(channel=item.channel,action="setting_channel", title="Configurar canal...",
                         text_color="aquamarine", thumbnail=get_thumb("setting_0.png"),
                         folder=False))

    autoplay.show_option(item.channel, itemlist)
    return itemlist

def list_all(item):
    logger.info()

    itemlist = []
    plot = ''

    soup = create_soup(item.url)
    matches = soup.find_all("article", class_="post single lg")
    '''if item.gen_sec:
        matches = soup.find_all("article", class_="post serie")'''

    for elem in matches:
        
        stitle = elem.h2.text
        info = elem.find("span", class_="tv-num").text
        year = elem.find("span", class_="date").text
        url = elem.find("a", class_="lnk-blk")['href']
        thumb = elem.img['src']
        try:
            plot = elem.find_all('p')[1].text
        except:
            plot = ''

        title = stitle
        if not unify:
            if year:
                title += ' [COLOR silver](%s)[/COLOR]' % year

            if full_title and not ' 0Eps' in info:
                title += ' [COLOR aquamarine](%s)[/COLOR]' % info.replace('Eps', ' Eps')

        itemlist.append(Item(channel=item.channel, title=title, url=url,
                             action='seasons', info_p=info, plot=plot,
                             thumbnail=thumb, contentSerieName=stitle,
                             infoLabels={'year': year}))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        
    try:    
        next_ = soup.find("nav", class_="navigation pagination").find_all("a")
        l = len(next_) -1
        next_page= next_[l]['href']
        itemlist.append(Item(channel=item.channel, title='Siguiente >>', url=next_page, action='list_all'))
    except:
        pass

    return itemlist

def new_episodes(item):
    logger.info()

    itemlist = []

    soup = create_soup(item.url)

    for elem in soup.find_all("article", class_="post episode sm"):
        
        stitle = elem.find("span", class_="tvshow").text

        ep_title = elem.find("h2", class_="entry-title").text
        url = elem.find("a", class_="lnk-blk")['href']
        #TODO usarlo de filtro en tmdb
        thumb = 'https:'+elem.img['src'].replace('/w185', '/original')
        title = stitle
        if full_title and not unify:
            title = '%s [COLOR aquamarine][I]%s[/I][/COLOR]' % (stitle, ep_title)
        ctitle = re.sub(r'(?: Temporada|) (\d+x.*)', '', stitle)

        itemlist.append(Item(channel=item.channel, title=title, url=url,
                             action='findvideos',
                             thumbnail=thumb, contentSerieName=ctitle))

    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
        
    try:    
        next_ = soup.find("nav", class_="navigation pagination").find_all("a")
        l = len(next_) -1
        next_page= next_[l]['href']
        itemlist.append(Item(channel=item.channel, title='Siguiente >>', url=next_page, action='list_all'))
    except:
        pass

    return itemlist

def section(item):

    itemlist = []

    if item.title == 'Generos':
        #TODO crear lista géneros
        return
    elif item.title == 'Alfabetico':
        words = '#ABCDEFGHIJKLMNOPQRSTUVWXYZ'
        for w in words:
            title = w
            url = '%s/ver/letter/%s' % (host, w.replace('#', '0-9'))
            itemlist.append(Item(channel=item.channel, title=title,
                                 url=url, action='list_all'))


    return itemlist

def seasons(item):
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels

    soup = create_soup(item.url)

    try:
        obj = soup.find('div', class_="aa-cn")['data-object']
    except:
        return itemlist


    for elem in soup.find_all("li", class_="sel-temp"):

        title = 'Temporada %s' % elem.text
        infoLabels['season'] = elem.text
        url = '{}wp-admin/admin-ajax.php'.format(host)

        itemlist.append(Item(channel=item.channel, title=title, url=url,
                             action='episodesxseason', infoLabels=infoLabels,
                             obj=obj))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)

    if config.get_videolibrary_support() and len(itemlist) and item.extra != 'episodios':
        itemlist.append(
                Item(channel=item.channel, title='[COLOR yellow]Añadir esta serie a la videoteca[/COLOR]', url=item.url,
                     action="add_serie_to_library", extra="episodios", contentSerieName=item.contentSerieName))

    return itemlist

def episodios(item):
    logger.info()
    itemlist = []
    templist = seasons(item)
    for tempitem in templist:
        itemlist += episodesxseason(tempitem)
    return itemlist

def episodesxseason(item):
    logger.info()
    itemlist = []
    infoLabels = item.infoLabels
    season = infoLabels['season']
    obj = item.obj
    
    data = ''
    n = 1
    Stop = False

    while not Stop:
        post = 'action=action_pagination_ep&page={}&object={}&season={}'.format(str(n), obj, season)
        new_data = httptools.downloadpage(item.url, post=post, add_referer=True, ignore_response_code=True)
        if new_data.sucess:
            new_data = new_data.data
        else:
            Stop = True
            break

        if not '<li><a href=' in new_data:
            Stop = True
            break
        data += new_data
        n += 1

    
    soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
    
    for elem in soup.find_all("li"):

        url = elem.a['href']

        ep, t_ep = scrapertools.find_single_match(elem.text, r'x(\d+) (.*)')
        t_ep = re.sub(r' – |\d+-\d+-\d+', '', t_ep)
        title = '%sx%s [COLOR aquamarine][I]%s[/I][/COLOR]' % (season, ep, t_ep)
        infoLabels['episode'] = ep

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='findvideos',
                                 infoLabels=infoLabels))
    
    tmdb.set_infoLabels_itemlist(itemlist, True)
    
    return itemlist

def search(item, text):
    logger.info()

    item.url = item.url + text
    if text != '':
        return list_all(item)

def findvideos(item):

    itemlist = []
    servers = {'Cload': 'cinemaupload'}
    IDIOMAS = {'Español Latino': 'LAT', 'Español Castellano': 'CAST',
               'Sub Español': 'VOSE', 'Ingles': 'VOS'}
    list_language = list(IDIOMAS.values())
    
    soup = create_soup(item.url)

    term_id = soup.find('div', class_="video aa-tb hdd anm-a on")['data-term']

    bloq = soup.find("ul", class_="aa-tbs-video player-options-list")
    for elem in bloq.find_all("a"):
        
        ide = elem['data-opt']
        info = elem.find('span', class_="option").text.partition(' - ')
        lang = str(info[2])
        srv = str(info[0])
        server = servers.get(srv, srv)

        language = IDIOMAS.get(lang, lang)
        link = '%s?trembed=%s&trid=%s&trtype=2' % (host, ide, term_id)
        soup = create_soup(link)
        url = soup.find('iframe')['src']
        url = url.replace('&#038;', '&')
        url = "%s" % url
        if "fastream" in url:
            server = "fastream"
        title = '%s [COLOR silver][%s][/COLOR]' % (server, language)

        itemlist.append(Item(channel=item.channel, title=title, url=url, action='play',
                             language=language, infoLabels=item.infoLabels, 
                             server=server))


    itemlist = servertools.get_servers_itemlist(itemlist)
    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)

    return itemlist
