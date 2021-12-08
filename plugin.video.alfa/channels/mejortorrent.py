# -*- coding: utf-8 -*-

import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

if PY3:
    import urllib.parse as urlparse                                             # Es muy lento en PY2.  En PY3 es nativo
    import urllib.parse as urllib
else:
    import urlparse                                                             # Usamos el nativo de PY2 que es más rápido
    import urllib

import re
import time
import traceback

from channelselector import get_thumb
from core import httptools
from core import scrapertools
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

host_list = ['https://www.mejortorrentes.net/', 'https://mejortorrent.one/']
channel = 'mejortorrent'
categoria = channel.capitalize()
host_index = config.get_setting('choose_domain', channel)
host = host_list[host_index]
host_emergency = False
domain_alt = host_list[1][-6:]
host_torrent = host[:-1]
movies_sufix = ''
series_sufix = ''

__modo_grafico__ = config.get_setting('modo_grafico', channel)                  # búsqueda TMDB ?
IDIOMAS_TMDB = {0: 'es', 1: 'en', 2: 'es,en'}
idioma_busqueda = IDIOMAS_TMDB[config.get_setting('modo_grafico_lang', channel)]    # Idioma base para TMDB
idioma_busqueda_VO = IDIOMAS_TMDB[2]                                                # Idioma para VO
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel)     # Actualización sólo últ. Temporada?
timeout = config.get_setting('timeout_downloadpage', channel)
season_colapse = config.get_setting('season_colapse', channel)                  # Season colapse?
filter_languages = config.get_setting('filter_languages', channel)              # Filtrado de idiomas?


def mainlist(item):
    logger.info()
    itemlist = []
    adjust_alternate_domain('', reset=True)                                     # Resetear dominio alternativo
    
    thumb_cartelera = get_thumb("now_playing.png")
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_documentales = get_thumb("channels_documentary.png")
    
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")
    
    autoplay.init(item.channel, list_servers, list_quality)

    itemlist.append(Item(channel=item.channel, title="Novedades", action="novedades_menu", 
                url=host, thumbnail=thumb_cartelera, extra2="novedades", category=categoria))
    itemlist.append(Item(channel=item.channel, title="Películas", action="submenu", 
                url=host, thumbnail=thumb_pelis, extra="peliculas", category=categoria))
    itemlist.append(Item(channel=item.channel, title="Series", action="submenu", 
                url=host, thumbnail=thumb_series, extra="series", category=categoria))
    itemlist.append(Item(channel=item.channel, title="Documentales", action="submenu", 
                url=host, thumbnail=thumb_documentales, extra="documentales", category=categoria))

    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search",
                url=host, thumbnail=thumb_buscar, extra="search", category=categoria))

    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", 
                folder=False, thumbnail=thumb_separador))
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", 
                thumbnail=thumb_settings))
    
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
    adjust_alternate_domain(item)
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_hd = get_thumb("channels_tvshow_hd.png")
    
    thumb_documentales = get_thumb("channels_documentary.png")

    patron = 'class="bloqtitulo"[^>]*>\s*<span[^>]*>Torrents<\/span>\s*(?:<\/td><\/tr><\/table>)?(.*?)<\/table>'
    data, success, code, item, itemlist = generictools.downloadpage(item.url, timeout=timeout/2, 
                                          patron=patron, item=item, itemlist=[])    # Descargamos la página

    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not success or itemlist:                                                 # Si ERROR o lista de errores lo reintentamos con otro Host
        item.url, data, success, code, item, itemlist = choose_alternate_domain(item, \
                                        url=item.url, code=code, patron=patron, itemlist=[])
        if not success or itemlist:                                             # Si ERROR o lista de errores ...
            return itemlist                                                     # ... Salimos
    
    # Seleccionamos el bloque y buscamos los apartados
    data = scrapertools.find_single_match(data, patron)
    patron = '(?i)<tr>\s*<td>\s*<a\s*href="([^"]+)"[^>]+>(?:<b>)?\s*(.*?)(?:<\/b>)?<\/a>\s*<\/td>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    #logger.debug(patron)
    #logger.debug(matches)
    #logger.debug(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                        " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  '
                        + 'Reportar el error con el log'))
        return itemlist                                             # si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    for scrapedurl, scrapedtitle in matches:
        if item.extra not in scrapedurl:                                        # Seleccionamos las categorias del apartado
            continue

        if 'culas HD' in scrapedtitle: thumb = thumb_pelis_hd
        elif 'culas' in scrapedtitle: thumb = thumb_pelis
        elif 'Series HD' in scrapedtitle: thumb = thumb_series_hd
        elif 'Series' in scrapedtitle: thumb = thumb_series
        else: thumb = thumb_documentales
        
        itemlist.append(Item(channel=item.channel, title=scrapedtitle, action="listado", extra=item.extra, 
                             url=urlparse.urljoin(host, scrapedurl), thumbnail=thumb))
        itemlist.append(Item(channel=item.channel, title=scrapedtitle + ' [A-Z]', action="alfabeto", extra=item.extra, 
                             url=urlparse.urljoin(host, scrapedurl.replace('peliculas-hd-alta-definicion', 'peliculas')), 
                             referer=urlparse.urljoin(host, scrapedurl), thumbnail=thumb))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []
    adjust_alternate_domain(item)
    
    data, success, code, item, itemlist = generictools.downloadpage(item.url, timeout=timeout, 
                                          item=item, itemlist=[])               # Descargamos la página

    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not success or itemlist:                                                 # Si ERROR o lista de errores ...
        return itemlist                                                         # ... Salimos
        
    patron = '(?i)squeda\s*de.*?culas\s*\:.*?<form\s*name="filtro"\s*action="([^"]+)"()'
    if not scrapertools.find_single_match(data, patron):
        patron = '(?i)<a\s*href="([^"]+)"\s*title="Mostrar[^>]+>(.*?)<\/a>'
    
    matches = re.compile(patron, re.DOTALL).findall(data)
    
    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + 
                        " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  '
                        + 'Reportar el error con el log'))
        return itemlist                                             # si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug(patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    if len(matches) > 1:
        for scrapedurl, scrapedtitle in matches:
            itemlist.append(item.clone(action="listado", title=scrapedtitle.upper(), 
                            url=urlparse.urljoin(host, scrapedurl), extra2='alfabeto'))
    else:
        post = 'campo=letra&valor=&valor2=&valor3=%s&valor4=3&submit=Buscar'
        for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', \
                      'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
            itemlist.append(item.clone(action="listado", title=letra, url=urlparse.urljoin(host, matches[0][0]), 
                        extra2='alfabeto', post=post % letra))

    return itemlist
    
    
def novedades_menu(item):
    logger.info()
    itemlist = []
    adjust_alternate_domain(item)

    patron = '(?i)<a href=\s*"([^"]+)"\s*class=\s*"menu_cabecera"\s*>[^>]+ltimos[^<]*<\/a>'
    data, success, code, item, itemlist = generictools.downloadpage(item.url, timeout=timeout/2, 
                                          patron=patron, item=item, itemlist=[])    # Descargamos la página

    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not success or itemlist:                                                 # Si ERROR o lista de errores lo reintentamos con otro Host
        item.url, data, success, code, item, itemlist = choose_alternate_domain(item, \
                                        url=item.url, code=code, patron=patron, itemlist=[])
        if not success or itemlist:                                             # Si ERROR o lista de errores ...
            return itemlist                                                     # ... Salimos
    
    item.action = 'listado'
    item.url = urlparse.urljoin(host, scrapertools.find_single_match(data, patron))
    
    return listado(item)
    

def listado(item):                                                              # Listado principal y de búsquedas
    logger.info()
    
    itemlist = []
    adjust_alternate_domain(item)

    #logger.debug(item)

    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    last_page_print = 1                                                         # Última página inicial, para píe de página
    page_factor = 1.0                                                           # Factor de conversión de pag. web a pag. Alfa
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    if item.page_factor:
        page_factor = float(item.page_factor)                                   # Si viene de una pasada anterior, lo usamos
        del item.page_factor                                                    # ... y lo borramos
    if item.last_page_print:
        last_page_print = item.last_page_print                                  # Si viene de una pasada anterior, lo usamos
        del item.last_page_print                                                # ... y lo borramos
    
    cnt_tot = 30                                                                # Poner el num. máximo de items por página
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    if item.cnt_tot_match:
        cnt_tot_match = float(item.cnt_tot_match)                               # restauramos el contador TOTAL de líneas procesadas de matches
        del item.cnt_tot_match
    else:
        cnt_tot_match = 0.0                                                     # Contador TOTAL de líneas procesadas de matches
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
    
    if item.chapter:                                                            # Tipo de vídeo en búsquedas, novedades, alfabeto
        chapter = item.chapter
        del item.chapter
    else:
        chapter = ''
        
    post = None
    if item.post:                                                               # Rescatamos el Post, si lo hay
        post = item.post
    referer = None
    if item.referer:                                                            # Rescatamos el Referer, si lo hay
        referer = item.referer
    headers = None
    if item.headers:                                                            # Rescatamos el Headers, si lo hay
        headers = item.headers
    
    next_page_url = item.url
    #Máximo num. de líneas permitidas por TMDB. Máx de 5 segundos por Itemlist para no degradar el rendimiento
    while (cnt_title < cnt_tot and curr_page <= last_page and fin > time.time()) or item.matches:
    
        # Descarga la página
        data = ''
        cnt_match = 0                                                           # Contador de líneas procesadas de matches
        if not item.matches:                                                    # si no viene de una pasada anterior, descargamos
            data, success, code, item, itemlist = generictools.downloadpage(next_page_url, headers=headers, 
                                          timeout=timeout_search, post=post, referer=referer, s2=False, 
                                          item=item, itemlist=itemlist)         # Descargamos la página)
            
            curr_page += 1                                                      # Apunto ya a la página siguiente
            if not data:                                                        # Si la web está caída salimos sin dar error
                if len(itemlist) > 1:                                           # Si hay algo que pintar lo pintamos
                    last_page = 0
                    break
                return itemlist                                                 # Si no hay nada más, salimos directamente

        #Patrón para búsquedas, pelis y series
        if item.extra == 'search':                                              # Búsquedas...
            patron = '()<td>\s*<a\s*href="([^"]+)"()[^>]+>([^<]+)\.*<\/a>\s*<span[^>]+>'
            patron += '\s*\((.*?)\)\s*<\/a>\s*<\/td>\s*<td[^>]+>\s*([^<]+)<\/td>'
            if not scrapertools.find_single_match(data, patron):
                patron = '()<td>\s*<a\s*href="([^"]+)"()[^>]+>\s*(?:<font[^>]+>)?'
                patron += '\s*([^.]+)\.*<\/a>\s*(?:<span[^>]+>\s*\((.*?)\)\s*'
                patron += '(?:<\/span>|<\/a>))?\s*<\/td>\s*<td[^>]+>\s*([^<]+)<\/td>'
        elif item.extra2 == 'alfabeto':                                         # Alfabeto
            patron = '()<td>\s*<a\s*href="([^"]+)"()\s*(?:title=[^>]+)?>(.*?)\.*<\/a>()()'
        elif item.extra2 == 'novedades':                                        # Novedades
            patron = '(?:<div\s*style=[^>]+>([^<]+)<\/div>\s*(?:<[^>]*>)?\s*)?'
            patron += '<span\s*style=[^>]+>[^<]+<\/span>\s*<a\s*href=\s*"([^"]+)"()'
            patron += '[^>]+>\s*(.*?)\.*<\/a>\s*(?:<span\s*style=[^>]+>[\(|\[]*(.*?)'
            patron += '[\)|\]]*<\/span>)?()'
        else:                                                                   # Películas o Series o Documentales, menú
            patron = '()(?:<br>|;">)\s*<a\s*href="([^"]+)"\s*>()\s*(.*?)\.*\s*<\/a>'
            patron += '(?:\s*<b>\(*\s*(.*?)\)*<\/b>)?()'

        if not item.matches:                                                    # De pasada anterior o desde Novedades?
            matches = re.compile(patron, re.DOTALL).findall(data)
        else:
            matches = item.matches
            del item.matches
            
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)

        if not matches and item.extra != 'search':                              # error o fin
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " 
                        + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + 
                        ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  ' 
                        + 'Reportar el error con el log'))
            last_page = 0
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        if not matches and item.extra == 'search':                              # búsqueda vacía
            if len(itemlist) > 0:                                               # Si hay algo que pintar lo pintamos
                last_page = 0
                break
            return itemlist                                                     # Salimos
        
        #Buscamos la última página
        if last_page == 99999:                                                  # Si es el valor inicial, buscamos
            patron_page = '<a\s*class="paginar"\s*href="[^"]+\/page\/(\d+)\/"\s*>&raquo;<\/a>\s*&nbsp;'
            if item.extra == 'search' or item.extra2 == 'novedades' or item.extra2 == 'alfabeto':
                last_page_print = int((float(len(matches)) / float(cnt_tot)) + 0.999999999)
                last_page = 1
            elif scrapertools.find_single_match(data, patron_page):
                try:
                    last_page = int(scrapertools.find_single_match(data, patron_page))
                except:
                    last_page = 50
                last_page_print = int((last_page * (float(len(matches)) / float(cnt_tot))) + 0.999999999)
                page_factor = float(last_page_print) / float(last_page)
                next_page_url = next_page_url + 'page/%s/' % curr_page
            else:
                patron_page = '<a\s*href="([^"]+)"\s*class="paginar"\s*>\d+<\/a>\s*&nbsp;'
                if item.extra == 'documentales':
                    last_page = 5
                else:
                    last_page = 50
                last_page_print = int((last_page * (float(len(matches)) / float(cnt_tot))) + 0.999999999)
                page_factor = float(last_page_print) / float(last_page)
                next_page_url = urlparse.urljoin(host, scrapertools.find_single_match(data, patron_page))
            #logger.debug('curr_page: ' + str(curr_page) + ' / last_page: ' + str(last_page) + ' / page_factor: ' + str(page_factor))
        
        #Marcamos la próxima página
        if '&p=' in  next_page_url:
            next_page_url = re.sub(r'&p=\d+', '&p=%s' % str(curr_page), next_page_url)
        elif '/page/' in  next_page_url:
            next_page_url = re.sub(r'\/page\/\d+\/', '/page/%s/' % str(curr_page), next_page_url)
        #logger.debug('curr_page: ' + str(curr_page) + ' / last_page: ' + str(last_page) + ' / last_page_print: ' + str(last_page_print))        
        
        #Empezamos el procesado de matches
        for _chapter, scrapedurl, _scrapedthumbnail, scrapedtitle, scrapedquality, _chapter2 in matches:
            cnt_match += 1
            
            chapter_alt = _chapter
            if _chapter2 and not _chapter: chapter_alt = _chapter2
            if chapter_alt: chapter = scrapertools.slugify(chapter_alt).lower()
            title = scrapertools.remove_htmltags(scrapedtitle).rstrip('.')      # Removemos Tags del título
            url = scrapedurl.replace(' ', '%20').replace('&amp;', '&')
            scrapedthumbnail = scrapertools.find_single_match(data, scrapedurl + \
                        '"[^>]*><img src="([^"]+)"').replace(' ', '%20').replace('&amp;', '&')

            title_subs = []                                                     # creamos una lista para guardar info importante
            
            # Slugify, pero más light
            title = title.replace("á", "a").replace("é", "e").replace("í", "i")\
                    .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                    .replace("ï¿½", "ñ").replace("Ã±", "ñ")
            title = scrapertools.decode_utf8_error(title)

            # Ignoramos los tipos de vídeos que no correspondan con las categorías gestionadas
            if (item.extra == 'search' or item.extra2 == 'novedades') and 'pelicula' \
                            not in chapter and 'serie' not in chapter and 'documental' \
                            not in chapter and 'capitulo' not in chapter :
                continue
            if item.extra == 'search' and item.extra2 == 'episodios' and 'serie' \
                            not in chapter and 'documental' not in chapter:
                continue
            
            # Salvo que venga la llamada desde Episodios, se filtran las entradas para evitar duplicados de Temporadas
            url_list = url
            if not (item.extra == 'search' and item.extra2 == 'episodios'):
                if scrapertools.find_single_match(url_list, '-torrents-\d+-\d+-'):
                    url_list = re.sub('-torrents-\d+-\d+-', '-torrents-', url)
                else:
                    url_list = re.sub('\/\d+\/\d+\/', '/', url)
                url_list = re.sub('(?i)-(\d+)-Temporada(?:-\D|-\.|\.)?', '-X-Temporada', url_list)
                url_list_alt = re.sub('(?i)-temporada-\d+', '', url_list)
                if url_list_alt in str(title_lista):                            # Si ya hemos procesado el título, lo ignoramos
                    continue
                else:
                    title_lista += [url_list_alt]                               # la añadimos a la lista de títulos
            
            cnt_title += 1                                                      # Incrementamos el contador de entradas válidas
            item_local = item.clone()                                           # Creamos copia de Item para trabajar
            if item_local.tipo:                                                 #... y limpiamos
                del item_local.tipo
            if item_local.totalItems:
                del item_local.totalItems
            if item_local.intervencion:
                del item_local.intervencion
            if item_local.viewmode:
                del item_local.viewmode
            if item_local.matches:
                del item_local.matches
            if item_local.post or item_local.post is None:
                del item_local.post
            if item_local.headers or item_local.headers is None:
                del item_local.headers
            if item_local.referer or item_local.referer is None:
                del item_local.referer
            item_local.extra2 = True
            del item_local.extra2
            item_local.text_bold = True
            del item_local.text_bold
            item_local.text_color = True
            del item_local.text_color

            # Después de un Search se restablecen las categorías
            if item_local.extra == 'search' or item.extra2 == 'novedades':
                if 'pelicula' in url or 'pelicula' in chapter:
                    if item.extra2 == 'novedades' and item_local.extra and item_local.extra != 'peliculas':  # Se filtra se de Menú de movedades
                        continue
                    item_local.extra = 'peliculas'                              # Película búsqueda, novedades
                elif 'serie' in url or 'serie' in chapter or 'capitulo' in chapter:
                    if item.extra2 == 'novedades' and item_local.extra and item_local.extra != 'series':  # Se filtra se de Menú de movedades
                        continue
                    item_local.extra = 'series'                                 # Serie búsqueda, novedades
                else:
                    if item.extra2 == 'novedades' and item_local.extra and item_local.extra != 'documentales':  # Se filtra se de Menú de movedades
                        continue
                    item_local.extra = 'documentales'                           # Documental búsqueda, novedades
            
            # Guardamos los formatos para películas
            if item_local.extra == 'peliculas':
                item_local.contentType = "movie"
                item_local.action = "findvideos"

            # Guardamos los formatos para series y documentales
            elif item_local.extra == 'series' or item_local.extra == 'documentales':
                item_local.contentType = "tvshow"
                item_local.action = "episodios"
                item_local.season_colapse = season_colapse                      # Muestra las series agrupadas por temporadas?
                
            # Procesamos idiomas
            item_local.language = []                                            # creamos lista para los idiomas
            if '[Subs. integrados]' in title or '(Sub Forzados)' in title \
                        or 'Subs integrados' in title or "[vos" in title.lower() \
                        or "(vos" in title.lower()or "v.o.s" in title.lower():
                title = re.sub(r'(?i)[\[|\(]?Sub.*\.*\s*[int|for]\w+[\]|\)]?|[\[|\(]?v\.*o\.*s\.*(?:e\.*)?[\]|\)]?', '', title)
                item_local.language = ['VOS']                                   # añadimos VOS
            if '[Dual' in title:
                title = re.sub(r'(?i)\[*dual.*?\]*', '', title)
                item_local.language += ['DUAL']                                 # añadimos DUAL
            if not item_local.language:
                item_local.language = ['CAST']                                  # [CAST] por defecto
                
            # Procesamos Calidad
            patron_quality = '(?i)[\[|\(](.*?)[\)|\]]'
            if scrapedquality:
                item_local.quality = scrapertools.remove_htmltags(scrapedquality)   # iniciamos calidad
            if item_local.contentType == "tvshow":
                if '720p' in title or '720p' in scrapedquality:
                    item_local.quality = 'HDTV-720p'
                    if not item.extra2 == 'novedades' and not 'hd' in item.url.lower() and item.extra not in ['search', 'documentales']: continue
                elif '1080p' in title or '1080p' in scrapedquality:
                    item_local.quality = '1080p'
                    if not item.extra2 == 'novedades' and not 'hd' in item.url.lower() and item.extra not in ['search', 'documentales']: continue
                else:
                    item_local.quality = 'HDTV'
                    if not item.extra2 == 'novedades' and 'hd' in item.url.lower() and item.extra not in ['search', 'documentales']: continue
            elif scrapedquality:
                item_local.quality = scrapedquality
            elif not scrapedquality:
                item_local.quality = 'HDRip'
                if scrapertools.find_single_match(title, patron_quality):
                    item_local.quality = scrapertools.find_single_match(title, patron_quality)
            if '4k' in title.lower() and not '4k' in item_local.quality.lower():
                item_local.quality += ', 4K'
            if '3d' in title.lower() and not '3d' in item_local.quality.lower():
                item_local.quality += ', 3D'
            if item_local.contentType == 'movie' and scrapertools.find_single_match(title, patron_quality):
                #patron_quality = '(?i)\[(.*?)\]'
                title = re.sub(patron_quality, '', title)
            title = re.sub(r'(?i)[\[|\(]?\d{3,4}p[\]|\)]?|[\[|\(]?(?:4k|3d)[\]|\)]?', '', title)
            
            item_local.thumbnail = urlparse.urljoin(host, scrapedthumbnail)

            item_local.url = urlparse.urljoin(host, url)                        # guardamos la url final
            item_local.context = "['buscar_trailer']"                           # ... y el contexto
            
            # Si es un episodio, construimos la url de la serie
            patron_epi = '(?i)[-|\s*](\d{1,2})(?:x|&#215;)(\d{1,2})(?:[-|\s*]al'
            patron_epi += '[-|\s*](?:\d{1,2}(?:x|&#215;))?(\d{1,2}))?'
            if item_local.contentType == 'tvshow' and domain_alt in host:
                url = ''
                url_list_alt = ''
                if scrapertools.find_single_match(item_local.url, patron_epi):
                    url_list_alt = re.sub(patron_epi, '', item_local.url)
                    season, epi, epi_al = scrapertools.find_single_match(item_local.url, patron_epi)
                    url = re.sub(patron_epi, '-temporada-%s' % season, item_local.url)
                elif item_local.extra == 'series' and not (item.extra == 'search' and item.extra2 == 'episodios'):
                    fin = inicio + 10                                           # Después de este tiempo pintamos (segundos)
                    url, success, code, item_local, itemlist = generictools.downloadpage(item_local.url, 
                                          timeout=timeout, item=item_local, itemlist=itemlist)       # Descargamos la página)
                    url = scrapertools.find_single_match(url, '<link\s*rel="canonical"\s*href="([^"]+)"')\
                                          .replace('-720p', '').replace('-1080p', '')
                    if url != item_local.url:
                        url_list_alt = re.sub('(?i)temporada-\d+', '', url)
                if url: item_local.url = urlparse.urljoin(host, url)            # guardamos la url final
                if url_list_alt and url_list_alt in str(title_lista):           # Si ya hemos procesado el título, lo ignoramos
                    continue
                else:
                    title_lista += [url_list_alt]                               # la añadimos a la lista de títulos
            if item_local.contentType == 'tvshow' and item.extra2 == 'novedades' \
                                and scrapertools.find_single_match(title, patron_epi):
                season, epi, epi_al = scrapertools.find_single_match(title, patron_epi)
                title = re.sub(patron_epi, '', title)
                if epi_al:
                    title_subs += ['Episodio %sx%s-al-%s' % (str(season), str(epi).zfill(2), str(epi_al).zfill(2))]  # Salvamos info de episodio
                else:
                    title_subs += ['Episodio %sx%s' % (str(season), str(epi).zfill(2))]     # Salvamos info de episodio
                title = scrapertools.find_single_match(title, '(?i)(^.*?)\s*(?:$|\(|\[|-|temp|(?:\&\#\s*)?\d+.*\s*temp)').strip()
            elif item_local.contentType == 'tvshow':
                title = scrapertools.find_single_match(title, '(?i)(^.*?)\s*(?:$|\(|\[|-|temp|(?:\&\#\s*)?\d+.*\s*temp)').strip()
                title = re.sub(patron_epi, '', title)
            
            #Limpiamos el título de la basura innecesaria
            title = re.sub(r'(?i)TV|Online|(4k-hdr)|(fullbluray)|4k| - 4k|(3d)|miniserie', '', title).strip()
            item_local.quality = re.sub(r'(?i)proper|unrated|directors|cut|repack|internal|real|extended|masted|docu|super|duper|amzn|uncensored|hulu', 
                        '', item_local.quality).strip()
            title = re.sub(r'[\(|\[]\s+[\)|\]]', '', title)
            title = title.replace('()', '').replace('[]', '').replace('[4K]', '').replace('(4K)', '').strip().lower().title()
            item_local.from_title = title.strip().lower().title()               # Guardamos esta etiqueta para posible desambiguación de título

            #Salvamos el título según el tipo de contenido
            if item_local.contentType == "movie":
                item_local.contentTitle = title
            else:
                item_local.contentSerieName = title.strip().lower().title()

            item_local.title = title.strip().lower().title()
            if not item_local.title: continue

            #Analizamos el año.  Si no está claro ponemos '-'
            item_local.infoLabels["year"] = '-'
            
            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs
                
            #Salvamos y borramos el número de temporadas porque TMDB a veces hace tonterias.  Lo pasamos como serie completa
            if item_local.contentSeason and (item_local.contentType == "season" \
                        or item_local.contentType == "tvshow"):
                item_local.contentSeason_save = item_local.contentSeason
                del item_local.infoLabels['season']

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale
            if filter_languages > 0:                                            # Si hay idioma seleccionado, se filtra
                itemlist = filtertools.get_link(itemlist, item_local, list_language)
            else:
                itemlist.append(item_local.clone())                             # Si no, pintar pantalla
            
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
        if last_page:
            if last_page > 1:
                last_page_print = int((last_page * page_factor) + 0.999999)
            title = '%s de %s' % (curr_page_print, last_page_print)
        else:
            title = '%s' % curr_page_print

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " 
                        + title, title_lista=title_lista, url=next_page_url, extra=item.extra, 
                        extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page), 
                        page_factor=str(page_factor), cnt_tot_match=str(cnt_tot_match), matches=matches, 
                        last_page_print=last_page_print, post=post, referer=referer, headers=headers, 
                        chapter=chapter))

    return itemlist

    
def findvideos(item):
    logger.info()

    adjust_alternate_domain(item)
    itemlist = []
    itemlist_t = []                                                             # Itemlist total de enlaces
    itemlist_f = []                                                             # Itemlist de enlaces filtrados
    matches = []
    data = ''
    code = 0
    post = None
    headers = None
    referer = None
    
    #logger.debug(item)
    
    if item.post or item.post is None:
        post = item.post
        del item.post
    if item.headers or item.headers is None:
        headers = item.headers
        del item.headers
    if item.referer or item.referer is None:
        referer = item.referer
        del item.referer

    #Bajamos los datos de las páginas
    if not item.matches:
        data, success, code, item, itemlist = generictools.downloadpage(item.url, timeout=timeout, post=post, headers=headers, 
                                          referer=referer, s2=False, item=item, itemlist=[])     # Descargamos la página)
    
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if (not data and not item.matches) or code == 999:
        if item.emergency_urls and not item.videolibray_emergency_urls:         # Hay urls de emergencia?
            if len(item.emergency_urls) > 1 and item.emergency_urls[1]:
                matches = item.emergency_urls[1]                                # Restauramos matches de vídeos
            elif len(item.emergency_urls) == 1 and item.emergency_urls[0]:
                matches = item.emergency_urls[0]                                # Restauramos matches de vídeos - OLD FORMAT
            item.armagedon = True                                               # Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 # Si es llamado desde creación de Videoteca...
                return item                                                     # Devolvemos el Item de la llamada
            else:
                return itemlist                                     # si no hay más datos, algo no funciona, pintamos lo que tenemos

    if item.contentType == 'movie':
        patron = '<a\s*href=\s*"((?:[^"]+)?secciones\.php\?sec\=descargas\&ap=contar&tabla=[^"]+)"'
        if not scrapertools.find_single_match(data, patron):
            patron = 'name="id_post"\s*>\s*<input\s*type="hidden"\s*value="([^"]+)"'
    else:
        patron = '<td><a\s*href="[^"]+"\s*onclick="post\("[^"]+"\,\s*\{u:\s*"([^"]*)"\}\);"'
        if not scrapertools.find_single_match(data, patron):
            patron = '<a\s*href="([^"]+)"[^>]*>Descargar<\/a>'
            if not scrapertools.find_single_match(data, patron):
                patron = '<td\s*><a\s*href="([^"]+)"[^>]*>[^<]*<\/a>\s*<\/td>'

    if not item.armagedon:
        if not item.matches:
            matches = re.compile(patron, re.DOTALL).findall(data)
        else:
            matches = item.matches
            del item.matches
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    if not matches:                                                             # error
        if item.videolibray_emergency_urls:                                     # Si es llamado desde creación de Videoteca...
            logger.error("ERROR 02: FINDVIDEOS: Ha cambiado la estructura de la Web " + 
                            " / PATRON: " + patron)
            return item                                                         # Devolvemos el Item de la llamada
        else:
            logger.error("ERROR 02: FINDVIDEOS: Ha cambiado la estructura de la Web " + 
                            " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.category + 
                        ': ERROR 02: FINDVIDEOS: Ha cambiado la estructura de la Web.  '
                        + 'Reportar el error con el log'))
            return itemlist                                     # si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    # Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls = []                                                # Iniciamos emergency_urls
        item.emergency_urls.append([])                                          # Reservamos el espacio para los .torrents locales
        matches_list = []                                                       # Convertimos matches-tuple a matches-list
        for tupla in matches:
            if isinstance(tupla, tuple):
                matches_list.append(list(tupla))
        if matches_list:
            item.emergency_urls.append(matches_list)                            # Salvamnos matches de los vídeos...  
        else:
            item.emergency_urls.append(matches)

    # Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    # Ahora tratamos los enlaces .torrent con las diferentes calidades
    for x, _scrapedurl in enumerate(matches):

        scrapedurl = generictools.convert_url_base64(_scrapedurl, host_torrent)
        # Si ha habido un cambio en la url, actualizados matches para emergency_urls
        if item.videolibray_emergency_urls and scrapedurl != _scrapedurl:
            item.emergency_urls[1][x] = scrapedurl

        scrapedtitle = ''
        scrapedpassword = ''
        referer = None
        post= None
        headers = None
        
        # Puede ser necesario baja otro nivel para encontrar la página
        if not 'magnet:' in scrapedurl and not '.torrent' in scrapedurl:
            patron_torrent = '(?i)>\s*Pincha[^<]*<a\s*href="([^"]+)"'
            data_torrent, success, code, item, itemlist = generictools.downloadpage(scrapedurl, timeout=timeout, 
                                              referer=referer, post=post, headers=headers, 
                                              s2=False, patron=patron_torrent, item=item, itemlist=itemlist)    # Descargamos la página)
                                              
            #logger.debug("PATRON: " + patron_torrent)
            #logger.debug(data_torrent)
            
            # Verificamos si se ha cargado una página, y si además tiene la estructura correcta
            if not data_torrent or code == 999:
                if item.emergency_urls and not item.videolibray_emergency_urls: # Hay urls de emergencia?
                    if len(item.emergency_urls) > 1 and item.emergency_urls[1]:
                        matches = item.emergency_urls[1]                        # Restauramos matches de vídeos
                    elif len(item.emergency_urls) == 1 and item.emergency_urls[0]:
                        matches = item.emergency_urls[0]                        # Restauramos matches de vídeos - OLD FORMAT
                    item.armagedon = True                                       # Marcamos la situación como catastrófica 
                else:
                    if item.videolibray_emergency_urls:                         # Si es llamado desde creación de Videoteca...
                        return item                                             # Devolvemos el Item de la llamada
                    else:
                        return itemlist                                 # si no hay más datos, algo no funciona, pintamos lo que tenemos
            
            # Obtenemos el enlace final
            scrapedurl = generictools.convert_url_base64(scrapertools.find_single_match(data_torrent, patron_torrent), host_torrent)

        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()
        if item_local.post or item_local.post is None:
            del item_local.post
        if item_local.headers or item_local.headers is None:
            del item_local.headers
        if item_local.referer or item_local.referer is None:
            del item_local.referer

        item_local.url = scrapedurl

        # Restauramos urls de emergencia si es necesario
        local_torr = ''
        if item.emergency_urls and not item.videolibray_emergency_urls:
            try:                                                                # Guardamos la url ALTERNATIVA
                if item.emergency_urls[0][0].startswith('http'):
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
        
        # Buscamos tamaño en el archivo .torrent
        if item_local.torrent_info:
            size = item_local.torrent_info
        else:
            size = ''
        if not size and not item.videolibray_emergency_urls:
            if not item.armagedon:
                # Buscamos el tamaño en el .torrent desde la web
                size = generictools.get_torrent_size(item_local.url, local_torr=local_torr, post=post, headers=headers, referer=referer)     
                if 'ERROR' in size and item.emergency_urls and not item.videolibray_emergency_urls:
                    item_local.armagedon = True
                    try:                                                        # Restauramos la url
                        if item.emergency_urls[0][0].startswith('http'):
                            item_local.url = generictools.convert_url_base64(item.emergency_urls[0][0], host_torrent)
                        else:
                            item_local.url = generictools.convert_url_base64(item.emergency_urls[0][0])
                            if not item.url.startswith('http'):
                                local_torr = filetools.join(config.get_videolibrary_path(), FOLDER, item_local.url)
                    except:
                        item_local.torrent_alt = ''
                        item.emergency_urls[0] = []
                    size = generictools.get_torrent_size(item_local.url, local_torr=local_torr, post=post, headers=headers, referer=referer)
        if size:
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
            item_local.torrent_info = '%s, ' % size                             # Agregamos size
        if item_local.url.startswith('magnet:'):
            item_local.torrent_info += ' Magnet'
        if item_local.torrent_info:
            item_local.torrent_info = item_local.torrent_info.strip().strip(',')
            item.torrent_info = item_local.torrent_info
            if not item.unify:
                item_local.torrent_info = '[%s]' % item_local.torrent_info
   
        # Guadamos la password del RAR
        password = scrapedpassword
        if item.contentType == 'movie':
            password = scrapedtitle
        # Si tiene contraseña, la guardamos y la pintamos
        if password or item.password:
            if not item.password: item.password = password
            item_local.password = item.password
            itemlist.append(item.clone(action="", title="[COLOR magenta][B] Contraseña: [/B][/COLOR]'" 
                        + item_local.password + "'", folder=False))
        
        # Guardamos urls de emergencia si se viene desde un Lookup de creación de Videoteca
        if item.videolibray_emergency_urls:
            item.emergency_urls[0].append(item_local.url)                       # guardamos la url y nos vamos
            continue
            
        if item_local.armagedon:
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
            item_local.alive = "??"                                             # Calidad del link sin verificar
        elif 'ERROR' in size and 'Pincha' in size:
            item_local.alive = "ok"                                             # link en error, CF challenge, Chrome disponible
        elif 'ERROR' in size and 'Introduce' in size:
            item_local.alive = "??"                                             # link en error, CF challenge, ruta de descarga no disponible
            item_local.channel = 'setting'
            item_local.action = 'setting_torrent'
            item_local.unify = False
            item_local.folder = False
            item_local.item_org = item.tourl()
        elif 'ERROR' in size:
            item_local.alive = "no"                                             # Calidad del link en error, CF challenge?
        else:
            item_local.alive = "ok"                                             # Calidad del link verificada
        if item_local.channel != 'setting':
            item_local.action = "play"                                          # Visualizar vídeo
            item_local.server = "torrent"                                       # Seridor Torrent
        
        itemlist_t.append(item_local.clone())                                   # Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                 # Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  # Pintar pantalla, si no está vacío

        #logger.debug("TORRENT: " + scrapedurl + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
        #logger.debug(item_local)

    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        return item                                                             # ... nos vamos
    
    if len(itemlist_f) > 0:                                                     # Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             # Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             # ... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, 
                        title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", 
                        thumbnail=thumb_separador, folder=False))
        
        if len(itemlist_t) == 0:
            if len(itemlist) == 0 or (len(itemlist) > 0 and itemlist[-1].server != 'torrent'):
                return []
        itemlist.extend(itemlist_t)                                             # Pintar pantalla con todo si no hay filtrado
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                              # Lanzamos Autoplay
    
    return itemlist
    

def episodios(item):
    logger.info()
    
    itemlist = []
    search_seasons = True
    adjust_alternate_domain(item)
    
    #logger.debug(item)

    if item.from_title:
        item.title = item.from_title
    
    #Limpiamos num. Temporada y Episodio que ha podido quedar por Novedades
    season_display = 0
    if item.contentSeason:
        if item.season_colapse:                                                 # Si viene del menú de Temporadas...
            season_display = item.contentSeason                                 # ... salvamos el num de sesión a pintar
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
    max_nfo = 0
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']
    y = []
    if modo_ultima_temp_alt and item.library_playcounts:                        #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_nfo = max(y)

    # Si la series tiene solo una temporada, o se lista solo una temporada, guardamos la url y seguimos normalmente
    list_temps = []
    list_temp = []
    if season_display > 0 or max_temp == 1 or not item.infoLabels['tmdb_id']:
        list_temps.append(item.url)
        
    # Obtenemos todas las Temporada de la Serie desde Search
    # Si no hay TMDB o es sólo una temporada, listamos lo que tenemos
    if search_seasons and season_display == 0 and item.infoLabels['tmdb_id'] and max_temp > 1:
        # Si hay varias temporadas, buscamos todas las ocurrencias y las filtraos por TMDB y calidad
        list_temp = generictools.find_seasons(item, modo_ultima_temp_alt, max_temp, max_nfo)

    if not list_temp:
        list_temp = list_temps[:]                                               # Lista final de Temporadas a procesar

    # Descarga las páginas
    for url in list_temp:                                                       # Recorre todas las temporadas encontradas

        data, success, code, item, itemlist = generictools.downloadpage(url, timeout=timeout, s2=False, 
                                          item=item, itemlist=itemlist)         # Descargamos la página
        
        #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
        if not success:                                                         # Si ERROR o lista de errores ...
            if len(itemlist) > 1 or not 'timeout' in code:                      # puede ser un enlace erroneo de una temporada.  Siguiente...
                continue
            logger.error("ERROR 01: EPISODIOS: La Web no responde o ha cambiado de URL " + 
                            " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.category + 
                            ': ERROR 01: EPISODIOS: La Web no responde o ha cambiado de URL.  '
                            + 'Reportar el error con el log'))
            return itemlist                                                     # Si no hay nada más, salimos directamente
        
        #Datos para crear el Post.
        if domain_alt in url:
            try:
                id_value, id_name = scrapertools.find_single_match(data, '<input\s*type="hidden"\s*value="([^"]+)"\s*name="([^"]+)">')
                url_post = 'download_torrent.php'
            except:
                id_name = ''
                id_value = ''
                url_post = 'download_tv.php'
        else:
            url_post = 'secciones.php?sec=descargas&ap=contar_varios'
            total_capis = scrapertools.find_single_match(data, '<input\s*type="hidden"\s*name="total_capis"\s*value="(\d+)"[^>]*>')
            tabla = scrapertools.find_single_match(data, '<input\s*type="hidden"\s*name="tabla"\s*value="([^"]+)"[^>]*>')
            titulo_post = scrapertools.find_single_match(data, '<input\s*type="hidden"\s*name="titulo"\s*value="([^"]+)"[^>]*>')

        patron = '(?i)<td\s*bgcolor[^>]+>\s*(?:<a\s*href="([^"]+)"[^>]*>)?([^<]+)'      # Patron general
        patron += '(?:<\/a>)?\s*<\/td>\s*<td[^<]+(?:<div[^>]+>(?:Fecha.?)?\s*([^<]+)'
        patron += '<\/div>\s*)?<\/td>\s*<td[^<]+<input\s*type="checkbox"\s*name="([^"]+)"'
        patron += '\s*value="([^"]+)"'
        patron_epi = '(?i)(\d{1,2})(?:x|&#215;)(\d{1,2})(?:[-|\s*](?:al|-)[-|\s*]'      # Patron episodio
        patron_epi += '(?:\d{1,2}(?:x|&#215;))?(\d{1,2}))?'

        matches = re.compile(patron, re.DOTALL).findall(data)
       
        if not matches:
            logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + 
                            " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.category + 
                            ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  '
                            + 'Reportar el error con el log'))
            return itemlist                                             # si no hay más datos, algo no funciona, pintamos lo que tenemos

        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)

        # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
        for scrapedurl, scrapedtitle, year, name, value in matches:
            
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
            if item_local.channel_host:
                del item_local.channel_host
            if item_local.active:
                del item_local.active
            if item_local.contentTitle:
                del item_local.infoLabels['title']
            if item_local.season_colapse:
                del item_local.season_colapse

            if domain_alt in url:
                if name and value and id_name and id_value:
                    item_local.post = urllib.urlencode({name: value, id_name: id_value})
                elif name and value:
                    item_local.post = urllib.urlencode({name: value})
            else:
                if name and value and total_capis and titulo_post and value not in scrapedurl:
                    item_local.post = urllib.urlencode({name: value, "total_capis": total_capis, "tabla": tabla, "titulo": titulo_post})
            
            if item_local.post:
                item_local.url = urlparse.urljoin(host, url_post)               # url del post
            elif scrapedurl:
                item_local.url = urlparse.urljoin(host, scrapedurl)             # url de episodio
            else:
                item_local.url = url                                            # url de temporada
            item_local.referer = url
            item_local.url_tvshow = url
            
            title = scrapedtitle
            item_local.title = ''
            item_local.context = "['buscar_trailer']"

            # Extraemos números de temporada y episodio
            alt_epi = ''
            try:
                
                item_local.contentSeason, item_local.contentEpisodeNumber, alt_epi = \
                            scrapertools.find_single_match(title, patron_epi)
                
                item_local.contentSeason = int(item_local.contentSeason)
                item_local.contentEpisodeNumber = int(item_local.contentEpisodeNumber)
            except:
                logger.error('ERROR al extraer Temporada/Episodio: ' + str(title))
                item_local.contentSeason = 1
                item_local.contentEpisodeNumber = 1

            if alt_epi:                                                         # Si son episodios múltiples, lo guardamos
                item_local.infoLabels['episodio_titulo'] = 'al %s' % str(alt_epi).zfill(2)
                item_local.title = '%sx%s al %s' % (str(item_local.contentSeason), 
                        str(item_local.contentEpisodeNumber).zfill(2), str(alt_epi).zfill(2))
            else:
                item_local.title = '%sx%s - ' % (str(item_local.contentSeason), 
                        str(item_local.contentEpisodeNumber).zfill(2))
            
            if season_display > 0:                                              # Son de la temporada estos episodios?
                if item_local.contentSeason > season_display:
                    break
                elif item_local.contentSeason < season_display:
                    continue

            itemlist.append(item_local.clone())

            #logger.debug(item_local)
            
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))       #clasificamos
        
    if item.season_colapse and not item.add_videolibrary:                       # Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist, url='season')

    if not item.season_colapse:                                                 # Si no es pantalla de Temporadas, pintamos todo
        # Pasada por TMDB y clasificación de lista por temporada y episodio
        tmdb.set_infoLabels(itemlist, True, idioma_busqueda=idioma)

        # Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    #logger.debug(item)

    return itemlist


def actualizar_titulos(item):
    logger.info()
    
    # Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    item = generictools.update_title(item)
    
    # Volvemos a la siguiente acción en el canal
    return item


def choose_alternate_domain(item, url='', code='', patron='', itemlist=[], headers=None, referer=None, post=None):
    global host, host_index, host_emergency
    logger.info('Dominio: %s, Index: %s, Emergency: %s' % (host, str(host_index), str(host_emergency)))
    
    data = ''
    success = False
    code = 999
    url_alt = url
    host_index_init = host_index
    
    if not url:
        logger.info('Falta URL')
        return url_alt, data, success, code, item, itemlist

    if host_emergency:
        if len(host_list) > 2:
            host_index_init = config.get_setting('choose_domain', channel)
        else:
            logger.info('Dominio ALTERNATIVO no disponible: %s' % str(host_list))
            return url_alt, data, success, code, item, itemlist

    if item.headers: headers = item.headers
    if item.referer: referer = item.referer
    if item.post: post = item.post
    
    for x, host_alt in enumerate(host_list):
        if x == host_index or x == host_index_init: continue

        url_alt = url.replace(host, host_alt)
        data, success, code, item, itemlist = generictools.downloadpage(url_alt, timeout=timeout, headers=headers, 
                                          referer=referer, post=post, patron=patron, item=item, itemlist=itemlist)  # Descargamos la página
        if success:
            host_index = x
            host = host_alt
            host_emergency = True
            config.set_setting('alternate_domain', host_index, channel)
            logger.info('Dominio ALTERNATIVO: %s, Index: %s, Emergency: %s' % (host, str(host_index), str(host_emergency)))
            break
    else:
        url_alt = url
        logger.info('Dominio ALTERNATIVO no disponible: %s' % str(host_list))

    return url_alt, data, success, code, item, itemlist


def adjust_alternate_domain(item, reset=False):
    global host, host_index, host_emergency
    
    if reset:
        config.set_setting('alternate_domain', -1, channel)
        return
    
    if item:
        item.category = categoria
    
    if item and item.action in ['listado', 'findvideos', 'episodios']:
        host = scrapertools.find_single_match(item.url, '(http.*\:\/\/(?:.*ww[^\.]*\.)?[^\.]+\.[^\/]+)(?:\/|\?|$)')
        if not host.endswith('/'): host += '/'
        return
    
    host_index_alt = config.get_setting('alternate_domain', channel)
    if host_index_alt >= 0:
        host_index = host_index_alt
        host = host_list[host_index]
        host_emergency = True


def search(item, texto):
    logger.info()
    texto = texto.replace(" ", "+")
    adjust_alternate_domain(item)
    
    try:
        if domain_alt in host:
            item.url = host + '?s=' + texto
        else:
            item.url = host + 'secciones.php?sec=buscador&valor=' + texto
        item.extra = 'search'

        if texto:
            return listado(item)
        else:
            return []
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc(1))
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    adjust_alternate_domain(item)

    item.title = "newest"
    item.category_new = "newest"
    item.channel = channel
    if domain_alt in host:
        item.url = host + 'ultimos-torrents-4-x/'
    else:
        item.url = host + 'secciones.php?sec=ultimos_torrents'
    
    try:
        for cat in ['peliculas', 'series', 'documentales', 'torrent']:
            if cat != categoria: continue
                
            item.extra = cat
            if cat == 'torrent': item.extra = ''
            item.extra2 = "novedades"
            item.action = "listado"
            itemlist = listado(item)
            break

        if len(itemlist) > 0 and (">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title):
            itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        logger.error(traceback.format_exc(1))
        return []

    return itemlist
