# -*- coding: utf-8 -*-
# -*- Channel PelisVips -*-
# -*- Created for Alfa-addon -*-
# -*- By the Alfa Develop Group -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

import re

from bs4 import BeautifulSoup
from channels import autoplay, filtertools
from core import httptools, scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb

#Yoast SEO v11.6
host = "https://www.pelisvips.com/"

unify = config.get_setting('unify')
lquality = {'hd1080p': 'FHD', 'hd720p': 'HD', 'hdreal720': 'HD',
            'br screener': 'BR-S', 'ts screener': 'TS'}

list_quality = list(lquality.values())

list_servers = ['directo', 'fembed', 'rapidvideo', 'mega', 'vidlox', 'streamango', 'openload']

IDIOMAS = {'Latino': 'LAT', 'Castellano': 'CAST',
           'Subtitulado': 'VOSE', 'Subtitulada': 'VOSE'}

list_language = list(IDIOMAS.values())

def mainlist(item):
    logger.info()
    itemlist = []

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Estrenos", action="list_all",
                         url= host+'genero/estrenos/', viewmode="movie_with_plot",
                         thumbnail=get_thumb("premieres", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Novedades", action="list_all",
                         url= host, viewmode="movie_with_plot",
                         thumbnail=get_thumb("newest", auto=True)))

    itemlist.append(Item(channel=item.channel, title="Géneros", action="genres",
                         url=host, thumbnail=get_thumb("genres", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Castellano", action="list_all",
                         url=host+'ver-idioma/castellano/',
                         thumbnail=get_thumb("cast", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Latino", action="list_all",
                         url=host+'ver-idioma/latino/',
                         thumbnail=get_thumb("lat", auto=True)))

    itemlist.append(Item(channel=item.channel, title="VOSE", action="list_all",
                         url=host+'ver-idioma/subtitulada/',
                         thumbnail=get_thumb("vose", auto=True)))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                         url= host + "?s=", thumbnail=get_thumb("search", auto=True)))

    autoplay.show_option(item.channel, itemlist)

    return itemlist


def create_soup(url, soup=True, referer=None, post=None):
    logger.info()

    data = httptools.downloadpage(url, headers=referer, post=post).data
    if soup:
        soup = BeautifulSoup(data, "html5lib", from_encoding="utf-8")
        return soup
    return data

