# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido

from builtins import range
from past.utils import old_div

import re
import datetime
import time
import ast
import random
import traceback

from channelselector import get_thumb
from core import filetools
from core import scrapertools
from core import servertools
from core import channeltools
from core import tmdb
from core.item import Item
from platformcode import config, logger
from lib import generictools
from channels import filtertools
from channels import autoplay


IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'Version Original': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['torrent']

host = 'https://pctfenix.com/'
host_torrent = host[:-1]
sufix = scrapertools.find_single_match(host, '\.\w+\/*$')
download_sufix = 'descargar-gratis/'
channel_py = 'pctfenix'
categoria = channel_py.capitalize()
decode_code = ''
page_url = ''

#Carga de opciones del canal        
__modo_grafico__ = config.get_setting('modo_grafico', channel_py)               #TMDB?
IDIOMAS_TMDB = {0: 'es', 1: 'en', 2: 'es,en'}
idioma_busqueda = IDIOMAS_TMDB[config.get_setting('modo_grafico_lang', channel_py)] # Idioma base para TMDB
idioma_busqueda_VO = IDIOMAS_TMDB[2]                                                # Idioma para VO
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel_py)  #Actualización sólo últ. Temporada?
timeout = config.get_setting('timeout_downloadpage', channel_py)                #Timeout downloadpage
#timeout = timeout * 2                                                           # Incremento temporal
if timeout == 0: timeout = None
season_colapse = config.get_setting('season_colapse', channel_py)               # Season colapse?
filter_languages = config.get_setting('filter_languages', channel_py)           # Filtrado de idiomas?


def mainlist(item):
    logger.info()
    
    itemlist = []

    thumb_cartelera = get_thumb("now_playing.png")
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_pelis_VO = get_thumb("channels_vos.png")
    
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    thumb_series_VOD = get_thumb("videolibrary_tvshow.png")
    
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")

    autoplay.init(item.channel, list_servers, list_quality)
        
    itemlist.append(Item(channel=item.channel, title="Destacados:", 
                    url=host, thumbnail=thumb_cartelera, folder=False))
    itemlist.append(Item(channel=item.channel, action="listado", title="       - Novedades", 
                    url=host + "descargar-lo-ultimo", extra="novedades", thumbnail=thumb_cartelera, category=categoria))
    itemlist.append(Item(channel=item.channel, action="listado", title="       - Más Visitados", 
                    url=host + "mas-visitados", extra="novedades", thumbnail=thumb_cartelera, category=categoria))
    #itemlist.append(Item(channel=item.channel, action="listado", title="       - Más Descargados", 
    #                url=host + "mas-descargados", extra="novedades", thumbnail=thumb_cartelera, category=categoria))
    itemlist.append(Item(channel=item.channel, action="listado", title="       - Mejor Valorados", 
                    url=host + "mas-valorados", extra="novedades", thumbnail=thumb_cartelera, category=categoria))
    
    itemlist.append(Item(channel=item.channel, action="submenu", title="Películas", 
                    url=host, extra="peliculas", thumbnail=thumb_pelis, category=categoria))

    itemlist.append(Item(channel=item.channel, action="submenu", title="Series", 
                    url=host, extra="series", thumbnail=thumb_series, category=categoria))
    
    itemlist.append(Item(channel=item.channel, action="search", title="Buscar", 
                    url=host + "buscar", thumbnail=thumb_buscar, category=categoria))
    
    itemlist.append(Item(channel=item.channel, url=host, 
                    title="[COLOR yellow]Configuración:[/COLOR]", folder=False, thumbnail=thumb_separador, category=categoria))
    
    itemlist.append(Item(channel=item.channel, action="configuracion", 
                    title="Configurar canal", thumbnail=thumb_settings, category=categoria))
    
    autoplay.show_option(item.channel, itemlist)                                #Activamos Autoplay

    return itemlist
    
    
def configuracion(item):
    from platformcode import platformtools
    ret = platformtools.show_channel_settings()
    platformtools.itemlist_refresh()
    return
    

def submenu(item):
    logger.info()
    
    itemlist = []
    item.extra2 = ''
    matches_hd = []
    
    data, success, code, item, itemlist = generictools.downloadpage(item.url, timeout=timeout, s2=False, 
                                          decode_code=decode_code, quote_rep=True, item=item, itemlist=[])      # Descargamos la página
        
    patron = '<div\s*class="[^"]+">\s*<h4>\s*Categorias\s*<\/h4>\s*<ul>(.*?)<\/ul>\s*<\/div>'
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(data)

    data_menu = scrapertools.find_single_match(data, patron)                    #Seleccionamos el trozo que nos interesa
    if not data_menu:
        try:
            logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " 
                    + " / PATRON: " + patron + " / DATA: " + data)
        except:
            logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " 
                    + " / PATRON: " + patron + " / DATA: (probablemente bloqueada por antivirus)")
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  ' 
                    + ' Reportar el error con el log'))
        return itemlist                                                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    # Procesamos la página
    patron = '<li><a\s*(?:style="[^"]+"\s*)?href="([^"]+)"\s*.itle="[^"]+"\s*>'
    patron += '(?:<i\s*class="[^"]+">\s*<\/i>)?([^>]+)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data_menu)

    #logger.debug(patron)
    #logger.debug(matches)
    #logger.debug(data_menu)
    
    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                    " / PATRON: " + patron + " / DATA: " + data_menu)
        itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  ' 
                    + 'Reportar el error con el log'))
        return itemlist                                                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    for scrapedurl, scrapedtitle in matches:
        title = scrapedtitle.strip()
        url = urlparse.urljoin(host, scrapedurl)
        if 'otras-peliculas' in url:
            continue

        #Preguntamos por las entradas que no corresponden al "extra"
        if item.extra in scrapedtitle.lower() or (item.extra == "peliculas" and \
                    ("cine" in scrapedurl or "anime" in scrapedurl)):
            
            #Si tiene filtro de idiomas, marcamos estas páginas como no filtrables
            if "castellano" in title.lower() or "latino" in title.lower() or \
                    "subtituladas" in title.lower() or "vo" in title.lower() or \
                    "v.o" in title.lower() or "- es" in title.lower():
                item.extra2 = "categorias"
            else:
                item.extra2 = ""
            
            itemlist.append(item.clone(action="listado", title=title, url=url+page_url))

    # Para películas, ahondamos en calidades
    if item.extra == "peliculas":
        patron = '<div\s*class="title-hd\s*subca">(.*?)<\/div>'
        data_hd = scrapertools.find_single_match(data, patron)                  #Seleccionamos el trozo que nos interesa
        if data_hd:
            patron = '<a\s*href="([^"]+)"\s*.itle="[^"]+"\s*>([^<]+)\s*<'
            matches_hd = re.compile(patron, re.DOTALL).findall(data_hd)
            #logger.debug(matches_hd)
            if matches_hd:
                itemlist.append(item.clone(action="", title="[COLOR yellow]Calidades:[/COLOR]", folder=False))
                for scrapedurlcat, scrapedtitlecat in matches_hd:               #Pintamos las categorías de peliculas en HD
                    urlcat = urlparse.urljoin(host, scrapedurlcat)
                    itemlist.append(item.clone(action="listado", title="   - Calidad: " 
                            + scrapedtitlecat, url=urlcat+page_url))

    return itemlist


