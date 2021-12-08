# -*- coding: utf-8 -*-
# ------------------------------------------------------------
# channeltools - Herramientas para trabajar con canales
# ------------------------------------------------------------

from __future__ import absolute_import
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

from . import jsontools
from core.item import Item
from platformcode import config, logger

DEFAULT_UPDATE_URL = "/channels/"
dict_channels_parameters = dict()

""" CACHING CHANNELS PARAMETERS """
alfa_caching = False
alfa_channels = {}
kodi = True
try:
    import xbmcgui
    import json
    window = xbmcgui.Window(10000)                                              # Home
except:
    kodi = False


def has_attr(channel_name, attr):
    """
    Booleano para determinar si un canal tiene una def en particular

    @param channel_name: nombre del canal a verificar
    @type channel_name: str
    @param attr: nombre de la función a verificar
    @type attr: str

    @return: True si hay función o False si no la hay, None si no hay canal
    @rtype: bool
    """
    existe = False
    from core import filetools
    channel_file = filetools.join(config.get_runtime_path(), 'channels', channel_name + ".py")
    channel = None
    itemlist = []

    if filetools.exists(channel_file):
        try:
            channel = __import__('channels.%s' % channel_name, None, None, ["channels.%s" % channel_name])
            if hasattr(channel, attr):
                existe = True
        except:
            pass
    else:
        return None

    return existe


def get_channel_attr(channel_name, attr, item):
    """
    Ejecuta una función específica de un canal y devuelve su salida.
    Además devuelve None si ocurre un error como canal o función inexistentes, errores de import, etc

    @param channel_name: nombre del canal
    @type channel_name: str
    @param attr: función a ejecutar
    @type attr: str
    @param item: item con el que invocar a la función [requerido]
    @type item: item

    @return: según la función, generalmente list, o None si ocurre un error
    @rtype: list, any, None
    """
    from core import filetools
    from channels import autoplay
    channel_file = filetools.join(config.get_runtime_path(), 'channels', channel_name + ".py")
    channel = None
    itemlist = None

    def disabled_autoplay_init(channel, list_servers, list_quality, reset=False):
        return False
    def disabled_autoplay_show_option(channel, itemlist, text_color='yellow', thumbnail=None, fanart=None):
        return False
    def disabled_autoplay_start(itemlist, item):
        return False

    autoplay.init = disabled_autoplay_init
    autoplay.show_option = disabled_autoplay_show_option
    autoplay.start = disabled_autoplay_start

    if filetools.exists(channel_file):
        channel = __import__('channels.%s' % channel_name, globals(), locals(), ["channels.%s" % channel_name])
        if hasattr(channel, attr):
            logger.info("Ejecutando método '{}' del canal '{}'".format(attr, channel_name))
            itemlist = getattr(channel, attr)(item)
        else:
            logger.error("ERROR: El canal '{}' no tiene el atributo '{}'".format(channel_name, attr))
            return itemlist
    else:
        logger.error("ERROR: El canal '{}' no existe".format(channel_name))
        return itemlist
    return itemlist


def is_adult(channel_name):
    channel_parameters = get_channel_parameters(channel_name)
    logger.info("channel {}.is adult={}".format(channel_name, channel_parameters["adult"]))
    return channel_parameters["adult"]


def is_enabled(channel_name):
    logger.info("channel_name=" + channel_name)
    return get_channel_parameters(channel_name)["active"] and get_channel_setting("enabled", channel=channel_name,
                                                                                  default=True)


