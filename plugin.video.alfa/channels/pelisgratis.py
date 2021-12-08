# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import base64

from core import httptools
from core import scrapertools
from core import servertools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from channelselector import get_thumb


thumbletras = {'#': 'https://s32.postimg.cc/drojt686d/image.png',
               'a': 'https://s32.postimg.cc/llp5ekfz9/image.png',
               'b': 'https://s32.postimg.cc/y1qgm1yp1/image.png',
               'c': 'https://s32.postimg.cc/vlon87gmd/image.png',
               'd': 'https://s32.postimg.cc/3zlvnix9h/image.png',
               'e': 'https://s32.postimg.cc/bgv32qmsl/image.png',
               'f': 'https://s32.postimg.cc/y6u7vq605/image.png',
               'g': 'https://s32.postimg.cc/9237ib6jp/image.png',
               'h': 'https://s32.postimg.cc/812yt6pk5/image.png',
               'i': 'https://s32.postimg.cc/6nbbxvqat/image.png',
               'j': 'https://s32.postimg.cc/axpztgvdx/image.png',
               'k': 'https://s32.postimg.cc/976yrzdut/image.png',
               'l': 'https://s32.postimg.cc/fmal2e9yd/image.png',
               'm': 'https://s32.postimg.cc/m19lz2go5/image.png',
               'n': 'https://s32.postimg.cc/b2ycgvs2t/image.png',
               'o': 'https://s32.postimg.cc/c6igsucpx/image.png',
               'p': 'https://s32.postimg.cc/jnro82291/image.png',
               'q': 'https://s32.postimg.cc/ve5lpfv1h/image.png',
               'r': 'https://s32.postimg.cc/nmovqvqw5/image.png',
               's': 'https://s32.postimg.cc/zd2t89jol/image.png',
               't': 'https://s32.postimg.cc/wk9lo8jc5/image.png',
               'u': 'https://s32.postimg.cc/w8s5bh2w5/image.png',
               'v': 'https://s32.postimg.cc/e7dlrey91/image.png',
               'w': 'https://s32.postimg.cc/fnp49k15x/image.png',
               'x': 'https://s32.postimg.cc/dkep1w1d1/image.png',
               'y': 'https://s32.postimg.cc/um7j3zg85/image.png',
               'z': 'https://s32.postimg.cc/jb4vfm9d1/image.png'
               }

audio_color = {'LAT': '[COLOR limegreen][LAT][/COLOR]',
               'CAST': '[COLOR gold][CAST][/COLOR]',
               'VOSE': '[COLOR grey][VOSE][/COLOR]'}

IDIOMAS = {'latino': 'LAT', 'espanol': 'CAST', 'castellano': 'CAST',
           'subtitulado': 'VOSE', 'subtitulo': 'VOSE'}

list_language = list(IDIOMAS.values())

list_quality = ['BRRip', 'HDRip', 'DVD-R', 'HDTv-rip', 'BR-Screener',
                'WEB-S', 'TS-HQ', 'TS-Screener']

list_servers = ['upstream', 'vidfast', 'okru', 'zplayer']

host = 'http://pelisgratis.nu/'
#host = 'http://pelisap.com/'