def listado(item):                                                              # Listado principal y de búsquedas
    logger.info()
    
    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")

    #logger.debug(item)
    
    curr_page = 0                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    last_page_print = 1                                                         # Última página inicial, para píe de página
    page_url = urlparse.urljoin(host, '/controllers/load-more.php')             # URL para paginar
    page_post_url = '/' + item.url.replace(host, '')
    page_post = 'i=%s&c=300&u=%s'                                               # Paginador
    
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    if item.last_page_print:
        last_page_print = item.last_page_print                                  # Si viene de una pasada anterior, lo usamos
        del item.last_page_print                                                # ... y lo borramos
    if item.cnt_tot_match:
        cnt_tot_match = float(item.cnt_tot_match)                               # restauramos el contador TOTAL de líneas procesadas de matches
        del item.cnt_tot_match
    else:
        cnt_tot_match = 0.0                                                     # Contador TOTAL de líneas procesadas de matches
    
    cnt_tot = 30                                                                # Poner el num. máximo de items por página
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 5                                                            # Después de este tiempo pintamos (segundos)
    timeout_search = timeout * 2                                                # Timeout para descargas
    if item.extra == 'search' and item.extra2 == 'episodios':                   # Si viene de episodio se quitan los límites
        cnt_tot = 999
        fin = inicio + 30

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                            # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                                    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista.extend(item.title_lista)                                    # Se usa la lista de páginas anteriores en Item
        del item.title_lista                                                    # ... limpiamos
    matches = []
        
    if not item.extra2:                                                         # Si viene de Catálogo o de Alfabeto
        item.extra2 = ''
        
    post = None
    forced_proxy_opt = None
    if item.post:
        forced_proxy_opt = None
    if item.post or item.post is None:                                          # Rescatamos el Post, si lo hay
        post = item.post
        del item.post
    if item.page_post_url:
        page_post_url = item.page_post_url
        del item.page_post_url
    next_page_url = item.url
    
    #Máximo num. de líneas permitidas por TMDB. Máx de 5 segundos por Itemlist para no degradar el rendimiento
    while (cnt_title < cnt_tot and curr_page <= last_page and fin > time.time()) or item.matches:
    
        # Descarga la página
        data = ''
        fichas = ''
        cnt_match = 0                                                           # Contador de líneas procesadas de matches

        if not item.matches:                                                    # si no viene de una pasada anterior, descargamos
            data, success, code, item, itemlist = generictools.downloadpage(next_page_url, 
                                          timeout=timeout_search, post=post, s2=True, 
                                          decode_code=decode_code, quote_rep=True, 
                                          forced_proxy_opt=forced_proxy_opt, 
                                          no_comments=False, item=item, itemlist=itemlist)
            fichas = data
            curr_page += 1                                                      #Apunto ya a la página siguiente
            
            if item.extra == "search":
                patron = '<a\s*href="([^"]+)">\s*<img\s*src="([^"]+)"\s*'       #url, thumb
                patron += 'alt="([^"]+)"[^<]+>\s*<h6>([^<]+)<\/h6>()\s*<\/a>'   #título_alt, #título, calidad (vacío)
            else:
                patron = '<div\s*class="slide-it[^>]+>\s*<div\s*class="movie-item">\s*'
                patron += '<div\s*class="mv-img">\s*<img\s*src="([^"]+)"\s*alt="([^"]+)"[^>]+>\s*<\/div>\s*'

            #logger.debug("PATRON: " + patron)
            #logger.debug(data)
            
            #Ver si hay datos consistentes
            if not data or not scrapertools.find_single_match(data, patron):
                
                """ TEMPORAL: aparente error en la Web """
                if last_page == 99999 and next_page_url != page_url and item.extra != "search":
                    next_page_url = page_url
                    post = page_post % (1, page_post_url)
                    continue

                last_page = 0
                if len(itemlist) > 0 or success:                                # Si hay algo que pintar lo pintamos
                    break

                logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL" 
                        + " / PATRON: " + patron + " / DATA: " + data)
                cnt_tot_match += len(itemlist)
              
                itemlist.append(item.clone(action='', title=item.category + 
                            ': ERROR 01: LISTADO: La Web no responde o ha cambiado de URL. ' 
                            + 'Si la Web está activa, reportar el error con el log'))

                return itemlist                                                 #Salimos
        
        #Scrapea los datos de cada vídeo.  Título alternativo se mantiene, aunque no se usa de momento
        if item.extra == "search":
            patron = '<a\s*href="([^"]+)">\s*<img\s*src="([^"]+)"\s*'           #url, thumb
            patron += 'alt="([^"]+)"[^<]+>\s*<h6>([^<]+)<\/h6>()\s*<\/a>'       #título_alt, #título, calidad (vacío)
        else:
            patron = '<div\s*class="slide-it[^>]+>\s*<div\s*class="movie-item">\s*'
            patron += '<div\s*class="mv-img">\s*<img\s*src="([^"]+)"\s*alt="([^"]+)"[^>]+>\s*<\/div>\s*'    #thumb, Alt
            patron += '<div\s*class="hvr-inner">\s*<a\s*href="([^"]+)"[^>]+>[^<]+<i\s*'                     #url
            patron += 'class=[^>]+>\s*<\/i>\s*<\/a>\s*<\/div>\s*<div\s*class="title-in">\s*'
            patron += '<h6>\s*<a\s*href="[^>]+>([^<]+)<\/a>\s*<\/h6>\s*(?:<strong>)?([^<]*)(?:<\/strong>)?' #título, calidad

        if not item.matches:                                                    # De pasada anterior?
            matches = re.compile(patron, re.DOTALL).findall(fichas)
        else:
            matches = item.matches
            del item.matches
            
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(fichas)

        if not matches:                                                         #error
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + " / DATA: " + fichas)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log'))
            if len(itemlist) > 1:                                               # Si hay algo que pintar lo pintamos
                last_page = 0
                break
            return itemlist                                                     #Salimos

        """
        #Buscamos la última página
        """
        if last_page == 99999:                                                  #Si es el valor inicial, buscamos
            post = page_post % (last_page, page_post_url)
            last_page == 999
        
        #Buscamos la próxima página
        if post:                                                                # Search o Novedades antiguas
            post = page_post % (curr_page, page_post_url)
            next_page_log = item.page_url

        """
        #Empezamos el procesado de matches
        """
        for _scrapedthumbnail, alt, _scrapedurl, _scrapedtitle, _calidad in matches:
            
            scrapedurl = _scrapedurl
            scrapedtitle = _scrapedtitle
            scrapedthumbnail = _scrapedthumbnail
            calidad = _calidad
            if not calidad:
                calidad = scrapertools.find_single_match(scrapedthumbnail, '\-\-(?:.*?\-\-)?(?:.*?\-\-)?(.*?)\.jpg').replace('-', ' ')
            year = ''
            size = ''
            
            if item.extra == 'search':                                          # Cambia el orden de las variables
                scrapedurl = _scrapedthumbnail
                scrapedthumbnail = alt
                alt = _scrapedurl
                last_page = 0                                                   # No hay forma de obtener más páginas

            scrapedurl = urlparse.urljoin(host, scrapedurl)
            scrapedthumbnail = urlparse.urljoin(host, scrapedthumbnail)

            cnt_match += 1
            
            title = scrapedtitle.strip()
            title = scrapertools.remove_htmltags(title).rstrip('.')             # Removemos Tags del título
            url = scrapedurl
            title_subs = []                                                     # creamos una lista para guardar info importante

            # Si es una serie, se guarda la info de temp x epi para futuro uso, y se limpia en título
            contentSeason = ''
            contentEpisodeNumber = 1
            contentEpisodeNumber_multi = ''
            if 'descargar-series/' in item.url or 'temporada' in url:
                try:
                    contentSeason = int(scrapertools.find_single_match(url, 'temporada-(\d+)'))
                    contentEpisodeNumber = int(scrapertools.find_single_match(url, 'capitulo-(\d+)'))
                except:
                    pass
                contentEpisodeNumber_multi = scrapertools.find_single_match(url, 'capitulo-\d+-al-(\d+)')
                #url = re.sub('temporada-\d+', 'temporada-1', url)
                #url = re.sub('capitulo-\d+(?:-al-\d+)?', 'capitulo-01', url)
                title = scrapertools.find_single_match(title, '(^.*?)\s*(?:-\s*)?[T|t]emp')     #Quitamos info de temp x epi

            # Slugify, pero más light
            title = title.replace("á", "a").replace("é", "e").replace("í", "i")\
                    .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                    .replace("ï¿½", "ñ").replace("Ã±", "ñ")
            title = scrapertools.decode_utf8_error(title)

            #logger.debug(title)
            
            # Se filtran las entradas para evitar duplicados de Temporadas
            if url in title_lista or scrapedthumbnail in title_lista:           # si ya se ha tratado, pasamos al siguiente item
                continue                                                        # solo guardamos la url para series y docus
            elif 'descargar-series/' in item.url or 'temporada' in scrapedurl:
                if item.extra == 'search':                                      # Desde Search no viene calidad, se adivina
                    if 'hdtv720p' not in url and url+'hdtv720p' not in title_lista:
                        url += 'hdtv720p'
                        if not calidad: calidad = 'HDTV 720p AC3 5.1'
                    else:
                        if not calidad: calidad = 'HDTV'
                if item.extra != "novedades":
                    if title in title_lista:
                        continue
                    else:
                        title_lista += [title]
                title_lista += [url]
                title_lista += [scrapedthumbnail]

            # Tratamiento especial para Novedades, con opciones como 4K
            if item.extra == "novedades" and item.extra2:
                if not item.extra2 in url and not item.extra2 in scrapedtitle and not item.extra2 in scrapedthumbnail:
                    continue
            
            cnt_title += 1                                                      # Incrementamos el contador de entradas válidas
            
            item_local = item.clone()                                           # Creamos copia de Item para trabajar
            if item_local.tipo:                                                 # ... y limpiamos
                del item_local.tipo
            if item_local.totalItems:
                del item_local.totalItems
            if item_local.post:
                del item_local.post
            if item_local.pattern:
                del item_local.pattern
            if item_local.intervencion:
                del item_local.intervencion
            if item_local.viewmode:
                del item_local.viewmode
            item_local.extra2 = True
            del item_local.extra2
            item_local.text_bold = True
            del item_local.text_bold
            item_local.text_color = True
            del item_local.text_color
            item_local.matches = []
            del item_local.matches
            item_local.title_lista = []
            del item_local.title_lista
            
            item_local.title = ''
            item_local.context = "['buscar_trailer']"
            item_local.quality = calidad
            
            #Guardamos el resto de variables del vídeo
            item_local.url = url
            item_local.thumbnail = scrapedthumbnail
            item_local.contentThumbnail = item_local.thumbnail

            """Si vienen de Novedades, se prepara el título para las series"""
            if item.extra == "novedades" and 'temporada' in scrapedurl and contentSeason:
                if contentEpisodeNumber_multi:
                    title_subs += ["Episodio %sx%s-al-%s" % (str(contentSeason), \
                                      str(contentEpisodeNumber).zfill(2), str(contentEpisodeNumber_multi).zfill(2))]
                else:
                    title_subs += ["Episodio %sx%s" % (str(contentSeason), str(contentEpisodeNumber).zfill(2))]

            
            
            #Establecemos los valores básicos en función del tipo de contenido
            if (item_local.extra == "series" or 'descargar-series/' in item.url \
                            or 'temporada' in scrapedurl or "serie" in scrapedurl): #Series
                item_local.action = "episodios"
                item_local.contentType = "tvshow"
                item_local.season_colapse = True
                item_local.extra = "series"
            else:                                                                   #Películas
                item_local.action = "findvideos"
                item_local.contentType = "movie"
                item_local.extra = "peliculas"
                size = size.replace(".", ",")
                if size:
                    item_local.quality = '%s [%s]' % (item_local.quality, size)

            #Determinamos y marcamos idiomas
            item_local.language = []
            if "[vos" in title.lower() or "v.o.s" in title.lower() or "vo" in title.lower() \
                        or "subs" in title.lower() or "-vo/" in scrapedurl or "vos" in \
                        calidad.lower() or "vose" in calidad.lower() or "v.o.s" in calidad.lower() \
                        or "sub" in calidad.lower() or "-vo/" in item.url or "sbs" in title.lower() :
                item_local.language += ["VOS"]                                  # VOS
            if "latino" in title.lower() or "argentina" in title.lower() or "-latino/" in \
                        scrapedurl or "latino" in calidad.lower() or "argentina" in calidad.lower() \
                        or "latino" in item.url:
                item_local.language += ["LAT"]                                  # LAT
            if "[dual" in title.lower() or "multileng" in title.lower() or "multileng" \
                        in item_local.quality.lower() or (("espa" in title.lower() or \
                        "spani" in title.lower()) and "VOS" in item_local.language):
                title = re.sub(r'\[[D|d]ual.*?\]', '', title)
                title = re.sub(r'\[[M|m]ultileng.*?\]', '', title)
                item_local.quality = re.sub(r'\[[M|m]ultileng.*?\]', '', item_local.quality)
                item_local.language[0:0] = ["DUAL"]                             # DUAL
            if "VOS" in item_local.language and "DUAL" not in item_local.language and \
                        ("[sp" in item_local.quality.lower() or "espa" in item_local.quality.lower() \
                        or "cast" in item_local.quality.lower() or "spani" in item_local.quality.lower()):
                item_local.language[0:0] = ["DUAL"]                             # DUAL 
            if ("[es-" in item_local.quality.lower() or (("cast" in item_local.quality.lower() \
                        or "espa" in item_local.quality.lower() or "spani" in \
                        item_local.quality.lower()) and ("eng" in item_local.quality.lower() \
                        or "ing" in item_local.quality.lower()))) and "DUAL" not in \
                        item_local.language:
                item_local.language[0:0] = ["DUAL"]                             # DUAL
            if not item_local.language:
                item_local.language = ["CAST"]                                  # Si no hay otro idioma, ponero CAST por defecto
            
            #Guardamos info de 3D en calidad y limpiamos
            if "3d" in title.lower():
                if not "3d" in item_local.quality.lower():
                    item_local.quality = item_local.quality + " 3D"
                calidad3D = scrapertools.find_single_match(title, r'(?i)3d\s*(?:h-*\s*sbs\s|sbs\s|hou\s*|aa\s*|ou\s*)?\s*').strip()
                if calidad3D:
                    item_local.quality = item_local.quality.replace("3D", calidad3D)
                title = re.sub(r'(?i)3d\s*(?:h-*\s*sbs\s|sbs\s|hou\s*|aa\s*|ou\s*)?\s*', '', title)
                if "imax" in title.lower():
                    item_local.quality = item_local.quality + " IMAX"
                    title = re.sub(r'(?i)(?:version)?\s*imax\s*', '', title)
            if "2d" in title.lower():
                title = re.sub(r'(?i)\s*.2d.\s*', '', title)
                title_subs += ["[2D]"]
            if "HDR" in title:
                title = title.replace(" HDR", "")
                if not "HDR" in item_local.quality:
                    item_local.quality += " HDR"    

            #Terminamos de preparar la calidad
            item_local.quality = re.sub(r'(?i)\[es-\w+]|[\s|-]caste\w+|[\s|-]espa\w+|[\s|-|\[]spani\w+|[\s|-].ngl\w+', '', item_local.quality)
            item_local.quality = re.sub(r'(?i)proper|unrated|directors|cut|repack|internal|real|gratis', '', item_local.quality)
            item_local.quality = re.sub(r'(?i)extended|masted|docu|super|duper|amzn|uncensored|hulu', '', item_local.quality)
            item_local.quality = re.sub(r'(?i)[\s|-]latino\s*|[\+|-]*subs|vose\s*|vos\s*', '', item_local.quality)
            item_local.quality = re.sub(r'(?i)\[\d{4}\]\s*|\[cap.*?\]\s*|\s*cap\w*\s*|\[docu.*?\]\s*|\[\s*|\]\s*', '', item_local.quality)
            item_local.quality = item_local.quality.replace("ALTA DEFINICION", "HDTV").strip()
            
            #Eliminamos Temporada de Series, solo nos interesa la serie completa
            if ("temp" in title.lower() or "cap" in title.lower()) and item_local.contentType != "movie":
                title = re.sub(r'(?i)(?:-*\s*temp\w*\.*\s*\d+\s*)?(?:cap\w*\.*\s*\d+\s*)?(?:al|Al|y)\s*\d+', '', title)
                title = re.sub(r'(?i)-*\s*temp\w*\.*\s*\d+(?:x\d+)?', '', title)
                title = re.sub(r'(?i)-*\s*cap.*?\d+(?:\s*al\s*\d+)?', '', title)
            if "audio" in title.lower():                                        #Reservamos info de audio para después de TMDB
                title_subs += ['[%s]' % scrapertools.find_single_match(title, r'(\[[a|A]udio.*?\])')]
                title = re.sub(r'\[[a|A]udio.*?\]', '', title)
            if "duolog" in title.lower() or "trilog" in title.lower() or "saga" in title.lower():
                title_subs += ["[Saga]"]
                title = re.sub(r'(?i)duolog\w*|trilog\w*|\s*saga\s*.ompleta|\s*saga', '', title)
            if scrapertools.find_single_match(title, r'(?i)version\s*ext\w*|\(version\s*ext\w*\)|v\.\s*ext\w*|V\.E\.'):
                title_subs += ["[V. Extendida]"]
                title = re.sub(r'(?i)version\s*ext\w*|\(version\s*ext\w*\)|v\.\s*ext\w*|V\.E\.', '', title)
            if "colecc" in title.lower() or "completa" in title.lower():
                title = re.sub(r'(?i)\s*colecci..|\s*completa', '', title)
            if scrapertools.find_single_match(title, r'(- [m|M].*?serie ?\w+)'):
                title = re.sub(r'(?i)-*\s*m.*?serie\s*\w*', '', title)
                title_subs += ["[Miniserie]"]

            #Limpiamos restos en título
            title = re.sub(r'(?i)castellano|español|ingl.s\s*|english\s*|calidad|de\s*la\s*serie|spanish|Descarga\w*\s*\w+\-\w+', '', title)
            title = re.sub(r'(?i)ver\s*online\s*(?:serie\s*)|descarga.*\s*Serie\s*(?:hd\s*)?|ver\s*en\s*linea\s*|v.o.\s*|cvcd\s*', '', title)
            title = re.sub(r'(?i)en\s*(?:Full\s*)?HD\s*|microhd\s*|hdtv\s*|\(proper\)\s*|ratdvd\s*|dvdrip\s*|dvd.*\s*|dvbrip\s*', '', title)
            title = re.sub(r'(?i)ESDLA\s*|dvb\s*|descarga\w*\s*|torrent\s*|gratis\s*|estreno\w*\s*', '', title)
            title = re.sub(r'(?i)(?:la\s*)?pelicula\w*\s*en\s*latino\s*|(?:la\s*)?pelicula\w*\s*|descarga\w*\s*todas\s*', '', title)
            title = re.sub(r'(?i)bajar\s*|hdrip\s*|rip\s*|xvid\s*|ac3\s*5\.1\s*|ac3\s*|1080p\s*|720p\s*|dvd-screener\s*', '', title)
            title = re.sub(r'(?i)ts-screener\s*|screener\s*|bdremux\s*|4k\s*uhdrip\s*|full\s*uhd4k\s*|4kultra\s*|2cd\s*', '', title)
            title = re.sub(r'(?i)fullbluray\s*|en\s*bluray\s*|bluray\s*en\s*|bluray\s*|bonus\s*disc\s*|de\s*cine\s*', '', title)
            title = re.sub(r'(?i)telecine\s*|argentina\s*|\+\+sub\w+\s*|\+-\+sub\w+\s*|directors\s*cut\s*|\s*en\s*hd', '', title)
            title = re.sub(r'(?i)subs.\s*integrados\s*|subtitulos\s*|blurayrip(?:\])?|descarga\w*\s*otras\s*|\(comple.*?\)', '', title).strip()
            title = re.sub(r'(?i)resubida|montaje\s*del\s*director|-*v.cine\s*|x264\s*|mkv\s*|sub\w*\s*|sbs', '', title).strip()
            title = title.replace("a?o", 'año').replace("a?O", 'año').replace("A?o", 'Año')\
                    .replace("A?O", 'Año').strip()
            title = title.replace("(", "-").replace(")", "-").replace(".", " ").strip()
            if "en espa" in title: title = title[:-11]

            #Guardamos el año que puede venir en el título, por si luego no hay resultados desde TMDB
            if scrapertools.find_single_match(title, r'\s+[\[|\(|-]*(\d{4})[\]|\)|-]*\s*'):
                year = int(scrapertools.find_single_match(title, r'\s+[\[|\(|-]*(\d{4})[\]|\)|-]*\s*'))
                if title != str(year):
                    title = re.sub(r'\s+[\[|\(|-]*(\d{4})[\]|\)|-]*\s*', '', title)
                else:
                    year = ''
            else:
                year = ''
            if year and year >= 1900 and year <= 2040:
                item_local.infoLabels['year'] = year
            else:
                item_local.infoLabels['year'] = '-'

            # Normalizamos títulos
            if item_local.contentType == "tvshow":
                title = scrapertools.find_single_match(title, '(^.*?)(?:$|\s+\(|\s+\[|\s+-)')
            if not title:
                title = "SIN TITULO"
            title = re.sub(r'(?:-\s*)?ES\s*|\(4k\)\s*|\[4k\]\s*|\(|\)|\[|\]|BR\s*|[\(|\[]\s+[\)|\]]|\(\)\s*|\[\]\s*|\+\s*', '', title)
            title = re.sub(r'\s*-\s*', ' ', title)
            item_local.from_title = title.strip().lower().title()               #Guardamos esta etiqueta para posible desambiguación de título
            item_local.title = title.strip().lower().title()

            #Salvamos el título según el tipo de contenido
            if item_local.contentType == "movie":
                item_local.contentTitle = item_local.title
            else:
                item_local.contentSerieName = item_local.title

            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale.  Excluye categorías en otros idiomas.
            if filter_languages > 0 and item.extra2 != 'categorias':
                itemlist = filtertools.get_link(itemlist, item_local, list_language)
            else:
                itemlist.append(item_local.clone())                             #Si no, pintar pantalla
            
            cnt_title = len(itemlist)                                           # Recalculamos los items después del filtrado
            if cnt_title >= cnt_tot and (len(matches) - cnt_match) + cnt_title > cnt_tot * 1.3:     #Contador de líneas añadidas
                break
            
            #logger.debug(item_local)
    
        matches = matches[cnt_match:]                                           # Salvamos la entradas no procesadas
        cnt_tot_match += cnt_match                                              # Calcular el num. total de items mostrados
    
    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__, idioma_busqueda=idioma_busqueda)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    # Si es necesario añadir paginacion
    if curr_page <= last_page or len(matches) > 0:
        curr_page_print = int(cnt_tot_match / float(cnt_tot))
        if curr_page_print < 1:
            curr_page_print = 1
        title = '%s' % curr_page_print

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " 
                        + title, title_lista=title_lista, url=page_url, page_post_url=page_post_url, extra=item.extra, 
                        extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page), 
                        cnt_tot_match=str(cnt_tot_match), matches=matches, 
                        last_page_print=last_page_print, post=post))

    return itemlist

    
