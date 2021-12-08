# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# Unify
# ------------------------------------------------------------
# Herramientas responsables de unificar diferentes tipos de
# datos obtenidos de las paginas
# ----------------------------------------------------------

#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import os
import unicodedata
import re

from platformcode import config
from core.item import Item
from core import scrapertools
from platformcode import logger
import json

# Lista de elementos posibles en el titulo
color_list = ['movie',
              'tvshow',
              'year',
              'rating_1',
              'rating_2',
              'rating_3',
              'quality',
              'cast',
              'lat',
              'vose',
              'vos',
              'vo',
              'server',
              'library',
              'update',
              'no_update']

styles_path = os.path.join(config.get_runtime_path(), 'resources', 'color_styles.json')
colors_file = json.load(open(styles_path, "r"))

thumb_dict = {"movies": "https://s10.postimg.cc/fxtqzdog9/peliculas.png",
    "tvshows": "https://s10.postimg.cc/kxvslawe1/series.png",
    "on air":"https://i.postimg.cc/HLLJWMcr/en-emision.png",
    "all": "https://s10.postimg.cc/h1igpgw0p/todas.png",
    "genres": "https://s10.postimg.cc/6c4rx3x1l/generos.png",
    "search": "https://s10.postimg.cc/v985e2izd/buscar.png",
    "quality": "https://s10.postimg.cc/9bbojsbjd/calidad.png",
    "audio": "https://s10.postimg.cc/b34nern7d/audio.png",
    "newest": "https://s10.postimg.cc/g1s5tf1bt/novedades.png",
    "last": "https://s10.postimg.cc/i6ciuk0eh/ultimas.png",
    "hot": "https://s10.postimg.cc/yu40x8q2x/destacadas.png",
    "year": "https://s10.postimg.cc/atzrqg921/a_o.png",
    "alphabet": "https://s10.postimg.cc/4dy3ytmgp/a-z.png",
    "recomended": "https://s10.postimg.cc/7xk1oqccp/recomendadas.png",
    "more watched": "https://s10.postimg.cc/c6orr5neh/masvistas.png",
    "more voted": "https://s10.postimg.cc/lwns2d015/masvotadas.png",
    "favorites": "https://s10.postimg.cc/rtg147gih/favoritas.png",
    "colections": "https://s10.postimg.cc/ywnwjvytl/colecciones.png",
    "categories": "https://s10.postimg.cc/v0ako5lmh/categorias.png",
    "premieres": "https://s10.postimg.cc/sk8r9xdq1/estrenos.png",
    "documentaries": "https://s10.postimg.cc/68aygmmcp/documentales.png",
    "language": "https://s10.postimg.cc/6wci189ft/idioma.png",
    "new episodes": "https://s10.postimg.cc/fu4iwpnqh/nuevoscapitulos.png",
    "country": "https://s10.postimg.cc/yz0h81j15/pais.png",
    "adults": "https://s10.postimg.cc/s8raxc51l/adultos.png",
    "recents": "https://s10.postimg.cc/649u24kp5/recents.png",
    "updated" : "https://s10.postimg.cc/46m3h6h9l/updated.png",
    "actors": "https://i.postimg.cc/tC2HMhVV/actors.png",
    "cast": "https://i.postimg.cc/qvfP5Xvt/cast.png",
    "lat": "https://i.postimg.cc/Gt8fMH0J/lat.png",
    "vose": "https://i.postimg.cc/kgmnbd8h/vose.png",
    "vo": "https://i.postimg.cc/Ss9gF3nG/vo.png",
    "accion": "https://s14.postimg.cc/sqy3q2aht/action.png",
    "adolescente" : "https://s10.postimg.cc/inq7u4p61/teens.png",
    "adultos": "https://s10.postimg.cc/s8raxc51l/adultos.png",
    "animacion": "https://s14.postimg.cc/vl193mupd/animation.png",
    "anime" : "https://s10.postimg.cc/n9mc2ikzt/anime.png",
    "artes marciales" : "https://s10.postimg.cc/4u1v51tzt/martial_arts.png",
    "asiaticas" : "https://i.postimg.cc/Xq0HXD5d/asiaticas.png",
    "aventura": "https://s14.postimg.cc/ky7fy5he9/adventure.png",
    "belico": "https://s14.postimg.cc/5e027lru9/war.png",
    "biografia" : "https://s10.postimg.cc/jq0ecjxnt/biographic.png",
    "carreras": "https://s14.postimg.cc/yt5qgdr69/races.png",
    "ciencia ficcion": "https://s14.postimg.cc/8kulr2jy9/scifi.png",
    "cine negro" : "https://s10.postimg.cc/6ym862qgp/noir.png",
    "comedia": "https://s14.postimg.cc/9ym8moog1/comedy.png",
    "cortometraje" : "https://s10.postimg.cc/qggvlxndl/shortfilm.png",
    "crimen": "https://s14.postimg.cc/duzkipjq9/crime.png",
    "de la tv": "https://s10.postimg.cc/94gj0iwh5/image.png",
    "deporte": "https://s14.postimg.cc/x1crlnnap/sports.png",
    "destacadas": "https://s10.postimg.cc/yu40x8q2x/destacadas.png",
    "documental": "https://s10.postimg.cc/68aygmmcp/documentales.png",
    "doramas":"https://s10.postimg.cc/h4dyr4nfd/doramas.png",
    "drama": "https://s14.postimg.cc/fzjxjtnxt/drama.png",
    "erotica" : "https://s10.postimg.cc/dcbb9bfx5/erotic.png",
    "espanolas" : "https://s10.postimg.cc/x1y6zikx5/spanish.png",
    "estrenos" : "https://s10.postimg.cc/sk8r9xdq1/estrenos.png",
    "extranjera": "https://s10.postimg.cc/f44a4eerd/foreign.png",
    "familiar": "https://s14.postimg.cc/jj5v9ndsx/family.png",
    "fantasia": "https://s14.postimg.cc/p7c60ksg1/fantasy.png",
    "fantastico" : "https://s10.postimg.cc/tedufx5eh/fantastic.png",
    "historica": "https://s10.postimg.cc/p1faxj6yh/historic.png",
    "horror" : "https://s10.postimg.cc/8exqo6yih/horror2.png",
    "infantil": "https://s14.postimg.cc/4zyq842mp/childish.png",
    "intriga": "https://s14.postimg.cc/5qrgdimw1/intrigue.png",
    "latino" : "https://s10.postimg.cc/swip0b86h/latin.png",
    "mexicanas" : "https://s10.postimg.cc/swip0b86h/latin.png",
    "misterio": "https://s14.postimg.cc/3m73cg8ep/mistery.png",
    "musical": "https://s10.postimg.cc/hy7fhtecp/musical.png",
    "peleas" : "https://s10.postimg.cc/7a3ojbjwp/Fight.png",
    "policial" : "https://s10.postimg.cc/wsw0wbgbd/cops.png",
    "recomendadas": "https://s10.postimg.cc/7xk1oqccp/recomendadas.png",
    "religion" : "https://s10.postimg.cc/44j2skquh/religion.png",
    "romance" : "https://s10.postimg.cc/yn8vdll6x/romance.png",
    "romantica": "https://s14.postimg.cc/8xlzx7cht/romantic.png",
    "suspenso": "https://s10.postimg.cc/7peybxdfd/suspense.png",
    "telenovelas": "https://i.postimg.cc/QCXZkyDM/telenovelas.png",
    "terror": "https://s14.postimg.cc/thqtvl52p/horror.png",
    "thriller": "https://s14.postimg.cc/uwsekl8td/thriller.png",
    "western": "https://s10.postimg.cc/5wc1nokjt/western.png"
    }