def genres(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    
    bloque = soup.find_all('ul', class_="sbi-list")[1]
    matches = bloque.find_all('a')
    
    for elem in matches:
        url = elem['href']
        title = elem.text.strip()
        
        itemlist.append(Item(channel=item.channel, action="list_all",
                             title=title, url=url))

    return itemlist


def search(item, texto):
    logger.info()
    texto_post = texto.replace(" ", "+")
    item.url = item.url + texto_post
    try:
        return list_search(item)
    # Se captura la excepcion, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
    

    

def list_search(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    matches = soup.find_all('li', class_='itemlist')

    for elem in matches:
        url = elem.a['href']
        url = urlparse.urljoin(host, url)
        stitle = elem.a['title']
        thumbnail = elem.img['src']
        info = elem.find('p', class_='main-info-list').text.partition('Calidad:')
        plot = elem.find('p', class_='text-list').text.partition('cula Completa ')[2]

        title = clear_title(stitle)
        year = scrapertools.find_single_match(stitle, r'\((\d{4})\)$')
        quality = info[2].strip()

        quality = lquality.get(quality.lower(), quality)
        
        info_langs = info[0].split('Idioma:')[1]
        list_langs = scrapertools.find_multiple_matches(info_langs, '([a-zA-Z]+)')
        langs, list_langs = extrae_idiomas(list_langs)


        plot = ''
        if not unify:
            stitle = "[B]%s[/B] [COLOR darkgrey](%s)[/COLOR]" % (
                     title, year)
            plot = '[COLOR yellowgreen][I]Idiomas[/COLOR]: %s\n[COLOR yellowgreen]Calidad[/COLOR]: %s[/I]\n\n' % (
                    langs, quality)

        itemlist.append(Item(channel = item.channel,
                             action = 'findvideos',
                             contentTitle = title,
                             infoLabels = {'year':year},
                             quality = quality,
                             thumbnail = thumbnail,
                             title = stitle,
                             language=list_langs,
                             url = url,
                             plot=plot,
                             plot2=plot
                             ))
    
    tmdb.set_infoLabels(itemlist, True)
    
    if not unify:
        for item in itemlist:
            if item.infoLabels['tmdb_id'] and not 'Idiomas' in item.contentPlot:
                item.plot1 = item.contentPlot
                item.contentPlot = item.plot2+item.contentPlot

    return itemlist


def list_all(item):
    logger.info()
    itemlist = []
    
    soup = create_soup(item.url)
    matches = soup.find_all('a', class_='movie-item clearfix tooltipS')
    
    for elem in matches:
        
        url = elem['href']
        url = urlparse.urljoin(host, url)
        quality = elem.find('div', class_='_format').text.strip()
        thumbnail = elem.img['src']
        stitle = elem.img['alt']
        syear = elem.find('div', class_='label_year').text
        audio = elem.find('div', class_='_audio')

        title, year = clear_title(stitle, syear)
        stitle = title
        
        quality = lquality.get(quality.lower(), quality)
        
        list_langs = audio.find_all('img')
        langs, list_langs = extrae_idiomas(list_langs)
        plot = ''
        if not unify:
            stitle = "[B]%s[/B] [COLOR darkgrey](%s)[/COLOR]" % (
                     title, year)
            plot = '[COLOR yellowgreen][I]Idiomas[/COLOR]: %s\n[COLOR yellowgreen]Calidad[/COLOR]: %s[/I]\n\n' % (
                    langs, quality)
        
        itemlist.append(Item(channel = item.channel,
                             action = 'findvideos',
                             contentTitle = title,
                             infoLabels = {'year':year},
                             quality = quality,
                             thumbnail = thumbnail,
                             title = stitle,
                             language=list_langs,
                             url = url,
                             plot=plot,
                             plot2=plot
                             ))
    tmdb.set_infoLabels(itemlist, True)
    if not unify:
        for item in itemlist:
            if item.infoLabels['tmdb_id'] and not 'Idiomas' in item.contentPlot:
                item.plot1 = item.contentPlot
                item.contentPlot = item.plot2+item.contentPlot
                
    try:
        next_page = soup.find('a', class_='nextpostslink')['href']
        next_page = urlparse.urljoin(host, next_page)
    except:
        next_page = None
    if next_page:
        itemlist.append(Item(channel=item.channel, action="list_all",
                             title='Página Siguiente >>',
                             text_color='aquamarine',
                             url=next_page.strip()))

    return itemlist


def findvideos(item):
    logger.info()
    itemlist = []
    from lib import players_parse
               
    # Descarga la pagina
    soup = create_soup(item.url).find('div', id='movie-player')

    matches = soup.find_all('li')
    
    for elem in matches:
        title = "%s"
        url = elem.a['rel'][0]
        url = players_parse.player_parse(url, elem.a['title'], host)
        
        info = elem.find('span', class_='optxt').text.partition('\n')
        
        slang = info[0].strip().replace('Español ', '')
        squality = info[2].strip().replace(' ', '')
        
        language = IDIOMAS.get(slang, slang)
        quality = lquality.get(squality.lower(), squality)

        if "pelisvips.com" in url:
            data = create_soup(url, soup=False).partition('sources:')[2]
            url = scrapertools.find_single_match(data, "file': '([^']+)")
        
        elif "pelisup" in url:
            url = url.replace('pelisup', 'fembed')
        
        if not unify:
            title += ' [COLOR palegreen][%s] [/COLOR][COLOR grey][%s][/COLOR]' % (quality, language)

        if url:
            itemlist.append(
                item.clone(action="play", title=title, url=url,
                           quality= quality, language=language,
                           plot=item.plot1
                           ))
    
    itemlist=servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())

    # Requerido para FilterTools

    itemlist = filtertools.get_links(itemlist, item, list_language)

    # Requerido para AutoPlay

    autoplay.start(itemlist, item)
    
    
    if itemlist and item.contentChannel != "videolibrary":
        if config.get_videolibrary_support():
            itemlist.append(Item(channel=item.channel, title="Añadir a la videoteca", text_color="gold",
                                 action="add_pelicula_to_library", url=item.url, thumbnail = item.thumbnail,
                                 contentTitle=item.contentTitle
                                 ))
    return itemlist


def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    try:
        if categoria == 'peliculas':
            item.url = host

        elif categoria == 'documentales':
            item.url = host + "genero/documental/"

        elif categoria == 'infantiles':
            item.url = host + "genero/animacion/"

        elif categoria == 'terror':
            item.url = host + "genero/terror/"

        elif categoria == 'castellano':
            item.url = host + "ver-idioma/castellano/"

        elif categoria == 'latino':
            item.url = host + "ver-idioma/latino/"

        itemlist = list_all(item)

        if itemlist[-1].action == "list_all":
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist

def clear_title(stitle, syear=None):
    title = re.sub(r' / (.*)| \(.*', '', stitle)
    if syear:
        year = scrapertools.find_single_match(syear, r'(\d{4})') or '-'
        return title, year
    return title

def extrae_idiomas(list_language):
    logger.info()
    textoidiomas = ''
    
    for i, elem in enumerate(list_language):
        try:
            idioma = elem['title']
        except:
            idioma = elem.strip()
        
        c_lang = IDIOMAS.get(idioma, idioma)
        
        textoidiomas += "%s, " % c_lang
        list_language[i] = c_lang

    textoidiomas = textoidiomas[:-2]
    
    return textoidiomas, list_language