def findvideos(item):
    logger.info()
    
    itemlist = []
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    matches = []
    data = ''
    code = 0
    if not item.language:
        item.language = ['CAST']                                                #Castellano por defecto
    
    #logger.debug(item)

    """ Descarga la página """
    data_servidores = ''
    enlaces_ver = []
    enlaces_descargar = []
    data_servidores_stat = False
    size = ''
    post = None
    timeout_search = timeout * 2                                                # Timeout para descargas
    forced_proxy_opt = None
    if item.post:
        forced_proxy_opt = None
        #timeout_search = timeout * 3                                            # Timeout para proxy
        post = item.post
        del item.post
    else:
        if not download_sufix in item.url:
            item.url = item.url.replace(sufix, sufix+download_sufix)
    
    if not item.matches:
        data, success, code, item, itemlist = generictools.downloadpage(item.url, timeout=timeout_search, 
                                          decode_code=decode_code, quote_rep=True, post=post, 
                                          item=item, itemlist=[])               # Descargamos la página)
        data = data.replace("$!", "#!").replace("Ã±", "ñ").replace("//pictures", "/pictures")

    """ Procesamos los datos de las páginas """

    # Salvamos el enlace .torrent
    #Patron para .torrent
    patron = '<div\s*class=\s*"ctn[^"]+"[^>]*>\s*<a\s*href=\s*"(?:javascript:)?[^"]*"'
    patron += '\s*id=\s*"btn-[^"]+"\s*data-ut=\s*"([^"]+)"'
    if not scrapertools.find_single_match(data, patron):
        patron = '<div\s*class=\s*"ctn[^"]+"[^>]*>\s*<a\s*href=\s*"(?:javascript:)?([^"]+)"'
        patron += '\s*id=\s*"btn-[^"]+"'
    url_torr = scrapertools.find_single_match(data, patron)
    if 'javascript:' in url_torr: url_torr = ''
    if url_torr:
        url_torr = urlparse.urljoin(host, url_torr)
    url_torr = url_torr.replace(" ", "%20")                                     #sustituimos espacios por %20, por si acaso
    
    # Salvamos los enlaces DIRECTOS
    #Seleccionar el bloque para evitar duplicados
    patron_ver = '<h4>DESCARGAS DIRECTA EN 1 LINK<\/h4>(.*?)<\/div>'
    data_ver = scrapertools.find_single_match(data, patron_ver)
    patron_descargar = '<h4>LINKS INTERCAMBIABLES<\/h4>(.*?)<\/div>'
    data_descargar = scrapertools.find_single_match(data, patron_descargar)
    data_descargar = re.sub('\s+', ' ', data_descargar)

    # Patrón para Servidores
    patron_directos = '<a\s*href=\s*(?:"javascript:modlinks\()?"([^"]+)"(?:\);")?'
    patron_directos += '\s*(?:target=\s*"_blank"\s*)?style=\s*"[^"]+">\s*([^<]+)\s*<\/a>'
    if data_ver: enlaces_ver = re.compile(patron_directos, re.DOTALL).findall(data_ver)
    if data_descargar: enlaces_descargar = re.compile(patron_directos, re.DOTALL).findall(data_descargar)

    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if (not data and not item.matches) or code == 999 or (not url_torr and not enlaces_ver and not enlaces_descargar): # Si no hay datos o url, error
        if not url_torr and not enlaces_ver and not enlaces_descargar and 'Archivo torrent no Existe' in data:
            return itemlist                                                     #No hay enlaces
        
        logger.error("ERROR 02: FINDVIDEOS: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + " / DATA: ")     # + str(data)
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            url_torr = item.emergency_urls[0][0]                                #Restauramos la url
            if len(item.emergency_urls) > 1 and item.emergency_urls[1]:
                data_ver = item.emergency_urls[1]                               #Restauramos matches de VER de vídeos
            if len(item.emergency_urls) > 2 and item.emergency_urls[2]:
                data_descargar = item.emergency_urls[2]                         #Restauramos matches de DESCARGAR de vídeos
            item.armagedon = True                                               #Marcamos la situación como catastrófica
            data = 'xyz123'                                                     #Para que no haga más preguntas
        else:
            #Si no hay datos consistentes, nos vamos
            itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. ' 
                        + 'Si la Web está activa, reportar el error con el log', 
                        folder=False))
            if item.videolibray_emergency_urls:
                return item
            else:
                return itemlist                                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    if not item.armagedon:
        if item.matches:
            matches = item.matches
            del item.matches

    #logger.debug("PATRON Torrent: " + patron)
    #logger.debug("PATRON directos: " + patron_directos)
    #logger.debug(enlaces_ver)
    #logger.debug(enlaces_descargar)
    #logger.debug(matches)
    #logger.debug(data)

    #Si es un lookup para cargar las urls de emergencia en la Videoteca, lo iniciamos
    if item.videolibray_emergency_urls:
        item.emergency_urls = []
        item.emergency_urls.append([])                                          #Guardamos el enlace del .torrent
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    
    """ Tratamos los enlaces .torrent de calidades alternativas """
    matches_torent = []
    if item.armagedon and item.url_quality_alt:
        for url in item.emergency_urls[0]:
            matches_torent.append((url, item.quality, '', ''))
    elif url_torr:
        matches_torent.append((url_torr, item.quality, size, data))

    if not item.armagedon and item.url_quality_alt:
        for post_match, quality in item.url_quality_alt:
            url_torr = item.url
            size = ''

            if not url_torr.startswith('magnet'):
                if url_torr.startswith('http') or url_torr.startswith('//'):
                    url_torr = urlparse.urljoin(host, url_torr)
                
                data_alt, success, code, item, itemlist = generictools.downloadpage(url_torr, timeout=timeout_search, 
                                          decode_code=decode_code, quote_rep=True, post=post_match, 
                                          item=item, itemlist=itemlist)         # Descargamos la página)
                data_alt = data_alt.replace("$!", "#!").replace("Ã±", "ñ").replace("//pictures", "/pictures")
                
                #Patron para .torrent
                patron = '<div\s*class=\s*"ctn[^"]+"[^>]*>\s*<a\s*href=\s*"(?:javascript:)?[^"]*"'
                patron += '\s*id=\s*"btn-[^"]+"\s*data-ut=\s*"([^"]+)"'
                if not scrapertools.find_single_match(data, patron):
                    patron = '<div\s*class=\s*"ctn[^"]+"[^>]*>\s*<a\s*href=\s*"(?:javascript:)?([^"]+)"'
                    patron += '\s*id=\s*"btn-[^"]+"'
                
                if 'Archivo torrent no Existe' in data_alt:
                    url_torr = ''
                else:
                    url_torr = scrapertools.find_single_match(data_alt, patron)
                if 'javascript:' in url_torr: url_torr = ''
                if url_torr:
                    url_torr = urlparse.urljoin(host, url_torr)
                else:
                    continue
                url_torr = url_torr.replace(" ", "%20")                         #sustituimos espacios por %20, por si acaso

            matches_torent.append((url_torr, quality, size, data_alt))
    
    """ Ahora tratamos los enlaces .torrent """
    for x, (url, quality, _size, _data) in enumerate(matches_torent):
        url_torr = url
        size = _size
        data = _data

        if url_torr.startswith('http') or url_torr.startswith('//'):
            url_torr = generictools.convert_url_base64(url_torr, host_torrent)
        else:
            url_torr = generictools.convert_url_base64(url_torr)
        
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()

        item_local.url = url_torr
        item_local.quality = quality

        # Restauramos urls de emergencia si es necesario
        local_torr = ''
        if item.emergency_urls and not item.videolibray_emergency_urls:
            try:                                                                # Guardamos la url ALTERNATIVA
                if item.emergency_urls[0][0].startswith('http') or item.emergency_urls[0][0].startswith('//'):
                    item_local.torrent_alt = generictools.convert_url_base64(item.emergency_urls[0][0], host_torrent)
                else:
                    item_local.torrent_alt = generictools.convert_url_base64(item.emergency_urls[0][0])
            except:
                item_local.torrent_alt = ''
                item.emergency_urls[0] = []
            from core import filetools
            if item.contentType == 'movie':
                FOLDER = config.get_setting("folder_movies")
            else:
                FOLDER = config.get_setting("folder_tvshows")
            if item.armagedon and item_local.torrent_alt:
                item_local.url = item_local.torrent_alt                         # Restauramos la url
                if not item.torrent_alt.startswith('http'):
                    local_torr = filetools.join(config.get_videolibrary_path(), FOLDER, item_local.url)
            if len(item.emergency_urls[0]) > 1:
                del item.emergency_urls[0][0]
        
        #Buscamos tamaño en el archivo .torrent
        if not size and not item.videolibray_emergency_urls:
            size = generictools.get_torrent_size(item_local.url, local_torr=local_torr)   #Buscamos el tamaño en el .torrent
            if 'ERROR' in size and item.emergency_urls and not item.videolibray_emergency_urls:
                item_local.armagedon = True
                try:                                                        # Restauramos la url
                    if item.emergency_urls[0][0].startswith('http') or item.emergency_urls[0][0].startswith('//'):
                        item_local.url = generictools.convert_url_base64(item.emergency_urls[0][0], host_torrent)
                    else:
                        item_local.url = generictools.convert_url_base64(item.emergency_urls[0][0])
                        if not item.url.startswith('http'):
                            local_torr = filetools.join(config.get_videolibrary_path(), FOLDER, item_local.url)
                except:
                    item_local.torrent_alt = ''
                    item.emergency_urls[0] = []
                size = generictools.get_torrent_size(item_local.url, local_torr=local_torr)

        if size:
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
            item_local.torrent_info = '%s, ' % size                             #Agregamos size
        item.quality = re.sub(r'\s\[\d+,?\d*?\s\w\s?[b|B]\]', '', item.quality) #Quitamos size de calidad, si lo traía
        if item_local.url.startswith('magnet:'):
            item_local.torrent_info += ' Magnet'
        if item_local.torrent_info:
            item_local.torrent_info = item_local.torrent_info.strip().strip(',')
            #item.torrent_info = item_local.torrent_info
            if not item.unify:
                item_local.torrent_info = '[%s]' % item_local.torrent_info
   
        # Guadamos la password del RAR                                          ######### REVISAR
        patron_pass = '<input\s*type="text"\s*id="txt_password"\s*name="[^"]+"\s*onClick="[^"]+"\s*value="([^"]+)"'
        if scrapertools.find_single_match(data, patron_pass):
            password = scrapertools.find_single_match(data, patron_pass)
            if password or item.password:
                if not item.password:
                    item.password = password
                    itemlist.append(item.clone(action="", title="[COLOR magenta][B] Contraseña: [/B][/COLOR]'" 
                            + item.password + "'", folder=False))
                item_local.password = item.password

        #Si es un lookup para cargar las urls de emergencia en la Videoteca, guardarmos los enlaces
        if item.videolibray_emergency_urls:
            item.emergency_urls[0].append(url_torr)                             #Guardamos el enlace del .torrent
        
        #... ejecutamos el proceso normal
        else:
            if item.armagedon:
                item_local.quality = '[COLOR hotpink][E][/COLOR] [COLOR limegreen]%s[/COLOR]' % item_local.quality
            
            #Ahora pintamos el link del Torrent
            item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                            + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                            (item_local.quality, str(item_local.language), \
                            item_local.torrent_info)
            
            #Preparamos título y calidad, quitando etiquetas vacías
            item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
            item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
            item_local.title = item_local.title.replace("--", "").replace("[]", "")\
                            .replace("()", "").replace("(/)", "").replace("[/]", "")\
                            .replace("|", "").strip()
            item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
            item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality)
            item_local.quality = item_local.quality.replace("--", "").replace("[]", "")\
                            .replace("()", "").replace("(/)", "").replace("[/]", "")\
                            .replace("|", "").strip()
            
            if not size or 'Magnet' in size:
                item_local.alive = "??"                                         #Calidad del link sin verificar
            elif 'ERROR' in size and 'Pincha' in size:
                item_local.alive = "ok"                                         #link en error, CF challenge, Chrome disponible
            elif 'ERROR' in size and 'Introduce' in size:
                item_local.alive = "??"                                         #link en error, CF challenge, ruta de descarga no disponible
                item_local.channel = 'setting'
                item_local.action = 'setting_torrent'
                item_local.unify = False
                item_local.folder = False
                item_local.item_org = item.tourl()
            elif 'ERROR' in size:
                item_local.alive = "no"                                         #Calidad del link en error, CF challenge?
            else:
                item_local.alive = "ok"                                         #Calidad del link verificada
            if item_local.channel != 'setting':
                item_local.action = "play"                                      #Visualizar vídeo
                item_local.server = "torrent"                                   #Seridor Torrent
            
            itemlist_t.append(item_local.clone())                               #Pintar pantalla, si no se filtran idiomas
            
            # Requerido para FilterTools
            if config.get_setting('filter_languages', channel_py) > 0:          #Si hay idioma seleccionado, se filtra
                itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

            #logger.debug("TORRENT: " + scrapedurl + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
            #logger.debug(item_local)
        
    if not item.videolibray_emergency_urls:
        if len(itemlist_f) > 0:                                                 #Si hay entradas filtradas...
            itemlist.extend(itemlist_f)                                         #Pintamos pantalla filtrada
        else:                                                                       
            if config.get_setting('filter_languages', channel_py) > 0 and len(itemlist_t) > 0:  #Si no hay entradas filtradas ...
                thumb_separador = get_thumb("next.png")                         #... pintamos todo con aviso
                itemlist.append(Item(channel=item.channel, url=host, 
                            title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                            thumbnail=thumb_separador, folder=False))
            itemlist.extend(itemlist_t)                                         #Pintar pantalla con todo si no hay filtrado
    
    
    """ VER y DESCARGAR vídeos, descargar vídeos un link,  o múltiples links"""
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    
    if item.armagedon and matches and not enlaces_ver:                          #Si es un proceso normal, seguimos
        enlaces_ver = matches

    #Si es un lookup para cargar las urls de emergencia en la Videoteca, lo hacemos y nos vamos sin más
    if item.videolibray_emergency_urls:
        item.emergency_urls.append(enlaces_ver)
        item.emergency_urls.append(enlaces_descargar)
        return item

    if not enlaces_ver and not enlaces_descargar:
        # Requerido para AutoPlay
        autoplay.start(itemlist, item)                                          #Lanzamos Autoplay
        return itemlist

    """ Recorre todos los links de VER y DESCARGAR, si está permitido """
    idioma = str(item.language)
    if not idioma: idioma = ['CAST']
    for accion in ['ver', 'descarga']:
        ver_enlaces = 5
        cnt_enl_ver = 1
        cnt_enl_verif = 1
        verificar_enlaces_validos = True
        if accion == 'ver':
            enlaces = enlaces_ver[:]
        else:
            enlaces = enlaces_descargar[:]
        
        for enlace, servidor in enlaces:
            item_local = item.clone()
            servidor = servidor.replace("streamin", "streaminto").replace("uploaded", "uploadedto")
            partes = enlace.split(" ")                                          #Partimos el enlace en cada link de las partes
            if accion == 'descarga':
                title = "Descarga"                          #Usamos la palabra reservada de Unify para que no formatee el título
                servidor = scrapertools.find_single_match(servidor, '(^\w+)')
            else:
                title = servidor
            
            #Recorremos cada una de las partes.  Vemos si el primer link está activo.  Si no lo está ignoramos todo el enlace
            p = 1
            for enlace in partes:
                if accion == 'descarga':
                    if not item.unify:                                          #Si titles Inteligentes NO seleccionados:
                        title = "[COLOR yellow][%s][/COLOR] %s (%s/%s) [COLOR limegreen]" % \
                                (servidor.capitalize(), "Descarga", p, len(partes)) + \
                                "[%s][/COLOR] [COLOR red]%s[/COLOR]" % (item_local.quality, \
                                str(item_local.language))
                    else:
                        title = title.replace('Descarga', 'Descarg.')
                        item_local.quality = '[/COLOR][COLOR white] %s (%s/%s) [/COLOR][COLOR limegreen][%s] ' \
                                % ('Descarg.', p, len(partes), item.quality)
                        title = "[COLOR yellow][%s]%s[/COLOR] [COLOR red][%s][/COLOR]" % \
                                (servidor.capitalize(), item_local.quality, str(item_local.language))
            
                p += 1
                mostrar_server = True
                if config.get_setting("hidepremium"):                           #Si no se aceptan servidore premium, se ignoran
                    mostrar_server = servertools.is_server_enabled(servidor)
                    
                #logger.debug("VER: url: " + enlace + " / title: " + title + 
                #        " / servidor: " + servidor + " / idioma: " + idioma + 
                #        " / validadción: " + str(mostrar_server))
                
                #Si el servidor es válido, se comprueban si los links están activos
                if mostrar_server:
                    try:
                        if cnt_enl_ver <= ver_enlaces or ver_enlaces == -1:
                            devuelve = servertools.findvideosbyserver(enlace, servidor)         #existe el link ?
                            if ver_enlaces == 0:
                                cnt_enl_ver += 1
                        else:
                            ver_enlaces = 0                                     #FORZAR SALIR del loop
                            break                                               #Si se ha agotado el contador de verificación, se sale
                        
                        if devuelve:                                            #Hay link
                            enlace = devuelve[0][1]                             #Se guarda el link
                            
                            #Verifica si está activo el primer link.  Si no lo está se ignora el enlace-servidor entero
                            if p <= 2:
                                item_local.alive = "??"                         #Se asume por defecto que es link es dudoso
                                if ver_enlaces != 0:                            #Se quiere verificar si el link está activo?
                                    if cnt_enl_verif <= ver_enlaces or  ver_enlaces == -1:      #contador?
                                        #Llama a la subfunción de check_list_links(itemlist) para cada link de servidor
                                        item_local.alive = servertools.check_video_link(enlace, servidor, timeout=timeout)  #activo el link ?
                                        if verificar_enlaces_validos:           #Los links tienen que ser válidos para contarlos?
                                            if item_local.alive == "Ok":        #Sí
                                                cnt_enl_verif += 1              #Movemos los contadores
                                                cnt_enl_ver += 1                #Movemos los contadores
                                        else:                                   #Si no es necesario que sean links válidos, sumamos
                                            cnt_enl_verif += 1                  #Movemos los contadores
                                            cnt_enl_ver += 1                    #Movemos los contadores
                                    else:
                                        ver_enlaces = 0                         #FORZAR SALIR del loop
                                        break                                   #Si se ha agotado el contador de verificación, se sale

                            #Si el link no está activo se ignora
                            if accion == 'ver':
                                if "??" in item_local.alive:                    #dudoso
                                    item_local.title = '[COLOR yellow][?][/COLOR] [COLOR yellow]' + \
                                            '[%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' \
                                            % (servidor.capitalize(), item_local.quality, \
                                            str(item_local.language))
                                elif "no" in item_local.alive.lower():          #No está activo.  Lo preparo, pero no lo pinto
                                    item_local.title = '[COLOR red][%s][/COLOR] [COLOR yellow]' % item_local.alive + \
                                            '[%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' \
                                            % (servidor.capitalize(), item_local.quality, str(item_local.language))
                                    logger.debug(item_local.alive + ": ALIVE / " + title + 
                                            " / " + servidor + " / " + enlace)
                                    raise
                                else:                                           #Sí está activo
                                    item_local.title = '[COLOR yellow][%s][/COLOR] [COLOR limegreen]' % \
                                            servidor.capitalize() + '[%s][/COLOR] [COLOR red]%s[/COLOR]' % \
                                            (item_local.quality, str(item_local.language))
                            else:
                                if "??" in item_local.alive:                    #dudoso
                                    if not item.unify:                          #Si titles Inteligentes NO seleccionados:
                                        item_local.title = '[COLOR yellow][?][/COLOR] %s' % \
                                                (title)
                                    else:
                                        item_local.title = '[COLOR yellow]%s[/COLOR]-%s' % \
                                                (item_local.alive, title)
                                elif "no" in item_local.alive.lower():          #No está activo.  Lo preparo, pero no lo pinto
                                    if not item.unify:                          #Si titles Inteligentes NO seleccionados:
                                        item_local.title = '[COLOR red][%s][/COLOR] %s' % \
                                            (item_local.alive, title)
                                    else:
                                        item_local.title = '[COLOR red]%s[/COLOR]-%s' % \
                                            (item_local.alive, title)
                                    logger.debug(item_local.alive + ": ALIVE / " 
                                            + title + " / " + servidor + " / " + enlace)
                                    raise
                                else:                                           #Sí está activo
                                    item_local.title = title

                            #Preparamos el resto de variables de Item para ver los vídeos en directo    
                            item_local.action = "play"
                            item_local.server = servidor
                            item_local.url = enlace
                            
                            #Preparamos título y calidad, quitamos etiquetas vacías
                            item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', \
                                    '', item_local.title)    
                            item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', \
                                    '', item_local.title)
                            item_local.title = item_local.title.replace("--", "")\
                                    .replace("[]", "").replace("()", "").replace("(/)", "")\
                                    .replace("[/]", "").strip()
                            item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]'\
                                    , '', item_local.quality)
                            item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', \
                                    '', item_local.quality)
                            item_local.quality = item_local.quality.replace("--", "")\
                                    .replace("[]", "").replace("()", "").replace("(/)", "")\
                                    .replace("[/]", "").strip()
                            
                            itemlist_t.append(item_local.clone())               #Pintar pantalla, si no se filtran idiomas
                            
                            
                            # Requerido para FilterTools
                            if config.get_setting('filter_languages', channel_py) > 0:                      #Si hay idioma seleccionado, se filtra
                                itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)    #Pintar pantalla, si no está vacío

                    except:
                        logger.error('ERROR al procesar enlaces VER/DESCARGAS DIRECTOS: ' + 
                                    servidor + ' / ' + enlace)
                        break

    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel_py) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, title=\
                        "[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                        thumbnail=thumb_separador, folder=False))

        if len(itemlist_t) == 0:
            if len(itemlist) == 0 or (len(itemlist) > 0 and itemlist[-1].server != 'torrent'):
                return []
        itemlist.extend(itemlist_t)                                             #Pintar pantalla con todo si no hay filtrado

    # Requerido para AutoPlay
    #autoplay.start(itemlist, item)                                              #Lanzamos Autoplay
    
    return itemlist
    