def get_channel_parameters(channel_name):
    from . import filetools
    global dict_channels_parameters

    if channel_name not in dict_channels_parameters:
        try:
            channel_parameters = get_channel_json(channel_name)
            # logger.debug(channel_parameters)
            if channel_parameters:
                # cambios de nombres y valores por defecto
                channel_parameters["title"] = channel_parameters.pop("name")
                channel_parameters["channel"] = channel_parameters.pop("id")

                # si no existe el key se declaran valor por defecto para que no de fallos en las funciones que lo llaman
                channel_parameters["update_url"] = channel_parameters.get("update_url", DEFAULT_UPDATE_URL)
                channel_parameters["language"] = channel_parameters.get("language", ["all"])
                channel_parameters["adult"] = channel_parameters.get("adult", False)
                channel_parameters["active"] = channel_parameters.get("active", False)
                channel_parameters["include_in_global_search"] = channel_parameters.get("include_in_global_search",
                                                                                        False)
                channel_parameters["categories"] = channel_parameters.get("categories", list())

                channel_parameters["thumbnail"] = channel_parameters.get("thumbnail", "")
                channel_parameters["banner"] = channel_parameters.get("banner", "")
                channel_parameters["fanart"] = channel_parameters.get("fanart", "")
                channel_parameters["req_assistant"] = channel_parameters.get("req_assistant", "")

                # Imagenes: se admiten url y archivos locales dentro de "resources/images"
                if channel_parameters.get("thumbnail") and "://" not in channel_parameters["thumbnail"]:
                    channel_parameters["thumbnail"] = filetools.join(config.get_runtime_path(), "resources", "media",
                                                                   "channels", "thumb", channel_parameters["thumbnail"])
                if channel_parameters.get("banner") and "://" not in channel_parameters["banner"]:
                    channel_parameters["banner"] = filetools.join(config.get_runtime_path(), "resources", "media",
                                                                "channels", "banner", channel_parameters["banner"])
                if channel_parameters.get("fanart") and "://" not in channel_parameters["fanart"]:
                    channel_parameters["fanart"] = filetools.join(config.get_runtime_path(), "resources", "media",
                                                                "channels", "fanart", channel_parameters["fanart"])

                # Obtenemos si el canal tiene opciones de configuración
                channel_parameters["has_settings"] = False
                if 'settings' in channel_parameters:
                    for s in channel_parameters['settings']:
                        if 'id' in s:
                            if s['id'] == "include_in_global_search":
                                channel_parameters["include_in_global_search"] = True
                            elif s['id'] == "filter_languages":
                                channel_parameters["filter_languages"] = s.get('lvalues',[])
                            if (s.get('enabled', False) and s.get('visible', False)):
                                channel_parameters["has_settings"] = True

                    del channel_parameters['settings']

                dict_channels_parameters[channel_name] = channel_parameters

            else:
                # para evitar casos donde canales no están definidos como configuración
                # lanzamos la excepcion y asi tenemos los valores básicos
                raise Exception

        except Exception as ex:
            logger.error(channel_name + ".json error \n%s" % ex)
            channel_parameters = dict()
            channel_parameters["channel"] = ""
            channel_parameters["adult"] = False
            channel_parameters['active'] = False
            channel_parameters["language"] = ""
            channel_parameters["update_url"] = DEFAULT_UPDATE_URL
            return channel_parameters

    return dict_channels_parameters[channel_name]


def get_channel_json(channel_name):
    # logger.info("channel_name=" + channel_name)
    from . import filetools
    channel_json = None
    try:
        channel_path = filetools.join(config.get_runtime_path(), "channels", channel_name + ".json")
        if filetools.isfile(channel_path):
            # logger.info("channel_data=" + channel_path)
            channel_json = jsontools.load(filetools.read(channel_path))
            # logger.info("channel_json= %s" % channel_json)

    except Exception as ex:
        template = "An exception of type %s occured. Arguments:\n%r"
        message = template % (type(ex).__name__, ex.args)
        logger.error("%s: %s" % (channel_name, message))

    return channel_json


def get_channel_controls_settings(channel_name):
    # logger.info("channel_name=" + channel_name)
    dict_settings = {}

    list_controls = get_channel_json(channel_name).get('settings', list())

    for c in list_controls:
        if 'id' not in c or 'type' not in c or 'default' not in c:
            # Si algun control de la lista  no tiene id, type o default lo ignoramos
            continue

        # new dict with key(id) and value(default) from settings
        dict_settings[c['id']] = c['default']

    return list_controls, dict_settings