def init_colors():
    # for color in color_list:
    #     config.set_setting("%s_color" % (color ), 'white')
    [config.set_setting("%s_color" % color, 'white') for color in color_list]

def set_genre(string):
    #logger.info()

    genres_dict = {'accion':['accion', 'action', 'accion y aventura', 'action & adventure'],
                   'adultos':['adultos', 'adultos +', 'adulto'],
                   'animacion':['animacion', 'animacion e infantil', 'dibujos animados'],
                   'adolescente':['adolescente', 'adolescentes', 'adolescencia', 'adolecentes'],
                   'aventura':['aventura', 'aventuras'],
                   'belico':['belico', 'belica', 'belicas', 'guerra', 'belico guerra'],
                   'biografia':['biografia', 'biografias', 'biografica', 'biograficas', 'biografico'],
                   'ciencia ficcion':['ciencia ficcion', 'cienciaficcion', 'sci fi', 'c ficcion'],
                   'cine negro':['film noir', 'negro'],
                   'comedia':['comedia', 'comedias'],
                   'cortometraje':['cortometraje', 'corto', 'cortos'],
                   'de la tv':['de la tv', 'television', 'tv'],
                   'deporte':['deporte', 'deportes'],
                   'destacadas':['destacada', 'destacadas'],
                   'documental':['documental', 'documentales'],
                   'erotica':['erotica', 'erotica +', 'eroticas', 'eroticas +', 'erotico', 'erotico +'],
                   'estrenos':['estrenos', 'estrenos'],
                   'extranjera':['extrajera', 'extrajeras', 'foreign'],
                   'familiar':['familiar', 'familia'],
                   'fantastico':['fantastico', 'fantastica', 'fantasticas'],
                   'historica':['historica', 'historicas', 'historico', 'historia'],
                   'infantil':['infantil', 'kids'],
                   'musical':['musical', 'musicales', 'musica'],
                   'policial':['policial', 'policiaco', 'policiaca'],
                   'recomendadas':['recomedada', 'recomendadas'],
                   'religion':['religion', 'religiosa', 'religiosas'],
                   'romantica':['romantica', 'romanticas', 'romantico'],
                   'suspenso':['suspenso', 'suspense'],
                   'thriller':['thriller', 'thrillers'],
                   'western':['western', 'westerns', 'oeste western']
                   }
    string = re.sub(r'peliculas de |pelicula de la |peli |cine ','', string)
    for genre, variants in genres_dict.items():
        if string in variants:
            string = genre

    return string