def episodios(item):
    logger.info()
    
    itemlist = []
    
    #logger.debug(item)

    if item.from_title:
        item.title = item.from_title
    
    #Limpiamos num. Temporada y Episodio que ha podido quedar por Novedades
    season_display = 0
    if item.contentSeason:
        if item.season_colapse:                                                 #Si viene del menú de Temporadas...
            season_display = item.contentSeason                                 #... salvamos el num de sesión a pintar
            item.from_num_season_colapse = season_display
            del item.season_colapse
            item.contentType = "tvshow"
            if item.from_title_season_colapse:
                item.title = item.from_title_season_colapse
                del item.from_title_season_colapse
                if item.infoLabels['title']:
                    del item.infoLabels['title']
        del item.infoLabels['season']
    if item.contentEpisodeNumber:
        del item.infoLabels['episode']
    if season_display == 0 and item.from_num_season_colapse:
        season_display = item.from_num_season_colapse

    # Obtener la información actualizada de la Serie.  TMDB es imprescindible para Videoteca
    idioma = idioma_busqueda
    if 'VO' in str(item.language):
        idioma = idioma_busqueda_VO
    try:
        tmdb.set_infoLabels(item, True, idioma_busqueda=idioma)
    except:
        pass
        
    modo_ultima_temp_alt = modo_ultima_temp
    if item.ow_force == "1":                                                    #Si hay una migración de canal o url, se actualiza todo 
        modo_ultima_temp_alt = False
    
    # Vemos la última temporada de TMDB y del .nfo
    max_temp = 1
    max_temp_seen = 0
    num_temporadas_flag = False
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']                         # Salvamos el num. máximo de temporadas
        num_temporadas_flag = True
    y = []
    if modo_ultima_temp_alt and item.library_playcounts:                        # Salvamos el num. de última temporada que hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_temp = max(y)
        num_temporadas_flag = True
    season = max_temp                                                           # Salvamos el num. última temporada

    max_page = 100                                                              # Límite de páginas a visitar, la web da valores malos
    if item.library_playcounts: 
        max_page = old_div(max_page, 5)                                         # Si es una actualización, recortamos
    page = 1
    
    if item.post:
        if not isinstance(item.post, list):
            post = [item.post]
        else:
            post = item.post
        del item.post
    else:
        post = [None]
    list_pages = []
    if item.serie_info:
        list_pages = [urlparse.urljoin(host, '/controllers/load.chapters.type.php')]
        post = [item.serie_info]
    if not download_sufix in item.url:
        item.url = item.url.replace(sufix, sufix+download_sufix)
    if '///' in item.url:
        item.url = item.url.replace('///', '/temporada-1/capitulo-01/')
    
    if not list_pages: list_pages = [item.url]
    data = ''
    list_episodes = []
    first = True
    quality = item.quality
    url_quality_alt = {}

    """ Descarga las páginas """
    while list_pages and page < max_page:                                       # Recorre la lista de páginas, con límite
        patron = 'onClick="modCap\((\d+)\)">([^<]+)<'
        
        if not data:
            data, success, code, item, itemlist = generictools.downloadpage(list_pages[0], timeout=timeout, 
                                          decode_code=decode_code, quote_rep=True, no_comments=False, post=post[0], 
                                          item=item, itemlist=itemlist)         # Descargamos la página
            del list_pages[0]
            if post:
                if post[0]:
                    if '_cidr=7263' in post[0]:
                        quality = '4KWebrip'
                    elif '_cidr=7264' in post[0]:
                        quality = 'Bluray 1080p'
                del post[0]

        #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
        if 'Descargar (0) Capitulos' in data:
            data = ''
            continue
        
        if not success or not data or not scrapertools.find_single_match(data, patron):
            if len(itemlist) > 0:
                break

        if first and not item.serie_info:
            try:
                patron_serie_info = '<script\s*type="text\/javascript">var\s*CNAME\s*=\s*"([^"]+)"\s*,\s*'
                patron_serie_info += 'CID\s*=\s*"([^"]+)"\s*,\s*CIDR\s*=\s*"([^"]+)"\s*;\s*<\/script>'
                item.serie_info = '_cname=%s&_cid=%s&_cidr=%s' % scrapertools.find_single_match(data, patron_serie_info)
                if item.quality == 'HDTV':
                    item.serie_info = item.serie_info.replace('_cidr=1469', '_cidr=767')
                if '_cidr=1469' in item.serie_info:
                    item.serie_info += '&_o=0'
                elif '_cidr=767' in item.serie_info:
                    item.serie_info += '&_o=1'
                elif '_cidr=7263' in item.serie_info:
                    item.serie_info += '&_o=2'
                elif '_cidr=7264' in item.serie_info:
                    item.serie_info += '&_o=3'
                else:
                    item.serie_info += '&_o=4'
            except:
                logger.error('ERROR en formato de SERIES: %s' % data)
                item.serie_info = '_cname=&_cid=&_cidr=&_o=0'

        if first and '_cidr=1469' in item.serie_info:
            list_pages += [urlparse.urljoin(host, '/controllers/load.chapters.type.php')]
            post += [item.serie_info.replace('_cidr=1469', '_cidr=7263').replace('&_o=0', '&_o=2')]
            list_pages += [urlparse.urljoin(host, '/controllers/load.chapters.type.php')]
            post += [item.serie_info.replace('_cidr=1469', '_cidr=7264').replace('&_o=0', '&_o=3')]
        
        url = urlparse.urljoin(host, '/controllers/show.chapters.php')
        
        matches = re.compile(patron, re.DOTALL).findall(data)
        
        if not matches and 'Descargar (0) Capitulos' not in data and not scrapertools.find_single_match(data, patron_serie_info):   #error
            logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " 
                    + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.category + 
                    ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  ' 
                    + 'Reportar el error con el log', contentSeason=0, contentEpisodeNumber=1))
            return itemlist                                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(list_pages)
        #logger.debug(data)
        
        page += 1                                                               # Apuntamos a la página siguiente

        """ Recorremos todos los episodios generando un Item local por cada uno en Itemlist """
        x = 0
        for scrapedurl, info in matches:
            item_local = item.clone()
            item_local.action = "findvideos"
            item_local.contentType = "episode"
            item_local.extra = "episodios"
            if item_local.library_playcounts:
                del item_local.library_playcounts
            if item_local.library_urls:
                del item_local.library_urls
            if item_local.path:
                del item_local.path
            if item_local.update_last:
                del item_local.update_last
            if item_local.update_next:
                del item_local.update_next
            if item_local.active:
                del item_local.active
            if item_local.contentTitle:
                del item_local.infoLabels['title']
            if item_local.season_colapse:
                del item_local.season_colapse

            item_local.url = url
            item_local.post = 'id=%s' % scrapedurl
            item_local.context = "['buscar_trailer']"
            
            patron_quality = '(?i)\[([^\]]*)\]\s*\[cap'
            quality_temp = scrapertools.find_single_match(info, patron_quality).replace('hdtv', 'HDTV')
            if '720p' in quality_temp or '1080p' in quality_temp:
                item_local.quality = quality_temp
            
            x += 1

            """ Localizamos el patrón correcto """
            patron = '[c|C]ap\.(\d+)'
            patron_al = '[c|C]ap\.\d+_(\d+)'
            temp_epi = scrapertools.find_single_match(info, patron)
            temp_epi_al = scrapertools.find_single_match(info, patron_al)
            item_local.contentSeason = 1
            item_local.contentEpisodeNumber = 1

            try:
                if len(temp_epi) > 3:
                    item_local.contentSeason = int(scrapertools.find_single_match(temp_epi, '^(\d{2})'))
                    item_local.contentEpisodeNumber = int(scrapertools.find_single_match(temp_epi, '^\d{2}(\d{2})'))
                    if temp_epi_al:
                        temp_epi_al = int(scrapertools.find_single_match(temp_epi_al, '^\d{2}(\d{2})'))
                else:
                    item_local.contentSeason = int(scrapertools.find_single_match(temp_epi, '^(\d{1})'))
                    item_local.contentEpisodeNumber = int(scrapertools.find_single_match(temp_epi, '^\d{1}(\d{2})'))
                    if temp_epi_al:
                        temp_epi_al = int(scrapertools.find_single_match(temp_epi_al, '^\d{1}(\d{2})'))
            except:
                logger.error('Episodio en error: %s' % info)

            if temp_epi_al:                                               #     Hay episodio dos? es una entrada múltiple?
                item_local.title = "%sx%s al %s -" % (str(item_local.contentSeason), \
                        str(item_local.contentEpisodeNumber).zfill(2), str(temp_epi_al)\
                        .zfill(2))                                              #Creamos un título con el rango de episodios
            else:                                                               #Si es un solo episodio, se formatea ya
                item_local.title = "%sx%s -" % (str(item_local.contentSeason), \
                        str(item_local.contentEpisodeNumber).zfill(2))

            if first:                                                           #Si es el primer episodio, comprobamos que ...
                first = False
                if item_local.contentSeason < max_temp:                         #... la temporada sea la última ...
                    modo_ultima_temp_alt = False                                #... si no, por seguridad leeremos toda la serie
            
            if modo_ultima_temp_alt and item.library_playcounts:                #Si solo se actualiza la última temporada de Videoteca
                if item_local.contentSeason < max_temp and modo_ultima_temp_alt and max_temp_seen > 1:
                    #list_pages = []                                             #Sale del bucle de leer páginas
                    continue                                                       #Sale del bucle actual del FOR de episodios por página
                elif item_local.contentSeason < max_temp:                       #Si está desordenada ...
                    modo_ultima_temp_alt = False                                #... por seguridad leeremos toda la serie
              
            if season_display > 0:
                if item_local.contentSeason > season_display or (not modo_ultima_temp_alt \
                            and item_local.contentSeason != season_display):
                    continue
                elif item_local.contentSeason < season_display and max_temp_seen > 1:
                    #list_pages = []                                             #Sale del bucle de leer páginas
                    continue
                elif item_local.contentSeason < season_display:                 #Si no ha encontrado epis de la temp, sigue
                    continue

            #logger.debug('quality: %s - item_local.quality: %s' % (quality, item_local.quality))
            if item_local.title not in str(list_episodes):
                if item_local.quality in item.quality:
                    list_episodes += [item_local.title]
                    
                    item_local.quality = item.quality
                    quality = item.quality
                    itemlist.append(item_local.clone())
            if quality not in item.quality or item_local.quality not in item.quality:
                quality_temp = quality
                if quality == item.quality:
                    if 'web' in item_local.quality:
                        quality_temp = '4KWebrip'
                    elif '1080' in item_local.quality:
                        quality_temp = 'Bluray 1080p'
                    else:
                        quality_temp = item_local.quality
                if not url_quality_alt.get(item_local.title, ''):
                    url_quality_alt[item_local.title] = [(item_local.post, quality_temp)]
                else:
                    url_quality_alt[item_local.title].append((item_local.post, quality_temp))
                continue
            
            max_temp_seen += 1

            #logger.debug(item_local)
            
        data = '' 

    try:
        if len(itemlist) > 1:
            itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))       #clasificamos
    except:
        logger.error(traceback.format_exc(1))
    
    for item_local in itemlist:                                                 # Salvamos las urls de calidades alternativas
        if url_quality_alt.get(item_local.title, ''):
            item_local.url_quality_alt = url_quality_alt[item_local.title]
    
    if item.season_colapse and not item.add_videolibrary:                       #Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)

    if not item.season_colapse:                                                 #Si no es pantalla de Temporadas, pintamos todo
        # Pasada por TMDB y clasificación de lista por temporada y episodio
        tmdb.set_infoLabels(itemlist, True, idioma_busqueda=idioma)

        #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    #logger.debug(item)

    return itemlist