def mainlist(item):
    logger.info()

    itemlist = []

    itemlist.append(item.clone(title="Estrenos",
                               action="lista",
                               thumbnail=get_thumb('premieres', auto=True),
                               url=host + 'genero/estrenos/'
                               ))

    itemlist.append(item.clone(title="Últimas",
                               action="lista",
                               thumbnail=get_thumb('last', auto=True),
                               url=host
                               ))
    
    itemlist.append(item.clone(title="Castellano",
                               action="lista",
                               thumbnail=get_thumb('cast', auto=True),
                               url=host + 'idioma/espanol/'
                               ))
    
    itemlist.append(item.clone(title="Latino",
                               action="lista",
                               thumbnail=get_thumb('lat', auto=True),
                               url=host + 'idioma/latino/'
                               ))
    
    itemlist.append(item.clone(title="VOSE",
                               action="lista",
                               thumbnail=get_thumb('vose', auto=True),
                               url=host + 'idioma/subtitulada/'
                               ))

    itemlist.append(item.clone(title="Generos",
                               action="seccion",
                               url=host,
                               thumbnail=get_thumb('genres', auto=True),
                               extra='generos'
                               ))

    itemlist.append(item.clone(title="Alfabetico",
                               action="seccion",
                               url=host + 'genero/estrenos/',
                               thumbnail=get_thumb('alphabet', auto=True),
                               extra='a-z'
                               ))

    '''itemlist.append(item.clone(title="Mas Vistas",
                               action="lista",
                               thumbnail=get_thumb('more watched', auto=True),
                               url=host + 'peliculas-mas-vistas'
                               ))

    itemlist.append(item.clone(title="Mas Votadas",
                               action="lista",
                               thumbnail=get_thumb('more voted', auto=True),
                               url=host + 'peliculas-mas-votadas'
                               ))'''

    itemlist.append(item.clone(title="Buscar...",
                               action="search",
                               url=host + '?s=',
                               thumbnail=get_thumb('search', auto=True)
                               ))

    return itemlist


def get_source(url, referer=None):
    logger.info()
    if referer is None:
        data = httptools.downloadpage(url).data
    else:
        data = httptools.downloadpage(url, headers={'Referer':referer}).data
    data = re.sub(r'\n|\r|\t|&nbsp;|<br>|\s{2,}', "", data)
    return data


def lista(item):
    logger.info()
    itemlist = []
    infoLabels = {}
    data = get_source(item.url)
    patron = '<article class="item.*?href="([^"]+)" title="([^"]+)">(.*?)<img.*?src="([^"]+)"'

    matches = re.compile(patron, re.DOTALL).findall(data)
 
    for url, scrapedtitle, info_data, scrapedthumbnail in matches:
        
        quality = scrapertools.find_single_match(info_data, 'class="calidad">([^<]+)</div>')
        info_data = scrapertools.find_single_match(info_data, '<div class="audio">(.*?)</div></div>')
        list_langs = re.compile('<div class="([^"]+)"', re.DOTALL).findall(info_data)

        zanga, list_langs = extrae_idiomas(list_langs)

        thumbnail = re.sub('p/w\d+', "p/original", scrapedthumbnail)
        #filter_thumb = re.sub('(.*?)/w\d+', "", scrapedthumbnail)
        #filter_list = {"poster_path": filter_thumb}
        #infoLabels = {'filtro': list(filter_list.items())}

        year = scrapertools.find_single_match(url, '-(\d{4})')
        if year:
            infoLabels =  {'year': year}
        
        title = scrapedtitle
        stitle = re.sub(' \((.*?)\)$', '', scrapedtitle)
        #excepcion para unify
        title += ' [COLOR grey][%s][/COLOR][COLOR khaki] %s[/COLOR]' % (quality, zanga)

        itemlist.append(item.clone(action='findvideos',
                                   title=title,
                                   url=url,
                                   thumbnail=thumbnail,
                                   contentTitle=stitle,
                                   quality=quality,
                                   language=list_langs,
                                   infoLabels=infoLabels
                                   ))
    tmdb.set_infoLabels_itemlist(itemlist, seekTmdb=True)
    
    # Paginacion
    if len(itemlist):
        info = scrapertools.find_single_match(data, r'<a class="page-link">([^<]+)')
        
        actual, total = scrapertools.find_single_match(info, r'(\d+) de (\d+)') or [1, 1]
        
        if info and int(actual) < int(total):
            next_ = int(actual) + 1
            if next_ == 2:
                next_page = item.url + 'page/%s/' % next_
            else:
              next_page = re.sub(r'page/\d+', 'page/%s' % next_, item.url)

            plot = info
            itemlist.append(item.clone(action="lista",
                                       title='Siguiente >>>',
                                       url=next_page,
                                       plot=plot,
                                       thumbnail='https://s32.postimg.cc/4zppxf5j9/siguiente.png'
                                       ))
    return itemlist