def remove_format(string):
    #logger.info()
    #logger.debug('entra en remove: %s' % string)
    string = string.rstrip()
    string = re.sub(r'(\[|\[\/)(?:color|COLOR|b|B|i|I).*?\]|\[|\]|\(|\)|\:|\.', '', string)
    #logger.debug('sale de remove: %s' % string)
    return string


def normalize(string):
    if not PY3 and isinstance(string, str):
        string = string.decode('utf-8')
    normal = ''.join((c for c in unicodedata.normalize('NFD', unicode(string)) if unicodedata.category(c) != 'Mn'))
    return normal


def simplify(string):

    #logger.info()
    #logger.debug('entra en simplify: %s'%string)
    string = remove_format(string)
    string = string.replace('-',' ').replace('_',' ')
    string = re.sub(r'\d+','', string)
    string = string.strip()

    notilde = normalize(string)
    try:
        string = notilde.decode()
    except:
        pass
    string = string.lower()
    #logger.debug('sale de simplify: %s' % string)

    return string


def add_languages(title, languages):
    #logger.info()

    if isinstance(languages, list):
        for language in languages:
            title = '%s %s' % (title, set_color(language, language))
    else:
        title = '%s %s' % (title, set_color(languages, languages))
    return title


def add_info_plot(plot, languages, quality, vextend):
    #logger.info()
    last = '[/I][/B]\n'

    if languages:
        l_part = '[COLOR yellowgreen][B][I]Idiomas:[/COLOR] '
        mid = ''

        if isinstance(languages, list):
            for language in languages:
                mid += '%s ' % (set_color(language, language))
        else:
            mid = '%s ' % (set_color(languages, languages))

        p_lang = '%s%s%s' % (l_part, mid, last)

    if quality:
        q_part = '[COLOR yellowgreen][B][I]Calidad:[/COLOR] '
        p_quality = '%s%s%s' % (q_part, quality, last)

    if vextend:
        v_part = '[COLOR yellowgreen][B][I]Tipo:[/COLOR] '
        p_vextend = '%s%s%s' % (v_part, "[Versión Extendida]", last)

    if languages and quality and vextend:
        plot_ = '%s%s%s\n%s' % (p_lang, p_quality, p_vextend, plot)
    elif languages and quality:
        plot_ = '%s%s\n%s' % (p_lang, p_quality, plot)
    elif languages:
        plot_ = '%s\n%s' % (p_lang, plot)

    elif quality:
        plot_ = '%s\n%s' % (p_quality, plot)

    elif vextend:
        plot_ = '%s\n%s' % (p_vextend, plot)

    else:
        plot_ = plot

    return plot_


def set_color(title, category):
    #logger.info()

    preset = config.get_setting("preset_style", default="Estilo 1")
    color_setting = colors_file[preset]

    color_scheme_generic = ['otro', 'dual']

    #logger.debug('category antes de remove: %s' % category)
    category = remove_format(category).lower()

    # Se verifica el estado de la opcion de colores personalizados
    custom_colors = config.get_setting('title_color')

    # Se Forma el diccionario de colores para cada elemento, la opcion esta activas utiliza la configuracion del
    #  usuario, si no  pone el titulo en blanco.
    if title not in ['', ' ']:

        color_scheme = {
            element: remove_format(config.get_setting('%s_color' % element)) if custom_colors else remove_format(
                color_setting.get(element, 'white')) for element in color_list}
        for gen in color_scheme_generic:
            color_scheme[gen] = "white"

        if category not in ['movie', 'tvshow', 'library', 'otro', 'update', 'no_update']:
            title = "[COLOR %s][%s][/COLOR]" % (color_scheme.get(category, 'blue'), title)
        else:
            title = "[COLOR %s]%s[/COLOR]" % (color_scheme[category], title)
    return title


def set_lang(language):
    #logger.info()

    langs = {
             "cast" : ['castellano','español','espanol','cast','esp','espaol', 'es','zc', 'spa', 'spanish', 'vc'],
             "ita": ['italiano','italian','ita','it'],
             "lat": ['latino','lat','la', 'español latino', 'espanol latino', 'espaol latino', 'zl', 'mx', 'co', 'vl'],
             "vose": ['subtitulado','subtitulada','sub','sub espanol','vose','espsub','su','subs castellano',
                      'sub español', 'vs', 'zs', 'vs', 'english-spanish subs', 'ingles sub espanol',
                      'ingles sub español'],
             "vos": ['vos', 'sub ingles', 'engsub', 'vosi','ingles subtitulado', 'sub: ingles'],
             "vo": ['ingles', 'en','vo', 'ovos', 'eng','v.o', 'english'],
             "dual": ['dual']
             }

    language = scrapertools.decodeHtmlentities(language)
    language = simplify(language)

    #logger.debug('language before simplify: %s' % language)
    #logger.debug('old language: %s' % old_lang)

    lang = "other"
    for k, v in langs.items():
        if language in v:
            lang = "%s" % k
    #logger.debug('language after simplify: %s' % language)

    return lang


def title_format(item, c_file=colors_file, srv_lst={}):
    global colors_file
    colors_file = c_file

    new_title = list()

    lang = False
    simple_language = ""

    videolibrary = True if item.channel == "videolibrary" else False
    vextend = True if "extend" in item.title.lower() else False

    # Pseudo tags

    if not item.action:
        if item.title:
            item.title = "[B]**- %s -**[/B]" % item.title
        item.thumbnail = "https://i.postimg.cc/ZqRGSfZF/null.png"
        return item

    # Ignored actions

    if item.action in ["mainlist", "submenu_tools", "setting_torrent", "channel_config", "buscartrailer",
                       "actualizar_titulos", "no_filter"] or item.channel in ["downloads"]:
        return item

    # Define Content type

    if item.contentType and "library" not in item.action:
        c_type = item.contentType
        if scrapertools.find_single_match(item.title, "(\d+(?:x|X)\d+)") and not item.unify_extended:
            c_type = "episode"
    else:
        c_type = detect_content_type(item)

    if not c_type and not videolibrary:
        logger.debug("Tipo desconocido: %s" % c_type)
        return item

    # Verify InfoLabels

    if item.infoLabels:
        info = item.infoLabels
    else:
        return item

    # Verify Trakt and News Grouped

    checks = verify_checks(item.title)

    # Define Language

    if item.language:
        simple_language, lang = get_languages(item.language)

    # Server format

    if c_type == "server" or item.action == "play":
        if item.server:
            title = "%s" % item.server.capitalize()
        else:
            title = set_server_name(item.title, srv_lst)
        title = "%s" % set_color(title, "server")
        if lang:
            title = add_languages(title, simple_language)
        if item.quality:
            title = "%s %s" % (title, set_color(item.quality, "quality"))
        if item.torrent_info:
            title = "%s [%s]" % (title, item.torrent_info)
        if videolibrary:
            title += ' [%s]' % item.contentChannel

        item.title = title

    # Add to library

    elif c_type == "library_action":
        item.title = '%s' % set_color(item.title, 'library')

    # Season format

    elif c_type == "season":
        item.title = set_color(item.title, "tvshow")

    # Episode format

    elif c_type == "episode":
        season = info["season"]
        episode = info["episode"]
        epi_name = info["episodio_titulo"] if info["episodio_titulo"] else (info["title"] if info["title"] else "Episodio %s" % episode)
        if season and episode:
            title = "%sx%s - %s" % (season, episode, epi_name)
            item.title = set_color(title, "tvshow")
        else:
            try:
                season, episode = scrapertools.find_single_match(item.title, "(\d+)(?:\s)?(?:x|X)(?:\s)?(\d+)")
                item.title = "%sx%s - %s" % (season, episode, item.contentSerieName)
            except:
                pass
            item.title = set_color(item.title, "tvshow")

    # Movie or TVShow format

    elif c_type in ["movie", "tvshow"] or videolibrary:

        if item.unify_extended:
            title = item.title
        else:
            title = info["title"] if c_type == "movie" else (info["title"] if info["title"] else info["tvshowtitle"])
            title = remove_format(title.capitalize())

        if videolibrary:
            new_title.append("%s" % set_library_format(item, title))
        else:
            new_title.append("%s" % (set_color(title, c_type)))

        new_title.append("%s" % (set_color(info["year"], "year")))

        if info["rating"]:
            new_title.append(format_rating(info["rating"]))
        title = " ".join(new_title)
        item.title = title
    item.plot = add_info_plot(item.plot, simple_language, item.quality, vextend)

    item = add_extra_info(item, checks)
    return item


def thumbnail_type(item):
    #logger.info()
    # Se comprueba que tipo de thumbnail se utilizara en findvideos,
    # Poster o Logo del servidor

    thumb_type = config.get_setting('video_thumbnail_type')
    info = item.infoLabels
    if not item.contentThumbnail:
        item.contentThumbnail = item.thumbnail

    if info:
        if info['thumbnail'] != '':
            item.contentThumbnail = info['thumbnail']

        if item.action == 'play':
            if thumb_type == 0:
                if info['thumbnail'] != '':
                    item.thumbnail = info['thumbnail']
            elif thumb_type == 1:
                from core.servertools import get_server_parameters
                server_parameters = get_server_parameters(item.server.lower())
                item.thumbnail = server_parameters.get("thumbnail", item.contentThumbnail)

    return item.thumbnail


from decimal import *