def actualizar_titulos(item):
    logger.info()
    
    #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    item = generictools.update_title(item)
    
    #Volvemos a la siguiente acción en el canal
    return item

    
def search(item, texto):
    logger.info("search: " + texto)
    texto = texto.replace(" ", "+")

    try:
        item.url = host + "controllers/search-mini.php"
        item.post = "s=%s" % texto
        #item.url = host + "search"
        #item.post = "searchq=%s" % texto
        item.extra = "search"
        itemlist = listado(item)
        
        return itemlist

    # Se captura la excepción, para no interrumpir al buscador global si un canal falla
    except:
        import sys
        logger.error(traceback.format_exc())
        for line in sys.exc_info():
            logger.error("%s" % line)
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    
    item.title = "newest"
    item.category_new= 'newest'
    item.channel = channel_py
    
    try:
        if categoria == 'peliculas':
            item.url = host + '/descargar-peliculas/estrenos-de-cine/'
            item.extra = "novedades"
            item.action = "listado"
            itemlist = listado(item)
                
        elif categoria == 'series':
            item.url = host + 'descargar-series/'
            item.extra = "novedades"
            item.action = "listado"
            itemlist = listado(item)
                
        elif categoria == '4k':
            item.url = host + 'descargar-peliculas/hd/'
            item.extra = "novedades"
            item.extra2 = "4k"
            item.action = "listado"
            itemlist = listado(item)
                
        elif categoria == 'latino':
            item.url = host + 'descargar-peliculas/latino/'
            item.extra = "novedades"
            item.action = "listado"
            itemlist = listado(item)
            
        elif categoria == 'torrent':
            item.url = host + 'descargar-lo-ultimo'
            item.extra = "novedades"
            item.action = "listado"
            itemlist.extend(listado(item))
            
        if len(itemlist) > 0 and (">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title):
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        logger.error(traceback.format_exc())
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist