# -*- coding: utf-8 -*-

from builtins import range
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import re
import time

from channelselector import get_thumb
from core import httptools
from core import scrapertools
from core import servertools
from core.item import Item
from platformcode import config, logger
from core import tmdb
from lib import generictools
from channels import filtertools
from channels import autoplay


#IDIOMAS = {'CAST': 'Castellano', 'LAT': 'Latino', 'VO': 'Version Original'}
IDIOMAS = {'Castellano': 'CAST', 'Latino': 'LAT', 'Version Original': 'VO'}
list_language = list(IDIOMAS.values())
list_quality = []
list_servers = ['torrent']


host = 'https://zonatorrent.tv/'
host_torrent = host[:-1]
channel = "zonatorrent"

categoria = channel.capitalize()
__modo_grafico__ = config.get_setting('modo_grafico', channel)
modo_ultima_temp = config.get_setting('seleccionar_ult_temporadda_activa', channel)        #Actualización sólo últ. Temporada?
timeout = config.get_setting('timeout_downloadpage', channel)


def mainlist(item):
    logger.info()
    itemlist = []
    
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_buscar = get_thumb("search.png")
    thumb_separador = get_thumb("next.png")
    thumb_settings = get_thumb("setting_0.png")

    autoplay.init(item.channel, list_servers, list_quality)
    
    itemlist.append(Item(channel=item.channel, title="Películas", action="submenu", url=host, thumbnail=thumb_pelis, extra="peliculas"))
    
    itemlist.append(Item(channel=item.channel, url=host, title="Series", action="submenu", thumbnail=thumb_series, extra="series"))
    
    itemlist.append(Item(channel=item.channel, title="Buscar...", action="search", url=host + "?s=", thumbnail=thumb_buscar, extra="search"))
    
    itemlist.append(Item(channel=item.channel, url=host, title="[COLOR yellow]Configuración:[/COLOR]", folder=False, thumbnail=thumb_separador))
    
    itemlist.append(Item(channel=item.channel, action="configuracion", title="Configurar canal", thumbnail=thumb_settings))
    
    autoplay.show_option(item.channel, itemlist)            #Activamos Autoplay

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
    
    thumb_cartelera = get_thumb("now_playing.png")
    thumb_pelis_az = get_thumb("channels_movie_az.png")
    thumb_pelis = get_thumb("channels_movie.png")
    thumb_pelis_hd = get_thumb("channels_movie_hd.png")
    thumb_pelis_vos = get_thumb("channels_vos.png")
    thumb_popular = get_thumb("popular.png")
    thumb_generos = get_thumb("genres.png")
    thumb_spanish = get_thumb("channels_spanish.png")
    thumb_latino = get_thumb("channels_latino.png")
    thumb_torrent = get_thumb("channels_torrent.png")
    thumb_series = get_thumb("channels_tvshow.png")
    thumb_series_az = get_thumb("channels_tvshow_az.png")
    
    
    if item.extra != "series":
        item.url_plus = "movies"
        itemlist.append(item.clone(title="Últimas Películas", action="listado", url=host + "pelicula-3", url_plus=item.url_plus, thumbnail=thumb_cartelera))
        itemlist.append(item.clone(title="Alfabético", action="alfabeto", url=host + "letters/%s", thumbnail=thumb_pelis_az, extra2 = 'alfabeto'))
        itemlist.append(item.clone(title="Géneros", action="categorias", url=host + item.url_plus, url_plus=item.url_plus, extra2= "generos", thumbnail=thumb_generos))
        itemlist.append(item.clone(title="Calidades", action="categorias", url=host + item.url_plus, url_plus=item.url_plus, extra2= "calidades", thumbnail=thumb_pelis_hd))
        itemlist.append(item.clone(title="Más vistas", action="listado", url=host +  "/peliculas-mas-vistas-2/", url_plus=item.url_plus, thumbnail=thumb_popular, extra2="popular"))
        itemlist.append(item.clone(title="Más votadas", action="listado", url=host + "/peliculas-mas-votadas/", url_plus=item.url_plus, thumbnail=thumb_popular, extra2="popular"))
        itemlist.append(item.clone(title="Castellano", action="listado", url=host + "?s=spanish", url_plus=item.url_plus, thumbnail=thumb_spanish, extra2="CAST"))
        itemlist.append(item.clone(title="Latino", action="listado", url=host + "?s=latino", url_plus=item.url_plus, thumbnail=thumb_latino, extra2="LAT"))
        itemlist.append(item.clone(title="Subtitulado", action="listado", url=host + "?s=Subtitulado", url_plus=item.url_plus, thumbnail=thumb_pelis_vos, extra2="VOSE"))

    else:
        item.url_plus = "serie-2"
        itemlist.append(item.clone(title="Series completas", action="listado", url=item.url + item.url_plus, url_plus=item.url_plus, thumbnail=thumb_series, extra="series"))
        itemlist.append(item.clone(title="Alfabético A-Z", action="alfabeto", url=item.url + "letters/%s", url_plus=item.url_plus, thumbnail=thumb_series_az, extra="series", extra2 = 'alfabeto'))
        itemlist.append(item.clone(title="Más vistas", action="listado", url=host +  "/peliculas-mas-vistas-2/", url_plus=item.url_plus, thumbnail=thumb_popular, extra2="popular"))
        itemlist.append(item.clone(title="Más votadas", action="listado", url=host + "/peliculas-mas-votadas/", url_plus=item.url_plus, thumbnail=thumb_popular, extra2="popular"))
        itemlist.append(item.clone(title="Castellano", action="listado", url=host + "?s=spanish", url_plus=item.url_plus, thumbnail=thumb_spanish, extra2="CAST"))
        itemlist.append(item.clone(title="Latino", action="listado", url=host + "?s=latino", url_plus=item.url_plus, thumbnail=thumb_latino, extra2="LAT"))
        itemlist.append(item.clone(title="Subtitulado", action="listado", url=host + "?s=Subtitulado", url_plus=item.url_plus, thumbnail=thumb_pelis_vos, extra2="VOSE"))

    return itemlist
    

def categorias(item):
    logger.info()
    
    itemlist = []
    
    data = ''
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        if not PY3:
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
    except:
        pass
        
    patron = '<div id="categories-2" class="Wdgt widget_categories"><div class="Title widget-title">Categorías</div><ul>(.*?)<\/ul><\/div>'
    #Verificamos si se ha cargado una página, y si además tiene la estructura correcta
    if not data or not scrapertools.find_single_match(data, patron):
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            for clone_inter, autoridad in item.intervencion:
                thumb_intervenido = get_thumb(autoridad)
                itemlist.append(item.clone(action='', title="[COLOR yellow]" + clone_inter.capitalize() + ': [/COLOR]' + intervenido_judicial + '. Reportar el problema en el foro', thumbnail=thumb_intervenido))
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL: " + item.url + data)
    if not data:    #Si no ha logrado encontrar nada, salimos
        itemlist.append(item.clone(action='', title=item.category + ': ERROR 01: SUBMENU: La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    data = scrapertools.find_single_match(data, patron)
    patron = '<li class="[^>]+><a href="([^"]+)"\s?(?:title="[^"]+")?>(.*?)<\/a><\/li>'
    matches = re.compile(patron, re.DOTALL).findall(data)

    if not matches:
        logger.error("ERROR 02: SUBMENU: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.category + ': ERROR 02: SUBMENU: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug(item.url_plus)
    #logger.debug(matches)

    for scrapedurl, scrapedtitle in matches:

        #Preguntamos por las entradas que corresponden al "extra2"
        if item.extra2 == 'calidades':
            if scrapedtitle.lower() in ['dvd full', 'tshq', 'bdrip', 'dvdscreener', 'brscreener r6', 'brscreener', 'webscreener', 'dvd', 'hdrip', 'screener', 'screeer', 'webrip', 'brrip', 'dvb', 'dvdrip', 'dvdsc', 'dvdsc - r6', 'hdts', 'hdtv', 'kvcd', 'line', 'ppv', 'telesync', 'ts hq', 'ts hq proper', '480p', '720p', 'ac3', 'bluray', 'camrip', 'ddc', 'hdtv - screener', 'tc screener', 'ts screener', 'ts screener alto', 'ts screener medio', 'vhs screener']:
                itemlist.append(item.clone(action="listado", title=scrapedtitle.capitalize().strip(), url=scrapedurl))
        
        else: 
            if scrapedtitle.lower() not in ['estrenos de cine', 'serie tv', 'dvd full', 'tshq', 'bdrip', 'dvdscreener', 'brscreener r6', 'brscreener', 'webscreener', 'dvd', 'hdrip', 'screener', 'screeer', 'webrip', 'brrip', 'dvb', 'dvdrip', 'dvdsc', 'dvdsc - r6', 'hdts', 'hdtv', 'kvcd', 'line', 'ppv', 'telesync', 'ts hq', 'ts hq proper', '480p', '720p', 'ac3', 'bluray', 'camrip', 'ddc', 'hdtv - screener', 'tc screener', 'ts screener', 'ts screener alto', 'ts screener medio', 'vhs screener']:
                itemlist.append(item.clone(action="listado", title=scrapedtitle.capitalize().strip(), url=scrapedurl))

    return itemlist
    
    
def alfabeto(item):
    logger.info()
    itemlist = []
    
    itemlist.append(item.clone(action="listado", title="0-9", url=item.url % "0-9"))

    for letra in ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']:
        itemlist.append(item.clone(action="listado", title=letra, url=item.url % letra.lower()))

    return itemlist

    
def listado(item):
    logger.info()
    itemlist = []
    item.category = categoria

    #logger.debug(item)
    
    curr_page = 1                                                               # Página inicial
    last_page = 99999                                                           # Última página inicial
    if item.curr_page:
        curr_page = int(item.curr_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.curr_page                                                      # ... y lo borramos
    if item.last_page:
        last_page = int(item.last_page)                                         # Si viene de una pasada anterior, lo usamos
        del item.last_page                                                      # ... y lo borramos
    
    cnt_tot = 40                                                                # Poner el num. máximo de items por página
    cnt_title = 0                                                               # Contador de líneas insertadas en Itemlist
    inicio = time.time()                                    # Controlaremos que el proceso no exceda de un tiempo razonable
    fin = inicio + 10                                                           # Después de este tiempo pintamos (segundos)
    timeout_search = timeout                                                    # Timeout para descargas
    if item.extra == 'search':
        timeout_search = timeout * 2                                            # Timeout un poco más largo para las búsquedas
        if timeout_search < 5:
            timeout_search = 5                                                  # Timeout un poco más largo para las búsquedas

    #Sistema de paginado para evitar páginas vacías o semi-vacías en casos de búsquedas con series con muchos episodios
    title_lista = []                            # Guarda la lista de series que ya están en Itemlist, para no duplicar lineas
    if item.title_lista:                                    # Si viene de una pasada anterior, la lista ya estará guardada
        title_lista.extend(item.title_lista)                                    # Se usa la lista de páginas anteriores en Item
        del item.title_lista                                                    # ... limpiamos
        
    if not item.extra2:                                                         # Si viene de Catálogo o de Alfabeto
        item.extra2 = ''
    
    next_page_url = item.url
    #Máximo num. de líneas permitidas por TMDB. Máx de 10 segundos por Itemlist para no degradar el rendimiento
    while cnt_title <= cnt_tot * 0.45 and curr_page <= last_page and fin > time.time():
    
        # Descarga la página
        data = ''
        try:
            data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)|&nbsp;", "", httptools.downloadpage(next_page_url, timeout=timeout_search).data)
            if not PY3:
                data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        except:
            pass
        
        if not data:                                    #Si la web está caída salimos sin dar error
            logger.error("ERROR 01: LISTADO: La Web no responde o ha cambiado de URL: " + item.url + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: LISTADO:.  La Web no responde o ha cambiado de URL. Si la Web está activa, reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #Patrón para todo, menos para Alfabeto
        patron = '<li class="TPostMv"><article id="[^"]+" class="[^"]+"><a href="(?P<url>[^"]+)".*?><div[^>]+><figure[^>]+><img[^>]+src="(?P<thumb>[^"]+)"[^>]+><\/figure>(?:<span class="TpTv BgA">(.*?)<\/span>)?<\/div><h2 class="Title">(?P<title>.*?)<\/h2>.*?<span class="Time[^>]+>(?P<duration>.*?)<\/span><span class="Date[^>]+>(?P<year>.*?)<\/span>(?:<span class="Qlty">(?P<quality>.*?)<\/span>)?<\/p><div class="Description">.*?<\/div><\/div><\/article><\/li>'
        
        #Si viene de Alfabeto, ponemos un patrón especializado
        if item.extra2 == 'alfabeto':
            patron = '<td class="MvTbImg"><a href="(?P<url>[^"]+)".*?src="(?P<thumb>[^"]+)"[^>]+>(?:<span class="TpTv BgA">(.*?)<\/span>)?<\/a><\/td>[^>]+>[^>]+><strong>(?P<title>.*?)<\/strong><\/a><\/td><td>(?P<year>.*?)<\/td><td><p class="Info"><span class="Qlty">(?P<quality>.*?)<\/span><\/p><\/td><td>(?P<duration>.*?)<\/td>'
            
        matches = re.compile(patron, re.DOTALL).findall(data)
        if not matches and not 'Lo sentimos, no tenemos nada que mostrar' in data:  #error
            item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
            if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
                item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
                return itemlist                                                     #Salimos
            
            logger.error("ERROR 02: LISTADO: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: LISTADO: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
            break                                       #si no hay más datos, algo no funciona, pintamos lo que tenemos
        
        #logger.debug("PATRON: " + patron)
        #logger.debug(matches)
        #logger.debug(data)
        
        #Buscamos la url de paginado y la última página
        if item.extra2 == 'alfabeto':                                       #patrón especial
            patron = "<div class='wp-pagenavi'><span class='pages'>Pagina \d+ of (\d+)<\/span><span class='current'>(\d+)<\/span>"
            patron += '<a class="page larger" title="[^"]+" href="([^"]+)">'
        else:
            patron = '<div class="tr-pagnav wp-pagenavi">'
            patron += "<span aria-current='page' class='page-numbers current'>(\d+)<\/span>.*?<a class='page-numbers' href='[^+]+'>(\d+)<\/a>"
            patron += '<a class="next page-numbers" href="([^"]+)">Siguiente'
        
        if last_page == 99999:                                              #Si es el valor inicial, buscamos
            try:
                if item.extra2 == 'alfabeto':                               #patrón especial
                    last_page, curr_page, next_page_url = scrapertools.find_single_match(data, patron)
                else:
                    curr_page, last_page, next_page_url = scrapertools.find_single_match(data, patron)
                curr_page = int(curr_page)
                last_page = int(last_page)
            except:                                                         #Si no lo encuentra, lo ponemos a 1
                #logger.error('ERROR 03: LISTADO: Al obtener la paginación: ' + patron)
                curr_page = 1
                last_page = 0
                next_page_url = item.url + '/page/1'
            #logger.debug('curr_page: ' + str(curr_page) + ' / last_page: ' + str(last_page) + ' / url: ' + next_page_url)
        if last_page > 1:
            curr_page += 1                                                  #Apunto ya a la página siguiente
            next_page_url = re.sub(r'\/page\/\d+', '/page/%s' % curr_page, next_page_url)
        
        #Empezamos el procesado de matches
        for scrapedurl, scrapedthumb, scrapedtype, scrapedtitle, scrapedduration, scrapedyear, scrapedquality in matches:
            if item.extra2 == 'alfabeto':                                   #Cambia el orden de tres parámetros
                duration = scrapedquality
                year = scrapedduration
                quality = scrapedyear
            else:                                                           #lo estándar
                duration = scrapedduration
                year = scrapedyear
                quality = scrapedquality
            
            #estandarizamos la duración
            if 'h' not in duration:
                duration = '0:' + duration.replace('m', '')
            else:
                duration = duration.replace('h ', ':').replace('m', '')
            duration = re.sub(r',.*?\]', ']', duration)
            if '0:0' in duration or ',' in duration:
                duration = ''
            else:
                try:
                    hora, minuto = duration.split(':')
                    duration = '%s:%s h' % (str(hora).zfill(2), str(minuto).zfill(2))
                except:
                    duration = ''
            
            #Algunos enlaces no filtran tipos, lo hago aquí
            if item.extra2 in ['alfabeto', 'CAST', 'LAT', 'VOSE', 'popular'] or item.category_new == 'newest':
                if item.extra == 'peliculas' and 'tv' in scrapedtype.lower():
                    continue
                elif item.extra == 'series' and not 'tv' in scrapedtype.lower():
                    continue

            title = scrapedtitle
            # Slugify, pero más light
            title = title.replace("á", "a").replace("é", "e").replace("í", "i")\
                    .replace("ó", "o").replace("ú", "u").replace("ü", "u")\
                    .replace("ï¿½", "ñ").replace("Ã±", "ñ")
            title = scrapertools.decode_utf8_error(title)
            
            item_local = item.clone()                                                   #Creamos copia de Item para trabajar
            if item_local.tipo:                                                         #... y limpiamos
                del item_local.tipo
            if item_local.totalItems:
                del item_local.totalItems
            if item_local.post_num:
                del item_local.post_num
            if item_local.intervencion:
                del item_local.intervencion
            if item_local.viewmode:
                del item_local.viewmode
            item_local.text_bold = True
            del item_local.text_bold
            item_local.text_color = True
            del item_local.text_color
            if item_local.url_plus:
                del item_local.url_plus
                
            title_subs = []                                                 #creamos una lista para guardar info importante
            item_local.language = []                                        #iniciamos Lenguaje
            item_local.quality = quality                                    #guardamos la calidad, si la hay
            item_local.url = scrapedurl                                     #guardamos el thumb
            item_local.thumbnail = scrapedthumb                             #guardamos el thumb
            item_local.context = "['buscar_trailer']"
            
            item_local.contentType = "movie"                                #por defecto, son películas
            item_local.action = "findvideos"

            #Analizamos los formatos de series
            if '-serie-tv-' in scrapedurl or item_local.extra == 'series' or 'tv' in scrapedtype.lower():
                item_local.contentType = "tvshow"
                item_local.action = "episodios"
                item_local.season_colapse = True                            #Muestra las series agrupadas por temporadas
                
            #Buscamos calidades adicionales
            if "3d" in title.lower() and not "3d" in item_local.quality.lower():
                if item_local.quality:
                    item_local.quality += " 3D"
                else:
                    item_local.quality = "3D"
                title = re.sub('(?i)3D', '', title)
                title = title.replace('[]', '')
            if item_local.quality:
                item_local.quality += ' %s' % scrapertools.find_single_match(title, '\[(.*?)\]')
            else:
                item_local.quality = '%s' % scrapertools.find_single_match(title, '\[(.*?)\]')
            
            #Detectamos idiomas
            if 'LAT' in item.extra2:
                item_local.language += ['LAT']
            elif 'VOSE' in item.extra2:
                item_local.language += ['VOSE']
            if item_local.extra2: del item_local.extra2
                
            if ("latino" in scrapedurl.lower() or "latino" in title.lower()) and "LAT" not in item_local.language:
                item_local.language += ['LAT']
            elif ('subtitulado' in scrapedurl.lower() or 'subtitulado' in title.lower() or 'vose' in title.lower()) and "VOSE" not in item_local.language:
                item_local.language += ['VOSE']
            elif ('version-original' in scrapedurl.lower() or 'version original' in title.lower() or 'vo' in title.lower()) and "VO" not in item_local.language:
                item_local.language += ['VO']
            
            if item_local.language == []:
                item_local.language = ['CAST']

            #Detectamos info interesante a guardar para después de TMDB
            if scrapertools.find_single_match(title, '[m|M].*?serie'):
                title = re.sub(r'[m|M]iniserie', '', title)
                title_subs += ["Miniserie"]
            if scrapertools.find_single_match(title, '[s|S]aga'):
                title = re.sub(r'[s|S]aga', '', title)
                title_subs += ["Saga"]
            if scrapertools.find_single_match(title, '[c|C]olecc'):
                title = re.sub(r'[c|C]olecc...', '', title)
                title_subs += ["Colección"]
                
            if "duolog" in title.lower():
                title_subs += ["[Saga]"]
                title = title.replace(" Duologia", "").replace(" duologia", "").replace(" Duolog", "").replace(" duolog", "")
            if "trilog" in title.lower():
                title_subs += ["[Saga]"]
                title = title.replace(" Trilogia", "").replace(" trilogia", "").replace(" Trilog", "").replace(" trilog", "")
            if "extendida" in title.lower() or "v.e." in title.lower()or "v e " in title.lower():
                title_subs += ["[V. Extendida]"]
                title = title.replace("Version Extendida", "").replace("(Version Extendida)", "").replace("V. Extendida", "").replace("VExtendida", "").replace("V Extendida", "").replace("V.Extendida", "").replace("V  Extendida", "").replace("V.E.", "").replace("V E ", "").replace("V:Extendida", "")
            
            #Analizamos el año.  Si no está claro ponemos '-'
            try:
                yeat_int = int(year)
                if yeat_int >= 1970 and yeat_int <= 2040:
                    item_local.infoLabels["year"] = yeat_int
                else:
                    item_local.infoLabels["year"] = '-'
            except:
                item_local.infoLabels["year"] = '-'
            
            #Empezamos a limpiar el título en varias pasadas
            patron = '\s?-?\s?(line)?\s?-\s?$'
            regex = re.compile(patron, re.I)
            title = regex.sub("", title)
            title = re.sub(r'\(\d{4}\s*?\)', '', title)
            title = re.sub(r'\[\d{4}\s*?\]', '', title)
            title = re.sub(r'[s|S]erie', '', title)
            title = re.sub(r'- $', '', title)

            #Limpiamos el título de la basura innecesaria
            title = re.sub(r'(?i)TV|Online|Spanish|Torrent|en Espa\xc3\xb1ol|Español|Latino|Subtitulado|Blurayrip|Bluray rip|\[.*?\]|R2 Pal|\xe3\x80\x90 Descargar Torrent \xe3\x80\x91|Completa|Temporada|Descargar|Torren|mkv|sbs|ts-', '', title)
            
            title = title.replace("Dual", "").replace("dual", "").replace("Subtitulada", "").replace("subtitulada", "").replace("Subt", "").replace("subt", "").replace("(Proper)", "").replace("(proper)", "").replace("Proper", "").replace("proper", "").replace("#", "").replace("(Latino)", "").replace("Latino", "").replace("LATINO", "").replace("Spanish", "").replace("Trailer", "").replace("Audio", "")
            title = title.replace("HDTV-Screener", "").replace("DVDSCR", "").replace("TS ALTA", "").replace("- HDRip", "").replace("(HDRip)", "").replace("- Hdrip", "").replace("(microHD)", "").replace("(DVDRip)", "").replace("HDRip", "").replace("(BR-LINE)", "").replace("(HDTS-SCREENER)", "").replace("(BDRip)", "").replace("(BR-Screener)", "").replace("(DVDScreener)", "").replace("TS-Screener", "").replace(" TS", "").replace(" Ts", "").replace(" 480p", "").replace(" 480P", "").replace(" 720p", "").replace(" 720P", "").replace(" 1080p", "").replace(" 1080P", "").replace("DVDRip", "").replace(" Dvd", "").replace(" DVD", "").replace(" V.O", "").replace(" Unrated", "").replace(" UNRATED", "").replace(" unrated", "").replace("screener", "").replace("TS-SCREENER", "").replace("TSScreener", "").replace("HQ", "").replace("AC3 5.1", "").replace("Telesync", "").replace("Line Dubbed", "").replace("line Dubbed", "").replace("LineDuB", "").replace("Line", "").replace("XviD", "").replace("xvid", "").replace("XVID", "").replace("Mic Dubbed", "").replace("HD", "").replace("V2", "").replace("CAM", "").replace("VHS.SCR", "").replace("Dvd5", "").replace("DVD5", "").replace("Iso", "").replace("ISO", "").replace("Reparado", "").replace("reparado", "").replace("DVD9", "").replace("Dvd9", "")

            #Terminamos de limpiar el título
            title = re.sub(r'\??\s?\d*?\&.*', '', title)
            title = re.sub(r'[\(|\[]\s+[\)|\]]', '', title)
            title = title.replace('()', '').replace('[]', '').strip().lower().title()

            #Limpiamos el año del título, siempre que no sea todo el título o una cifra de más dígitos
            if not scrapertools.find_single_match(title, '\d{5}'):
                title_alt = title
                title_alt = re.sub(r'[\[|\(]?\d{4}[\)|\]]?', '', title_alt).strip()
                if title_alt:
                    title = title_alt
            
            item_local.from_title = title.strip().lower().title()   #Guardamos esta etiqueta para posible desambiguación de título

            #Salvamos el título según el tipo de contenido
            if item_local.contentType == "movie":
                item_local.contentTitle = title.strip().lower().title()
            else:
                item_local.contentSerieName = title.strip().lower().title()

            item_local.title = title.strip().lower().title()

            #Añadimos la duración a la Calidad
            if duration:
                if item_local.quality:
                    item_local.quality += ' [%s]' % duration
                else:
                    item_local.quality = '[%s]' % duration
                
            #Guarda la variable temporal que almacena la info adicional del título a ser restaurada después de TMDB
            item_local.title_subs = title_subs

            #Ahora se filtra por idioma, si procede, y se pinta lo que vale
            if config.get_setting('filter_languages', channel) > 0 and item.extra2 not in ['CAST', 'LAT', 'VO', 'VOS', 'VOSE']:     #Si hay idioma seleccionado, se filtra
                itemlist = filtertools.get_link(itemlist, item_local, list_language)
            else:
                itemlist.append(item_local.clone())                     #Si no, pintar pantalla
            
            cnt_title = len(itemlist)                                   #Contador de líneas añadidas
            
            #logger.debug(item_local)

    #Pasamos a TMDB la lista completa Itemlist
    tmdb.set_infoLabels(itemlist, __modo_grafico__)
    
    #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
    item, itemlist = generictools.post_tmdb_listado(item, itemlist)

    # Si es necesario añadir paginacion
    if curr_page <= last_page:
        if last_page > 1:
            title = '%s de %s' % (curr_page-1, last_page)
        else:
            title = '%s' % curr_page-1

        itemlist.append(Item(channel=item.channel, action="listado", title=">> Página siguiente " + title, title_lista=title_lista, url=next_page_url, extra=item.extra, extra2=item.extra2, last_page=str(last_page), curr_page=str(curr_page)))

    return itemlist

    
def findvideos(item):
    logger.info()
    itemlist = []
    itemlist_t = []                                     #Itemlist total de enlaces
    itemlist_f = []                                     #Itemlist de enlaces filtrados
    titles = []                                         #Títulos de servidores Directos
    urls = []                                           #Urls de servidores Directos
    if not item.language:
        item.language = ['CAST']                        #Castellano por defecto
    matches = []
    item.category = categoria

    item.extra2 = 'xyz'
    del item.extra2
    
    #logger.debug(item)

    #Bajamos los datos de la página
    data = ''
    patron = '<a[^>]+href="([^"]+)"[^<]+</a></td><td><span><img[^>]+>(.*?)</span></td><td><span><img[^>]+>(.*?)</span></td><td><span>(.*?)</span>'
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)", "", httptools.downloadpage(item.url, timeout=timeout).data)
        if not PY3:
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        data = re.sub(r"&quot;", '"', data)
        data = re.sub(r"&lt;", '<', data)
    except:
        pass
        
    if not data:
        logger.error("ERROR 01: FINDVIDEOS: La Web no responde o la URL es erronea: " + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: FINDVIDEOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log', folder=False))
        
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            matches = item.emergency_urls[1]                                    #Restauramos matches de torrents
            titles = item.emergency_urls[2]                                     #Restauramos títulos de servidores Directos
            urls = item.emergency_urls[3]                                       #Restauramos urls de servidores Directos
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                                 #si no hay más datos, algo no funciona, pintamos lo que tenemos

    if not item.armagedon:
        matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches and not scrapertools.find_single_match(data, 'data-TPlayerNv="Opt\d+">.*? <span>(.*?)</span></li>'): #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)  #Llamamos al método para el pintado del error
        else:
            logger.error("ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web " + " / PATRON: " + patron + data)
            itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: FINDVIDEOS: No hay enlaces o ha cambiado la estructura de la Web.  Verificar en la Web esto último y reportar el error con el log', folder=False))
        
        if item.emergency_urls and not item.videolibray_emergency_urls:         #Hay urls de emergencia?
            matches = item.emergency_urls[1]                                    #Restauramos matches de torrents
            titles = item.emergency_urls[2]                                     #Restauramos títulos de servidores Directos
            urls = item.emergency_urls[3]                                       #Restauramos urls de servidores Directos
            item.armagedon = True                                               #Marcamos la situación como catastrófica 
        else:
            if item.videolibray_emergency_urls:                                 #Si es llamado desde creación de Videoteca...
                return item                                                     #Devolvemos el Item de la llamada
            else:
                return itemlist                                     #si no hay más datos, algo no funciona, pintamos lo que tenemos
    
    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls = []                                                #Iniciamos emergency_urls
        item.emergency_urls.append([])                                          #Reservamos el espacio para los .torrents locales
        matches_list = []                                                       # Convertimos matches-tuple a matches-list
        for tupla in matches:
            if isinstance(tupla, tuple):
                matches_list.append(list(tupla))
        if matches_list:
            item.emergency_urls.append(matches_list)                            # Salvamnos matches de los vídeos...  
        else:
            item.emergency_urls.append(matches)
    
    #Llamamos al método para crear el título general del vídeo, con toda la información obtenida de TMDB
    if not item.videolibray_emergency_urls:
        item, itemlist = generictools.post_tmdb_findvideos(item, itemlist)

    #Ahora tratamos los enlaces .torrent
    for x, (_scrapedurl, scrapedserver, language, quality) in enumerate(matches):    #leemos los torrents con la diferentes calidades
        
        scrapedurl = generictools.convert_url_base64(_scrapedurl, host_torrent)
        # Si ha habido un cambio en la url, actualizados matches para emergency_urls
        if item.videolibray_emergency_urls and scrapedurl != _scrapedurl:
            item.emergency_urls[1][x][0] = scrapedurl
        
        #Generamos una copia de Item para trabajar sobre ella
        item_local = item.clone()

        if 'torrent' not in scrapedserver.lower():                      #Si es un servidor Directo, lo dejamos para luego
            continue
            
        item_local.url = scrapedurl
        if '.io/' in item_local.url:
            item_local.url = re.sub(r'http.?:\/\/\w+\.\w+\/', host, item_local.url)     #Aseguramos el dominio del canal
        
        if item.videolibray_emergency_urls:
            item.emergency_urls[0].append(item_local.url)                       #guardamos la url y pasamos a la siguiente
            continue
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
        
        #Detectamos idiomas
        if ("latino" in scrapedurl.lower() or "latino" in language.lower()) and "LAT" not in item_local.language:
            item_local.language += ['LAT']
        elif ('subtitulado' in scrapedurl.lower() or 'subtitulado' in language.lower() or 'vose' in language.lower()) and "VOSE" not in item_local.language:
            item_local.language += ['VOSE']
        elif ('version-original' in scrapedurl.lower() or 'version original' in language.lower() or 'vo' in language.lower()) and "VO" not in item_local.language:
            item_local.language += ['VO']
        
        if item_local.language == []:
            item_local.language = ['CAST']
            
        #Añadimos la calidad y copiamos la duración
        item_local.quality = quality
        if scrapertools.find_single_match(item.quality, '(\[\d+:\d+\ h])'):
            item_local.quality += ' [/COLOR][COLOR white]%s' % scrapertools.find_single_match(item.quality, '(\[\d+:\d+\ h])')
        if item.armagedon:                                                      #Si es catastrófico, lo marcamos
            item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % item_local.quality
        
        #Buscamos si ya tiene tamaño, si no, los buscamos en el archivo .torrent
        size = scrapertools.find_single_match(item_local.quality, '\s\[(\d+,?\d*?\s\w\s?[b|B])\]')
        if not size and not item.armagedon:
            size = generictools.get_torrent_size(item_local.url)                #Buscamos el tamaño en el .torrent
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
            item_local.title = re.sub(r'\s\[\d+,?\d*?\s\w[b|B]\]', '', item_local.title) #Quitamos size de título, si lo traía
            size = size.replace('GB', 'G·B').replace('Gb', 'G·b').replace('MB', 'M·B')\
                        .replace('Mb', 'M·b').replace('.', ',')
            item_local.torrent_info = '%s' % size                               #Agregamos size
            if not item.unify:
                item_local.torrent_info = '[%s]' % item_local.torrent_info.strip().strip(',')
            item_local.quality = re.sub(r'\s\[\d+,?\d*?\s\w\s?[b|B]\]', '', item_local.quality)    #Quitamos size de calidad, si lo traía
        
        #Ahora pintamos el link del Torrent
        item_local.title = '[[COLOR yellow]?[/COLOR]] [COLOR yellow][Torrent][/COLOR] ' \
                        + '[COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR] %s' % \
                        (item_local.quality, str(item_local.language),  \
                        item_local.torrent_info)                                #Preparamos título de Torrent
        
        #Preparamos título y calidad, quitamos etiquetas vacías
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
        item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
        item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
        item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality).strip()
        item_local.quality = item_local.quality.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()

        item_local.alive = "??"                                                 #Calidad del link sin verificar
        item_local.action = "play"                                              #Visualizar vídeo
        item_local.server = "torrent"                                           #Servidor Torrent
        
        itemlist_t.append(item_local.clone())                                   #Pintar pantalla, si no se filtran idiomas
        
        # Requerido para FilterTools
        if config.get_setting('filter_languages', channel) > 0:                 #Si hay idioma seleccionado, se filtra
            itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío

        #logger.debug("TORRENT: " + scrapedurl + " / title gen/torr: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
        #logger.debug(item_local)
    
    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
        itemlist.extend(itemlist_t)                                             #Pintar pantalla con todo si no hay filtrado
    
    #Ahora tratamos los Servidores Directos
    itemlist_t = []                                                             #Itemlist total de enlaces
    itemlist_f = []                                                             #Itemlist de enlaces filtrados
    if not item.armagedon:
        titles = re.compile('data-..layer..="Opt\d+">(?:<span>)?.*?\s?(?:<strong>.*?<\/strong>)?(?:<\/span>)?<span>(.*?)<\/span><\/li>', re.DOTALL).findall(data)
        urls = re.compile('id="Opt\d+"><iframe[^>]+src="([^"]+)"', re.DOTALL).findall(data)
    
    #Si es un lookup para cargar las urls de emergencia en la Videoteca...
    if item.videolibray_emergency_urls:
        item.emergency_urls.append(titles)                                      #Salvamnos matches de los títulos...  
        item.emergency_urls.append(urls)                                        #Salvamnos matches de las urls...  
        return item                                                             #... y nos vamos

    #Recorremos la lista de servidores Directos, excluyendo YouTube para trailers
    if len(titles) == len(urls):
        for i in range(0, len(titles)):
            #Generamos una copia de Item para trabajar sobre ella
            item_local = item.clone()
            
            if i > 0:
                #logger.debug('titles: %s' % titles[i].strip())
                language, quality = titles[i].split(' - ')
                title = "%s" % titles[i].strip()
            else:
                title = titles[0]

            if "goo.gl" in urls[i]:
                try:
                    urls[i] = httptools.downloadpage(urls[i], follow_redirects=False, only_headers=True)\
                        .headers.get("location", "")
                except:
                    continue
            
            videourl = servertools.findvideos(urls[i])                      #Buscamos la url del vídeo
            
            #Ya tenemos un  enlace, lo pintamos
            if len(videourl) > 0:
                server = videourl[0][0]
                enlace = videourl[0][1]
                mostrar_server = True
                if config.get_setting("hidepremium"):                       #Si no se aceptan servidore premium, se ignoran
                    mostrar_server = servertools.is_server_enabled(server)
                if mostrar_server:
                    item_local.alive = "??"                                 #Se asume poe defecto que es link es dudoso
                    if server.lower() == 'youtube':                         #Pasamos de YouTube, usamos Trailers de Alfa
                        continue
                    if server.lower() != 'netutv':                          #Este servidor no se puede comprobar
                        #Llama a la subfunción de check_list_links(itemlist) para cada link de servidor
                        item_local.alive = servertools.check_video_link(enlace, server, timeout=timeout)
                    if '?' in item_local.alive:
                        alive = '?'                                         #No se ha podido comprobar el vídeo
                    elif 'no' in item_local.alive.lower():
                        continue                                            #El enlace es malo
                    else:
                        alive = ''                                          #El enlace está verificado

                #Detectamos idiomas
                item_local.language = []
                if "latino" in language.lower() and "LAT" not in item_local.language:
                    item_local.language += ['LAT']
                elif ('subtitulado' in language.lower() or 'vose' in language.lower()) and "VOSE" not in item_local.language:
                    item_local.language += ['VOSE']
                elif ('version original' in language.lower() or 'vo' in language.lower()) and "VO" not in item_local.language:
                    item_local.language += ['VO']
                
                if item_local.language == []:
                    item_local.language = ['CAST']

                #Ahora pintamos el link del Servidor Directo
                item_local.url = enlace
                item_local.quality = quality                                            #Añadimos la calidad
                if scrapertools.find_single_match(item.quality, '(\[\d+:\d+\ h])'):    #Añadimos la duración
                    item_local.quality += ' [/COLOR][COLOR white]%s' % scrapertools.find_single_match(item.quality, '(\[\d+:\d+\ h])')
                if item.armagedon:                                                      #Si es catastrófico, lo marcamos
                    item_local.quality = '[/COLOR][COLOR hotpink][E] [COLOR limegreen]%s' % item_local.quality
                item_local.title = '[COLOR yellow][%s][/COLOR] [COLOR yellow][%s][/COLOR] [COLOR limegreen][%s][/COLOR] [COLOR red]%s[/COLOR]' % (alive, server.capitalize(), item_local.quality, str(item_local.language))
                
                #Preparamos título y calidad, quitamos etiquetas vacías
                item_local.title = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.title)    
                item_local.title = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.title)
                item_local.title = item_local.title.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
                item_local.quality = re.sub(r'\s?\[COLOR \w+\]\[\[?\s?\]?\]\[\/COLOR\]', '', item_local.quality)
                item_local.quality = re.sub(r'\s?\[COLOR \w+\]\s?\[\/COLOR\]', '', item_local.quality)
                item_local.quality = item_local.quality.replace("--", "").replace("[]", "").replace("()", "").replace("(/)", "").replace("[/]", "").strip()
                
                item_local.action = "play"                                      #Visualizar vídeo
                item_local.server = server                                      #Servidor Directo
                
                itemlist_t.append(item_local.clone())                           #Pintar pantalla, si no se filtran idiomas
        
                # Requerido para FilterTools
                if config.get_setting('filter_languages', channel) > 0:         #Si hay idioma seleccionado, se filtra
                    itemlist_f = filtertools.get_link(itemlist_f, item_local, list_language)  #Pintar pantalla, si no está vacío
                
                #logger.debug("DIRECTO: " server + ' / ' + enlace + " / title: " + item.title + " / " + item_local.title + " / calidad: " + item_local.quality + " / content: " + item_local.contentTitle + " / " + item_local.contentSerieName)
                
                #logger.debug(item_local)

    if len(itemlist_f) > 0:                                                     #Si hay entradas filtradas...
        itemlist.extend(itemlist_f)                                             #Pintamos pantalla filtrada
    else:                                                                       
        if config.get_setting('filter_languages', channel) > 0 and len(itemlist_t) > 0: #Si no hay entradas filtradas ...
            thumb_separador = get_thumb("next.png")                             #... pintamos todo con aviso
            itemlist.append(Item(channel=item.channel, url=host, title="[COLOR red][B]NO hay elementos con el idioma seleccionado[/B][/COLOR]", thumbnail=thumb_separador, folder=False))
        itemlist.extend(itemlist_t)                                             #Pintar pantalla con todo si no hay filtrado
    
    # Requerido para AutoPlay
    autoplay.start(itemlist, item)                                              #Lanzamos Autoplay
    
    return itemlist

    
def episodios(item):
    logger.info()
    itemlist = []
    item.category = categoria
    
    #logger.debug(item)

    if item.from_title:
        item.title = item.from_title
    item.extra2 = 'xyz'
    del item.extra2
    
    item.quality = re.sub(r'\s?\[\d+:\d+\ h]', '', item.quality)                    #quitamos la duración de la serie
    
    #Limpiamos num. Temporada y Episodio que ha podido quedar por Novedades
    season_display = 0
    if item.contentSeason:
        if item.season_colapse:                                                     #Si viene del menú de Temporadas...
            season_display = item.contentSeason                                     #... salvamos el num de sesión a pintar
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
    #if not item.infoLabels['tmdb_id']:
    try:
        tmdb.set_infoLabels(item, True)                             #TMDB de cada Temp
    except:
        pass
        
    modo_ultima_temp_alt = modo_ultima_temp
    if item.ow_force == "1":                                        #Si hay un traspaso de canal o url, se actualiza todo 
        modo_ultima_temp_alt = False
    
    max_temp = 1
    if item.infoLabels['number_of_seasons']:
        max_temp = item.infoLabels['number_of_seasons']
    y = []
    if modo_ultima_temp_alt and item.library_playcounts:            #Averiguar cuantas temporadas hay en Videoteca
        patron = 'season (\d+)'
        matches = re.compile(patron, re.DOTALL).findall(str(item.library_playcounts))
        for x in matches:
            y += [int(x)]
        max_temp = max(y)

    # Descarga la página
    data = ''                                                       #Inserto en num de página en la url
    try:
        data = re.sub(r"\n|\r|\t|\s{2}|(<!--.*?-->)|&nbsp;", "", httptools.downloadpage(item.url, timeout=timeout).data)
        if not PY3:
            data = unicode(data, "utf-8", errors="replace").encode("utf-8")
        data = re.sub(r"&quot;", '"', data)
        data = re.sub(r"&lt;", '<', data)
        data = re.sub(r"&gt;", '>', data)
    except:                                                         #Algún error de proceso, salimos
        pass
        
    if not data:
        logger.error("ERROR 01: EPISODIOS: La Web no responde o la URL es erronea" + item.url)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 01: EPISODIOS:.  La Web no responde o la URL es erronea. Si la Web está activa, reportar el error con el log'))
        return itemlist

    #Buscamos los episodios
    patron = '<tr><td><span class="Num">\d+<\/span><\/td><td class="MvTbImg B"><a href="([^"]+)" class="MvTbImg">(?:<span class="[^>]+>)?<img src="([^"]+)" alt="([^"]+)">(?:<\/span>)?<\/a><\/td><td class="MvTbTtl">[^>]+>(.*?)<\/a>'
    matches = re.compile(patron, re.DOTALL).findall(data)
    if not matches:                                                             #error
        item = generictools.web_intervenida(item, data)                         #Verificamos que no haya sido clausurada
        if item.intervencion:                                                   #Sí ha sido clausurada judicialmente
            item, itemlist = generictools.post_tmdb_episodios(item, itemlist)   #Llamamos al método para el pintado del error
            return itemlist                                                     #Salimos
        
        logger.error("ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web " + " / PATRON: " + patron + " / DATA: " + data)
        itemlist.append(item.clone(action='', title=item.channel.capitalize() + ': ERROR 02: EPISODIOS: Ha cambiado la estructura de la Web.  Reportar el error con el log'))
        return itemlist                         #si no hay más datos, algo no funciona, pintamos lo que tenemos

    #logger.debug("PATRON: " + patron)
    #logger.debug(matches)
    #logger.debug(data)
    
    season = max_temp
    #Comprobamos si realmente sabemos el num. máximo de temporadas
    if item.library_playcounts or (item.infoLabels['number_of_seasons'] and item.tmdb_stat):
        num_temporadas_flag = True
    else:
        num_temporadas_flag = False

    # Recorremos todos los episodios generando un Item local por cada uno en Itemlist
    for scrapedurl, scrapedthumbnail, scrapedtitle, scrapedepi_name in matches:
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
        
        item_local.title = ''
        item_local.context = "['buscar_trailer']"
        item_local.url = scrapedurl
        title = scrapedtitle
        item_local.language = []
        
        #Buscamos calidades del episodio
        if 'hdtv' in scrapedtitle.lower() or 'hdtv' in scrapedurl:
            item_local.quality = 'HDTV'
        elif 'hd7' in scrapedtitle.lower() or 'hd7' in scrapedurl:
            item_local.quality = 'HD720p'
        elif 'hd1' in scrapedtitle.lower() or 'hd1' in scrapedurl:
            item_local.quality = 'HD1080p'
        
        #Buscamos idiomas del episodio
        lang = scrapedtitle.strip()
        if ('vo' in lang.lower() or 'v.o' in lang.lower() or 'vo' in scrapedurl.lower() or 'v.o' in scrapedurl.lower()) and not 'VO' in item_local.language:
            item_local.language += ['VO']
        elif ('vose' in lang.lower() or 'v.o.s.e' in lang.lower() or 'vose' in scrapedurl.lower() or 'v.o.s.e' in scrapedurl.lower()) and not 'VOSE' in item_local.language:
            item_local.language += ['VOSE']
        elif ('latino' in lang.lower() or 'latino' in scrapedurl.lower()) and not 'LAT' in item_local.language:
            item_local.language += ['LAT']
            
        if not item_local.language:
            item_local.language += ['CAST']

        #Buscamos la Temporada y el Episodio
        try:
            item_local.contentEpisodeNumber = 0
            if 'miniserie' in title.lower():
                item_local.contentSeason = 1
                title = title.replace('miniserie', '').replace('MiniSerie', '')
            elif 'completa' in title.lower():
                patron = '[t|T].*?(\d+) [c|C]ompleta'
                if scrapertools.find_single_match(title, patron):
                    item_local.contentSeason = int(scrapertools.find_single_match(title, patron))
            if not item_local.contentSeason:
                #Extraemos los episodios
                patron = '(\d{1,2})[x|X](\d{1,2})'
                item_local.contentSeason, item_local.contentEpisodeNumber = scrapertools.find_single_match(title, patron)
                item_local.contentSeason = int(item_local.contentSeason)
                item_local.contentEpisodeNumber = int(item_local.contentEpisodeNumber)
        except:
            logger.error('ERROR al extraer Temporada/Episodio: ' + title)
            item_local.contentSeason = 1
            item_local.contentEpisodeNumber = 0
        
        #Si son episodios múltiples, lo extraemos
        patron1 = '\d+[x|X]\d{1,2}.?(?:y|Y|al|Al)?(?:\d+[x|X]\d{1,2})?.?(?:y|Y|al|Al)?.?\d+[x|X](\d{1,2})'
        epi_rango = scrapertools.find_single_match(title, patron1)
        if epi_rango:
            item_local.infoLabels['episodio_titulo'] = 'al %s %s' % (epi_rango, scrapedepi_name)
            item_local.title = '%sx%s al %s -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2), str(epi_rango).zfill(2))
        else:
            item_local.title = '%sx%s -' % (str(item_local.contentSeason), str(item_local.contentEpisodeNumber).zfill(2))
            item.infoLabels['episodio_titulo'] = '%s' %scrapedepi_name

        if modo_ultima_temp_alt and item.library_playcounts:        #Si solo se actualiza la última temporada de Videoteca
            if item_local.contentSeason < max_temp:
                continue                                            #salta al siguiente episodio

        #Mostramos solo la temporada requerida
        if season_display > 0:
            if item_local.contentSeason > season_display:
                break
            elif item_local.contentSeason < season_display:
                continue
        
        itemlist.append(item_local.clone())
        
        #logger.debug(item_local)
            
    if len(itemlist) > 1:
        itemlist = sorted(itemlist, key=lambda it: (int(it.contentSeason), int(it.contentEpisodeNumber)))       #clasificamos
        
    if item.season_colapse and not item.add_videolibrary:                       #Si viene de listado, mostramos solo Temporadas
        item, itemlist = generictools.post_tmdb_seasons(item, itemlist)

    if not item.season_colapse:                                                 #Si no es pantalla de Temporadas, pintamos todo
        # Pasada por TMDB y clasificación de lista por temporada y episodio
        tmdb.set_infoLabels(itemlist, True)

        #Llamamos al método para el maquillaje de los títulos obtenidos desde TMDB
        item, itemlist = generictools.post_tmdb_episodios(item, itemlist)
    
    #logger.debug(item)

    return itemlist
    
    
def actualizar_titulos(item):
    logger.info()
    
    item = generictools.update_title(item) #Llamamos al método que actualiza el título con tmdb.find_and_set_infoLabels
    
    #Volvemos a la siguiente acción en el canal
    return item

    
def search(item, texto):
    logger.info()
    #texto = texto.replace(" ", "+")
    
    try:
        item.url = item.url + texto

        if texto != '':
            return listado(item)
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []
 
 
def newest(categoria):
    logger.info()
    itemlist = []
    item = Item()
    
    try:
        if categoria == 'peliculas':
            item.url = host + "estrenos-de-cine-2"
            item.extra = "peliculas"
            item.channel = channel
            item.category_new= 'newest'

            itemlist = listado(item)
            if len(itemlist) > 0 and (">> Página siguiente" in itemlist[-1].title or "Pagina siguiente >>" in itemlist[-1].title):
                itemlist.pop()

    # Se captura la excepción, para no interrumpir al canal novedades si un canal falla
    except:
        import sys
        for line in sys.exc_info():
            logger.error("{0}".format(line))
        return []

    return itemlist