def check_rating(rating):
    # logger.debug("\n\nrating %s" % rating)

    def check_decimal_length(_rating):
        """
       Dejamos que el float solo tenga un elemento en su parte decimal, "7.10" --> "7.1"
       @param _rating: valor del rating
       @type _rating: float
       @return: devuelve el valor modificado si es correcto, si no devuelve None
       @rtype: float|None
       """
        # logger.debug("rating %s" % _rating)

        try:
            # convertimos los deciamles p.e. 7.1
            return "%.1f" % round(_rating, 1)
        except Exception as ex_dl:
            template = "An exception of type %s occured. Arguments:\n%r"
            message = template % (type(ex_dl).__name__, ex_dl.args)
            logger.error(message)
            return None

    def check_range(_rating):
        """
       Comprobamos que el rango de rating sea entre 0.0 y 10.0
       @param _rating: valor del rating
       @type _rating: float
       @return: devuelve el valor si está dentro del rango, si no devuelve None
       @rtype: float|None
       """
        # logger.debug("rating %s" % _rating)
        # fix para comparacion float
        dec = Decimal(_rating)
        if 0.0 <= dec <= 10.0:
            # logger.debug("estoy en el rango!")
            return _rating
        else:
            # logger.debug("NOOO estoy en el rango!")
            return None

    def convert_float(_rating):
        try:
            return float(_rating)
        except ValueError as ex_ve:
            template = "An exception of type %s occured. Arguments:\n%r"
            message = template % (type(ex_ve).__name__, ex_ve.args)
            logger.error(message)
            return None

    if not isinstance(rating, float):
        # logger.debug("no soy float")
        if isinstance(rating, int):
            # logger.debug("soy int")
            rating = convert_float(rating)
        elif isinstance(rating, str):
            # logger.debug("soy str")

            rating = rating.replace("<", "")
            rating = convert_float(rating)

            if rating is None:
                # logger.debug("error al convertir str, rating no es un float")
                # obtenemos los valores de numericos
                new_rating = scrapertools.find_single_match(rating, "(\d+)[,|:](\d+)")
                if len(new_rating) > 0:
                    rating = convert_float("%s.%s" % (new_rating[0], new_rating[1]))

        else:
            logger.error("no se que soy!!")
            # obtenemos un valor desconocido no devolvemos nada
            return None

    if rating:
        rating = check_decimal_length(rating)
        rating = check_range(rating)

    return rating


def set_server_name(title, srv_lst):

    new_title = "Directo"
    for k, v in srv_lst.items():
        if v["name"].lower() in title.lower():
            new_title = '%s' % (v["name"].title())

    return new_title


def detect_content_type(item):
    #logger.info()

    if "library" in item.action:
         return "library_action"
    elif item.action == "play":
        return "server"
    elif item.contentEpisodeNumber:
        return "episode"
    elif item.contentSeason:
        return "season"
    elif item.contentSerieName:
        return "tvshow"
    elif item.contentTitle:
        return "movie"
    elif item.channel == "search":
        return "search"
    else:
        return ""


def set_library_format(item, new_title):
    #logger.info()

    if item.action == 'get_seasons':
        if 'Desactivar' in item.context[1]['title']:
            new_title = '%s' % set_color(new_title, 'update')
        if 'Activar' in item.context[1]['title']:
            new_title = '%s' % set_color(new_title, 'no_update')
    else:
        new_title = '%s' % set_color(new_title, 'library')

    return new_title


def get_languages(lang_data):
    lang = False
    if isinstance(lang_data, list):
        language_list = list()
        for language in lang_data:
            if language != '':
                lang = True
                language_list.append(set_lang(remove_format(language)).upper())
        simple_language = language_list
    else:
        if lang_data != '':
            lang = True
            simple_language = set_lang(lang_data).upper()
        else:
            simple_language = ''

    return simple_language, lang


def format_rating(rating):

    rating_value = check_rating(rating)

    # Asignamos el color dependiendo el puntaje, malo, bueno, muy bueno, en caso de que exista

    if rating_value:
        value = float(rating_value)
        color_rating = "rating_1" if value <= 3 else ("rating_2" if 3 < value <= 7 else "rating_3")
        rating = '%s' % rating_value
    else:
        rating = ''
        color_rating = 'otro'

    rating = '%s' % (set_color(rating, color_rating))

    return rating


def verify_checks(title):
    #logger.info()
    checks = list()

    if '[[I]v[/I]]' in title or '[COLOR limegreen][v][/COLOR]' in title:
        checks.append("visto")
    if title.startswith("[+]") or '[COLOR yellow][+][/COLOR]' in title:
        checks.append("group")

    return checks


def add_extra_info(item, checks):
    #logger.info()

    if item.from_channel and item.channel not in ["news"]:
        from core import channeltools
        channel_parameters = channeltools.get_channel_parameters(item.from_channel)
        item.title = '%s [%s]' % (item.title, channel_parameters['title'])

    if checks:
        if "group" in checks:
            check = "+"
            color_check = "yellow"
        elif "visto" in checks:
            check = u'\u221a'
            color_check = "limegreen"

        item.title = "[COLOR %s][B][%s][/B][/COLOR] %s" % (color_check, check, item.title)

    return item