def get_channel_setting(name, channel, default=None, caching_var=True):
    global alfa_caching, alfa_channels
    from . import filetools
    """
    Retorna el valor de configuracion del parametro solicitado.

    Devuelve el valor del parametro 'name' en la configuracion propia del canal 'channel'.

    Busca en la ruta \addon_data\plugin.video.alfa\settings_channels el archivo channel_data.json y lee
    el valor del parametro 'name'. Si el archivo channel_data.json no existe busca en la carpeta channels el archivo
    channel.json y crea un archivo channel_data.json antes de retornar el valor solicitado. Si el parametro 'name'
    tampoco existe en el el archivo channel.json se devuelve el parametro default.


    @param name: nombre del parametro
    @type name: str
    @param channel: nombre del canal
    @type channel: str
    @param default: valor devuelto en caso de que no exista el parametro name
    @type default: any

    @return: El valor del parametro 'name'
    @rtype: any

    """
    file_settings = filetools.join(config.get_data_path(), "settings_channels", channel + "_data.json")
    dict_settings = {}
    dict_file = {}
    
    if kodi and caching_var:
        alfa_caching = bool(window.getProperty("alfa_caching"))
        alfa_channels = json.loads(window.getProperty("alfa_channels"))
    if alfa_caching and caching_var and alfa_channels.get(channel):
        dict_settings = alfa_channels[channel].copy()
        if dict_settings.get(name, ''):
            dict_settings[name] = config.decode_var(dict_settings[name])
            #logger.error('%s, %s: A: %s - D: %s' % (name, channel, [alfa_channels[channel][name]], [config.decode_var(dict_settings[name])]))

    elif filetools.exists(file_settings):
        # Obtenemos configuracion guardada de ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            if isinstance(dict_file, dict) and 'settings' in dict_file:
                dict_settings = dict_file['settings']
                if alfa_caching and caching_var:
                    alfa_channels[channel] = dict_settings.copy()
                    window.setProperty("alfa_channels", json.dumps(alfa_channels))
        except EnvironmentError:
            logger.error("ERROR al leer el archivo: %s, parámetro: %s" % (file_settings, name))
            logger.error(filetools.file_info(file_settings))

    if not dict_settings or name not in dict_settings:
        # Obtenemos controles del archivo ../channels/channel.json
        try:
            list_controls, default_settings = get_channel_controls_settings(channel)
        except:
            default_settings = {}

        if name in default_settings:  # Si el parametro existe en el channel.json creamos el channel_data.json
            default_settings.update(dict_settings)
            dict_settings = default_settings
            if alfa_caching and caching_var:
                alfa_channels[channel] = dict_settings.copy()
                window.setProperty("alfa_channels", json.dumps(alfa_channels))
            dict_file['settings'] = dict_settings
            # Creamos el archivo ../settings/channel_data.json
            json_data = jsontools.dump(dict_file)
            if not filetools.write(file_settings, json_data, silent=True):
                logger.error("ERROR al salvar el parámetro: %s en el archivo: %s" % (name, file_settings))
                logger.error(filetools.file_info(file_settings))

    # Devolvemos el valor del parametro local 'name' si existe, si no se devuelve default
    return dict_settings.get(name, default)


def set_channel_setting(name, value, channel):
    global alfa_caching, alfa_channels
    from . import filetools
    """
    Fija el valor de configuracion del parametro indicado.

    Establece 'value' como el valor del parametro 'name' en la configuracion propia del canal 'channel'.
    Devuelve el valor cambiado o None si la asignacion no se ha podido completar.

    Si se especifica el nombre del canal busca en la ruta \addon_data\plugin.video.alfa\settings_channels el
    archivo channel_data.json y establece el parametro 'name' al valor indicado por 'value'.
    Si el parametro 'name' no existe lo añade, con su valor, al archivo correspondiente.

    @param name: nombre del parametro
    @type name: str
    @param value: valor del parametro
    @type value: str
    @param channel: nombre del canal
    @type channel: str

    @return: 'value' en caso de que se haya podido fijar el valor y None en caso contrario
    @rtype: str, None

    """
    # Creamos la carpeta si no existe
    if not filetools.exists(filetools.join(config.get_data_path(), "settings_channels")):
        filetools.mkdir(filetools.join(config.get_data_path(), "settings_channels"))

    file_settings = filetools.join(config.get_data_path(), "settings_channels", channel + "_data.json")
    dict_settings = {}

    dict_file = None

    if kodi:
        alfa_caching = bool(window.getProperty("alfa_caching"))
        alfa_channels = json.loads(window.getProperty("alfa_channels"))
    if alfa_caching and alfa_channels.get(channel):
        dict_settings = alfa_channels[channel].copy()
    
    elif filetools.exists(file_settings):
        # Obtenemos configuracion guardada de ../settings/channel_data.json
        try:
            dict_file = jsontools.load(filetools.read(file_settings))
            dict_settings = dict_file.get('settings', {})
        except EnvironmentError:
            logger.error("ERROR al leer el archivo: %s, parámetro: %s" % (file_settings, name))
            logger.error(filetools.file_info(file_settings))

    dict_settings[name] = value
    if alfa_caching:
        alfa_caching = bool(window.getProperty("alfa_caching"))
        if alfa_caching:
            alfa_channels[channel] = dict_settings.copy()
            window.setProperty("alfa_channels", json.dumps(alfa_channels))
        else:
            alfa_channels = {}
            window.setProperty("alfa_channels", json.dumps(alfa_channels))

    # comprobamos si existe dict_file y es un diccionario, sino lo creamos
    if dict_file is None or not dict_file:
        dict_file = {}

    dict_file['settings'] = dict_settings

    # Creamos el archivo ../settings/channel_data.json
    json_data = jsontools.dump(dict_file)
    if not filetools.write(file_settings, json_data, silent=True):
        logger.error("ERROR al salvar el parámetro: %s en el archivo: %s" % (name, file_settings))
        logger.error(filetools.file_info(file_settings))
        return None

    return value
