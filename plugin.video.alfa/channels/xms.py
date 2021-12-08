# -*- coding: utf-8 -*-
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                             # Usamos el nativo de PY2 que es más rápido

import re

import base64
from core import jsontools as json
from core import channeltools
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger

__channel__ = "xms"

#xtheatre XMS contenido NETU
#cam4 realizado canal separado

host = 'https://xtheatre.org/'
host1 = 'https://www.cam4.com/'
try:
    __modo_grafico__ = config.get_setting('modo_grafico', __channel__)
    __perfil__ = int(config.get_setting('perfil', __channel__))
except:
    __modo_grafico__ = True
    __perfil__ = 0

# Fijar perfil de color
perfil = [['0xFF6E2802', '0xFFFAA171', '0xFFE9D7940'],
          ['0xFFA5F6AF', '0xFF5FDA6D', '0xFF11811E'],
          ['0xFF58D3F7', '0xFF2E64FE', '0xFF0404B4']]

if __perfil__ - 1 >= 0:
    color1, color2, color3 = perfil[__perfil__ - 1]
else:
    color1 = color2 = color3 = ""

headers = [['User-Agent', 'Mozilla/50.0 (Windows NT 10.0; WOW64; rv:45.0) Gecko/20100101 Firefox/45.0'],
           ['Referer', host]]

parameters = channeltools.get_channel_parameters(__channel__)
fanart_host = parameters['fanart']
thumbnail_host = parameters['thumbnail']
thumbnail = 'https://raw.githubusercontent.com/Inter95/tvguia/master/thumbnails/adults/%s.png'


def mainlist(item):
    logger.info()
    itemlist = []

    itemlist.append(Item(channel=__channel__, title="Últimas", url=host + '?filtre=date&cat=0',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=thumbnail % '1'))

    itemlist.append(Item(channel=__channel__, title="Más Vistas", url=host + '?display=extract&filtre=views',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=thumbnail % '2'))

    itemlist.append(Item(channel=__channel__, title="Mejor Valoradas", url=host + '?display=extract&filtre=rate',
                         action="peliculas", viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=thumbnail % '3'))

    itemlist.append(Item(channel=__channel__, title="Categorías", action="categorias",
                         url=host + 'categories/', viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail=thumbnail % '4'))

    itemlist.append(Item(channel=__channel__, title="WebCam", action="webcamenu",
                         viewmode="movie_with_plot", viewcontent='movies',
                         thumbnail='https://ae01.alicdn.com/kf/HTB1LDoiaHsrBKNjSZFpq6AXhFXa9/-.jpg'))

    itemlist.append(Item(channel=__channel__, title="Buscador", action="search", url=host, thumbnail=thumbnail % '5'))

    return itemlist


def webcamenu(item):
    logger.info()
    all = "https://www.cam4.es/directoryCams?directoryJson=true&online=true&url=true&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60"
    url1= "https://www.cam4.es/directoryCams?directoryJson=true&online=true&url=true&gender=%s&broadcastType=%s_group&broadcastType=solo&broadcastType=male_female_group&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60"
        # https://www.cam4.es/directoryCams?directoryJson=true&online=true&url=true&gender=male&broadcastType=male_group&broadcastType=solo&broadcastType=male_female_group&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60
    url2= "https://www.cam4.es/directoryCams?directoryJson=true&online=true&url=true&broadcastType=male_group&broadcastType=female_group&broadcastType=male_female_group&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60"
    url3= "https://www.cam4.es/directoryCams?directoryJson=true&online=true&url=true&gender=shemale&page=1&orderBy=VIDEO_QUALITY&resultsPerPage=60"
   
    itemlist = [item.clone(title="Trending Cams", action="webcam", text_blod=True, url=all,
                           viewcontent='movies', viewmode="movie_with_plot"),
                item.clone(title="Females", action="webcam", text_blod=True,
                           viewcontent='movies', url=url1 %('female', 'female'), viewmode="movie_with_plot"),
                item.clone(title="Males", action="webcam", text_blod=True,
                           viewcontent='movies', url=url1 %('male', 'male'), viewmode="movie_with_plot"),
                item.clone(title="Couples", action="webcam", text_blod=True,
                           viewcontent='movies', url=url2, viewmode="movie_with_plot"),
                item.clone(title="Trans", action="webcam", text_blod=True, extra="Películas Por año",
                           viewcontent='movies', url=url3, viewmode="movie_with_plot")]
    return itemlist


def peliculas(item):
    logger.info()
    itemlist = []

    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|#038;", "", data)
    if "category" in item.url:
            patron = 'title="[^"]+" data-lazy-src="([^"]+)".*?'  # img
    else:
        patron = '<img width="\d+" height="\d+" src="([^"]+)".*?'
    patron += '<a href="([^"]+)" title="([^"]+)".*?'          # url, title
    patron += '<div class="right"><p>([^<]+)</p>'             # plot
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle, plot in matches:
        plot = scrapertools.decodeHtmlentities(plot)

        itemlist.append(item.clone(channel=__channel__, action="findvideos", title=scrapedtitle.capitalize(),
                                   url=scrapedurl, thumbnail=scrapedthumbnail, infoLabels={"plot": plot},
                                   fanart=scrapedthumbnail,viewmode="movie_with_plot",
                                   folder=True, contentTitle=scrapedtitle))
    # Extrae el paginador
    paginacion = scrapertools.find_single_match(data, '<a href="([^"]+)">Next &rsaquo;</a></li><li>')
    paginacion = urlparse.urljoin(item.url, paginacion)

    if paginacion:
        itemlist.append(Item(channel=__channel__, action="peliculas",
                             thumbnail=thumbnail % 'rarrow',
                             title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    return itemlist





def webcam(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>|#038;", "", data)
    JSONData = json.load(data)
    for Video in  JSONData["users"]:
        title = Video["username"]
        pais = Video["countryCode"]
        thumbnail = Video["snapshotImageLink"]
        video_url = Video["hlsPreviewUrl"]
        title =  "%s (%s)" % (title,pais)
        itemlist.append(item.clone(channel=__channel__, action="play", title=title,
                                   url=video_url, thumbnail=thumbnail, fanart=thumbnail,
                                   viewmode="movie_with_plot", folder=True, contentTitle=title))
    # Extrae el paginador
    paginacion = scrapertools.find_single_match(data, '<span id="pagerSpan">\d+</span> <a href="([^"]+)"')
    paginacion = urlparse.urljoin(item.url, paginacion)

    # if paginacion:
        # itemlist.append(Item(channel=__channel__, action="webcam",
                             # thumbnail=thumbnail % 'rarrow',
                             # title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    return itemlist


def categorias(item):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'data-lazy-src="([^"]+)".*?'
    patron += '<a href="([^"]+)".*?'
    patron += '<span>([^<]+)</span></a>.*?'
    patron += '<span class="nb_cat border-radius-5">([^<]+)</span>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedurl, scrapedtitle, vids in matches:
        title = "%s (%s)" % (scrapedtitle, vids.title())
        itemlist.append(item.clone(channel=__channel__, action="peliculas", fanart=scrapedthumbnail,
                                   title=title, url=scrapedurl, thumbnail=scrapedthumbnail,
                                   viewmode="movie_with_plot", folder=True))

    return itemlist


def search(item, texto):
    logger.info()

    texto = texto.replace(" ", "+")
    item.url = urlparse.urljoin(item.url, "?s={0}".format(texto))

    try:
        return sub_search(item)

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []


def sub_search(item):
    logger.info()

    itemlist = []
    data = httptools.downloadpage(item.url).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    patron = 'data-lazy-src="([^"]+)".*?'          # img
    patron += 'title="([^"]+)" />.*?'              # title
    patron += '</noscript><a href="([^"]+)".*?'    # url
    patron += '<div class="right"><p>([^<]+)</p>'  # plot
    matches = re.compile(patron, re.DOTALL).findall(data)

    for scrapedthumbnail, scrapedtitle, scrapedurl, plot in matches:
        itemlist.append(item.clone(title=scrapedtitle, url=scrapedurl, plot=plot, fanart=scrapedthumbnail,
                                   action="play", thumbnail=scrapedthumbnail))

    paginacion = scrapertools.find_single_match(
        data, "<a href='([^']+)' class=\"inactive\">\d+</a>")

    if paginacion:
        itemlist.append(item.clone(channel=__channel__, action="sub_search",
                                   title="\xc2\xbb Siguiente \xc2\xbb", url=paginacion))

    return itemlist


def findvideos(item):
    itemlist = []
    if "playlist.m3u8" in item.url:
        url = item.url
        itemlist.append(item.clone(action="play", title= "%s", url=url))
    else:
        data = httptools.downloadpage(item.url).data
        data = re.sub(r"\n|\r|\t|amp;|\s{2}|&nbsp;", "", data)
        data = scrapertools.find_single_match(data, '<div class="video-embed">(.*?)<div id="video-rate">')
        patron = 'src="([^"]+)"'
        matches = scrapertools.find_multiple_matches(data, patron)
        for url in matches:
            if "strdef" in url: 
                url = decode_url(url)
                if "strdef" in url:
                    url = httptools.downloadpage(url).url
            if not "/player/embed_player.php?vid=" in url: #netu
                itemlist.append(item.clone(action="play", title= "%s", url=url))
    itemlist = servertools.get_servers_itemlist(itemlist, lambda i: i.title % i.server.capitalize())
    return itemlist


def decode_url(txt):
    logger.info()
    itemlist = []
    data = httptools.downloadpage(txt).data
    data = re.sub(r"\n|\r|\t|&nbsp;|<br>", "", data)
    rep = True
    while rep == True:
        b64_data = scrapertools.find_single_match(data, '\(dhYas638H\("([^"]+)"\)')
        if b64_data:
            b64_url = base64.b64decode(b64_data + "=")
            b64_url = base64.b64decode(b64_url + "==")
            data = b64_url
        else:
            rep = False
    url = scrapertools.find_single_match(b64_url, '<iframe src="([^"]+)"')
    return url