def seccion(item):
    logger.info()
    itemlist = []
    data = get_source(item.url)
    if item.extra == 'generos':
        data = scrapertools.find_single_match(data, '<ul class="list-genero">(.*?)</ul>')
        patron = r'<li><a href="([^"]+)">([^<]+)'
    elif item.extra == 'a-z':
        patron = r'<li><a href="([^"]+)">(\w|#)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedurl, scrapedtitle in matches:
        url = scrapedurl
        thumbnail = ''
        if item.extra == 'generos':
            title = scrapedtitle
        else:
            title = scrapedtitle
            thumbnail = thumbletras.get(title.lower(), '')

        itemlist.append(item.clone(action='lista', title=title, url=url, thumbnail=thumbnail))

    return itemlist


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    item.url = item.url + texto

    try:
        return lista(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []


def findvideos(item):
    logger.info()
    itemlist = []
    global new_data
    new_data = []
    data = get_source(item.url)
    if not item.infoLabels.get('year', ''):
        year = scrapertools.find_single_match(data[:300], r' \((\d{4})\) ') or '-'
        item.infoLabels['year'] =  year
        tmdb.set_infoLabels_itemlist([item], seekTmdb=True)

    patron = 'aria-labelledby="([^"]+)">(.*?)</li>'
    matches = scrapertools.find_multiple_matches(data, patron)
    for scrapedlang, data in matches:

        if 'trail' in scrapedlang.lower():
            continue

        language = IDIOMAS.get(scrapedlang, scrapedlang)
        lang = audio_color.get(language, language)

        patron = '<a id="enlace".*?data-href="([^"]+)">.*?<img src.*?>([^<])'
        matches = scrapertools.find_multiple_matches(data, patron)

        for scrapedurl, info in matches:

            scrapedurl += "=="
            urls_page = base64.urlsafe_b64decode(scrapedurl)

            new_data = httptools.downloadpage(urls_page, headers={"referer": item.url}).data
            patron = 'data-embed="([^"]+)"'
            new_data = re.compile(patron, re.DOTALL).findall(new_data)

            for url in new_data:
                url = base64.urlsafe_b64decode(url+"==")
                title = ' %s [COLOR blue][%s][/COLOR]' % (lang, item.quality)
                itemlist.append(item.clone(title='%s'+title,
                                url=url,
                                action='play',
                                language=language,
                                lang=lang
                                ))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda x: x.title % x.server.capitalize())
    return itemlist

def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    # categoria='peliculas'
    try:
        if categoria == 'peliculas':
            item.url = host + 'genero/estrenos/'
        elif categoria == 'infantiles':
            item.url = host + 'genero/animacion/'
        elif categoria == 'terror':
            item.url = host + 'genero/terror/'
        itemlist = lista(item)
        if itemlist[-1].title == 'Siguiente >>>':
            itemlist.pop()
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist


def extrae_idiomas(list_language):
    logger.info()
    language=[]
    textoidiomas = ''
    
    for i, idioma in enumerate(list_language):
        lang = IDIOMAS.get(idioma, idioma)
        textoidiomas += "[%s] " % lang
        list_language[i] = lang
    
    return textoidiomas, list_language

def play(item):
    if 'video.pelisgratis.' in item.url:
        b_url = scrapertools.find_single_match(item.url, 'tor/(.*?)/')
        b_url = base64.b64decode(b_url+'==')
        try:
            l_url = b_url.split('[#]')
            n = len(l_url) - 1
            item.url = l_url[n]
            item.server='oprem'
        except:
            item.url = ''

    return [item]
