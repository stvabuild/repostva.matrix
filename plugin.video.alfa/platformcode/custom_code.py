# -*- coding: utf-8 -*-
# --------------------------------------------------------------------------------
# Updater (kodi)
# --------------------------------------------------------------------------------

#from builtins import str
import sys
PY3 = False
if sys.version_info[0] >= 3: PY3 = True; unicode = str; unichr = chr; long = int

import traceback
import xbmc
import xbmcaddon
import xbmcgui
import threading
import subprocess
import time
import os

from platformcode import config, logger, platformtools

from core import jsontools
from core import filetools
from core.item import Item
from lib.alfa_assistant import execute_binary_from_alfa_assistant

json_data_file_name = 'custom_code.json'
ADDON_NAME = 'plugin.video.alfa'
ADDON_PATH = config.get_runtime_path()
ADDON_USERDATA_PATH = config.get_data_path()
ADDON_USERDATA_BIN_PATH = filetools.join(ADDON_USERDATA_PATH, 'bin')
ADDON_VERSION = config.get_addon_version(with_fix=False, from_xml=True)
ADDON_CUSTOMCODE_JSON = filetools.join(ADDON_PATH, json_data_file_name)
ADDON_PLATFORM = config.get_system_platform()


def init():
    logger.info()

    """
    Todo el código añadido al add-on se borra con cada actualización.  Esta función permite restaurarlo automáticamente con cada actualización.  Esto permite al usuario tener su propio código, bajo su responsabilidad, y restaurarlo al add-on cada vez que se actualiza.
    
    El mecanismo funciona copiando el contenido de la carpeta-arbol "./userdata/addon_data/plugin.video.alfa/custom_code/..." sobre
    las carpetas de código del add-on.  No verifica el contenido, solo vuelca(reemplaza) el contenido de "custom_code".
    
    El usuario almacenará en las subcarpetas de "custom_code" su código actualizado y listo para ser copiado en cualquier momento.
    Si no se desea que copie algo, simplemente se borra de "custom_code" y ya no se copiará en la próxima actualización.
    
    Los pasos que sigue esta función, son los siguientes:
    
    1.- La función se llama desde videolibrary_service.py, desde la función inicial:
            # Copia Custom code a las carpetas de Alfa desde la zona de Userdata
            from platformcode import custom_code
            custom_code.init()
            
    2.- En el inicio de Kodi, comprueba si existe la carpeta "custom_code" en "./userdata/addon_data/plugin.video.alfa/".  
        Si no existe, la crea y sale sin más, dando al ususario la posibilidad de copiar sobre esa estructura su código, 
        y que la función la vuelque sobre el add-on en el próximo inicio de Kodi.
        
    3.- En el siguiente inicio de Kodi, comprueba si existe el custom_code.json en la carpeta root del add-on.
        Si no existe, lo crea con el número de versión del add-on vacío, para permitir que se copien los archivos en esta pasada.
        
    4.- Verifica que el número de versión del add-on es diferente de el de custom_code.json.  Si es la misma versión, 
        se sale porque ya se realizo la copia anteriormente.
        Si la versión es distinta, se realiza el volcado de todos los archivos de la carpeta-árbol "custom_code" sobre el add-on.
        Si la carpeta de destino no existe, dará un error y se cancelará la copia.  Se considera que no tienen sentido nuevas carpetas.
        
    5.- Si la copia ha terminado con éxito, se actualiza el custom_code.json con el número de versión del add-on,
        para que en inicios sucesivos de Kodi no se realicen las copias, hasta que el add-on cambie de versión.
        En el número de versión del add-on no se considera el número de fix.
        
    Tiempos:    Copiando 7 archivos de prueba, el proceso ha tardado una décima de segundo.
    """

    try:
        #Limpiamos los mensajes de ayuda obsoletos y restauramos los que tienen "version": True.  Por cada nueva versión
        if not filetools.exists(ADDON_CUSTOMCODE_JSON):
            from platformcode import help_window
            help_window.clean_watched_new_version()
        
        #Se realizan algunas funciones con cada nueva versión de Alfa
        if not filetools.exists(ADDON_CUSTOMCODE_JSON):
            config.set_setting('cf_assistant_ua', '')                   # Se limpia CF_UA. Mejora de rendimiento en httptools CF
            
        #Se verifica si están bien las rutas a la videoteca
        config.verify_directories_created()
        
        #Comprime la BD de cache de TMDB para evitar que crezca demasiado
        bd_tmdb_maintenance()
        if config.get_setting('tmdb_cache_expire', default=4) == 4:
            config.set_setting('tmdb_cache_expire', 2)

        #Borra el .zip de instalación de Alfa de la carpeta Packages, por si está corrupto, y que así se pueda descargar de nuevo
        #version = 'plugin.video.alfa-%s.zip' % ADDON_VERSION
        #filetools.remove(filetools.join('special://home', 'addons', 'packages', version), True)

        #Verifica si es necesario instalar script.alfa-update-helper
        verify_script_alfa_update_helper()
        
        #Borrar contenido de carpeta de Torrents y de Subtitles
        filetools.rmdirtree(filetools.join(config.get_videolibrary_path(), 'temp_torrents_arch'), silent=True)
        filetools.rmdirtree(filetools.join(config.get_videolibrary_path(), 'temp_torrents_Alfa'), silent=True)
        subtitle_path = config.get_kodi_setting("subtitles.custompath")
        if subtitle_path and filetools.exists(subtitle_path):
            for file in filetools.listdir(subtitle_path):
                if not file.endswith('.srt'): continue
                file_path = filetools.join(subtitle_path, file)
                ret = filetools.remove(file_path, silent=True)
                if not ret: logger.error('ERROR on REMOVING subtitle: ' + file_path)

        #Verifica si Kodi tiene algún achivo de Base de Datos de Vídeo de versiones anteriores, entonces los borra
        verify_Kodi_video_DB()
        
        #Verifica si la Base de Datos de Vídeo tiene la fuente de CINE con useFolderNames=1
        try:
            threading.Thread(target=set_Kodi_video_DB_useFolderNames).start()   # Creamos un Thread independiente por si la DB está Scanning
            time.sleep(1)                                                       # Dejamos terminar la inicialización...
        except:                                                                 # Si hay problemas de threading, nos vamos
            logger.error(traceback.format_exc())
        
        #LIBTORRENT: se descarga el binario de Libtorrent cada vez que se actualiza Alfa
        update_libtorrent()
        
        #TORREST: Modificaciones temporales
        if xbmc.getCondVisibility('System.HasAddon("plugin.video.torrest")'):
            try:
                __settings__ = xbmcaddon.Addon(id="plugin.video.torrest")
                if __settings__.getSetting("s:check_available_space") == 'true':
                    __settings__.setSetting("s:check_available_space", "false") # No comprobar espacio disponible hasta que lo arreglen
                #if not filetools.exists(filetools.join(config.get_data_path(), "quasar.json")) \
                #    and not config.get_setting('addon_quasar_update', default=False):
                #    question_update_external_addon("torrest")
            except:
                pass

        #QUASAR: Preguntamos si se hacen modificaciones a Quasar
        if not filetools.exists(filetools.join(config.get_data_path(), "quasar.json")) \
                    and not config.get_setting('addon_quasar_update', default=False):
            question_update_external_addon("quasar")
        
        #QUASAR: Hacemos las modificaciones a Quasar, si está permitido, y si está instalado
        if config.get_setting('addon_quasar_update', default=False) or \
                    (filetools.exists(filetools.join(config.get_data_path(), \
                    "quasar.json")) and xbmc.getCondVisibility('System.HasAddon("plugin.video.quasar")')):
            if not update_external_addon("quasar"):
                platformtools.dialog_notification("Actualización Quasar", "Ha fallado. Consulte el log")
        
        #Existe carpeta "custom_code" ? Si no existe se crea y se sale
        custom_code_dir = filetools.join(ADDON_USERDATA_PATH, 'custom_code')
        custom_code_json_path = ADDON_PATH
        custom_code_json = ADDON_CUSTOMCODE_JSON
        if not filetools.exists(custom_code_dir):
            create_folder_structure(custom_code_dir)
        #Existe "custom_code.json" ? Si no existe se crea
        if not filetools.exists(custom_code_json):
            create_json(custom_code_json_path)
        #Se verifica si la versión del .json y del add-on son iguales.  Si es así se sale.  Si no se copia "custom_code" al add-on
        verify_copy_folders(custom_code_dir, custom_code_json_path)
        
        #Si se han quedado "colgadas" descargas con archivos .RAR, se intenta identificarlos y reactivar el UnRar
        reactivate_unrar(init=True, mute=True)
        
        #Inicia un rastreo de vídeos decargados desde .torrent: marca los VISTOS y elimina los controles de los BORRADOS
        from servers.torrent import mark_torrent_as_watched
        try:
            threading.Thread(target=mark_torrent_as_watched).start()            # Creamos un Thread independiente, hasta el fin de Kodi
            time.sleep(2)                                                       # Dejamos terminar la inicialización...
        except:                                                                 # Si hay problemas de threading, nos vamos
            logger.error(traceback.format_exc())

        #Ejecuta la sobrescritura de la videoteca para los canales seleccionados
        reset_videolibrary_by_channel()
        clean_videolibrary_unused_channels()

    except:
        logger.error(traceback.format_exc())


def bd_tmdb_maintenance():
    try:
        import sqlite3
        
        fname = filetools.join(config.get_data_path(), "alfa_db.sqlite")
        
        if filetools.exists(fname):
            conn = sqlite3.connect(fname)
            conn.execute("VACUUM")
            conn.close()
            logger.info('TMDB DB compacted')
    except:
        logger.error(traceback.format_exc(1))


def marshal_check():
    import platform
    
    try:
        python_ver = platform.python_version().split('.')
        if len(python_ver) == 3:
            python_ver = '_%s_%s' % (str(python_ver[0]), str(python_ver[1]).zfill(2))
        else:
            python_ver = '_0_00'
        marshal_modules = ['lib/alfaresolver_py3', 'core/proxytools_py3']
        for module in marshal_modules:
            path = filetools.join(ADDON_PATH, filetools.dirname(module))
            path_list = sorted(filetools.listdir(path))
            library = filetools.dirname(module).rstrip('/')
            module_name = filetools.basename(module)
            for alt_module in path_list:
                if python_ver not in alt_module:
                    continue
                if module_name not in alt_module:
                    continue
                if alt_module == module_name + '.py':
                    continue
                try:
                    alt_module_path = '%s.%s' % (library, alt_module.rstrip('.py'))
                    spec = __import__(alt_module_path, None, None, [alt_module_path])
                    if not spec:
                        raise
                except Exception as e:
                    logger.info('marshal_check ERROR in %s: %s' % (alt_module, str(e)), force=True)
                    continue
                filetools.copy(filetools.join(path, alt_module), filetools.join(path, module_name + '.py'), silent=True)
                logger.info('marshal_check FOUND: %s' % alt_module, force=True)
                break
            else:
                logger.info('marshal_check NOT FOUND: %s%s.py' % (module_name, python_ver), force=True)
    except:
        logger.error(traceback.format_exc(1))


def verify_script_alfa_update_helper(silent=True):
    logger.info()
    
    import json
    from core import ziptools
    from core import httptools
    from platformcode import xbmc_videolibrary
    
    addons_path = filetools.translatePath("special://home/addons")
    repos_dir = 'downloads/repos/'
    alfa_repo = ['repository.alfa-addon', '1.0.6', '*']
    alfa_helper = ['script.alfa-update-helper', '0.0.6', '*']
    torrest_repo = ['repository.github', '0.0.6', '*']
    torrest_addon = 'plugin.video.torrest'
    futures_script = ['%sscript.module.futures' % repos_dir, '2.2.1', 'PY2']
    
    try:
        versiones = config.get_versions_from_repo()
    except:
        versiones = {}
        logger.error(traceback.format_exc())
    if not versiones:
        return
    
    repos = [futures_script, alfa_repo, torrest_repo]
    # Comprobamos si hay acceso a Github
    if not 'github' in versiones.get('url', '') or bool(xbmc.getCondVisibility("System.HasAddon(%s)" % alfa_helper[0])):
        repos += [alfa_helper]

    for addon_name, version, py in repos:
        if py != '*':
            if py == 'PY2' and PY3:
                continue
            if py == 'PY3' and not PY3:
                continue
        
        if repos_dir in addon_name:
            addonid = addon_name.replace(repos_dir, '')
            path_folder = repos_dir[:-1]
        else:
            addonid = addon_name
            path_folder = addonid
        
        new_version = versiones.get(addonid, version)
        package = addonid + '-%s.zip' % new_version
        filetools.remove(filetools.join('special://home', 'addons', 'packages', package), silent=silent)
        updated = bool(xbmc.getCondVisibility("System.HasAddon(%s)" % addonid))
        if updated:
            installed_version = xbmc.getInfoLabel('System.AddonVersion(%s)' % addonid)
            if installed_version != new_version:
                updated = False
            
        if not updated:
            url_repo = '%s%s/%s' % (versiones.get('url', ''), path_folder, package)
            response = httptools.downloadpage(url_repo, ignore_response_code=True, alfa_s=True, json_to_utf8=False)
            if response.code == 200:
                zip_data = response.data
                pkg_updated = filetools.join(addons_path, 'packages', package)
                res = filetools.write(pkg_updated, zip_data, mode='wb')
                
                # Si el .zip es correcto los extraemos e instalamos
                try:
                    unzipper = ziptools.ziptools()
                    unzipper.extract(pkg_updated, addons_path, silent=silent)
                except:
                    xbmc.executebuiltin('Extract("%s", "%s")' % (pkg_updated, addons_path))
                    time.sleep(1)

                logger.info("Installing %s" % package)
                try:
                    xbmc.executebuiltin('UpdateLocalAddons')
                    time.sleep(2)
                    method = "Addons.SetAddonEnabled"
                    xbmc.executeJSONRPC(
                        '{"jsonrpc": "2.0", "id":1, "method": "%s", "params": {"addonid": "%s", "enabled": true}}' % (method, addonid))
                except:
                    logger.error(traceback.format_exc())


    if versiones.get('addons_db', ''):
        
        repos = [(alfa_repo[0], alfa_repo[0]), (alfa_repo[0], ADDON_NAME), (alfa_repo[0], alfa_helper[0]), \
                    (torrest_repo[0], torrest_repo[0]), (torrest_repo[0], torrest_addon), \
                    ('repository.xbmc.org', futures_script[0].replace(repos_dir, ''))]
        try:
            for repo, addon in repos:
                sql = 'update installed set origin = "%s" where addonID = "%s" and origin <> "%s"' % (repo, addon, repo)
                nun_records, records = xbmc_videolibrary.execute_sql_kodi(sql, silent=silent, file_db=versiones['addons_db'])
        except:
            logger.error(traceback.format_exc())
    

    addonid = ADDON_NAME
    new_version = versiones.get(addonid, ADDON_VERSION)
    updated = bool(xbmc.getCondVisibility("System.HasAddon(%s)" % addonid))
    if updated:
        if ADDON_VERSION != new_version:
            def check_alfa_version():
                logger.info(new_version)
                xbmc.executebuiltin('UpdateAddonRepos')
                for x in range(40):
                    addon_version = config.get_addon_version(with_fix=False, from_xml=True)
                    if addon_version == new_version: break
                    time.sleep(2)
                if addon_version != new_version:
                    logger.info("Notifying obsolete version %s ==> %s" % (addon_version, new_version), force=True)
                    platformtools.dialog_notification("Alfa: versión oficial: [COLOR hotpink][B]%s[/B][/COLOR]" % new_version, \
                            "[COLOR yellow]Tienes una versión obsoleta: [B]%s[/B][/COLOR]" % addon_version)
            try:
                threading.Thread(target=check_alfa_version).start()
                time.sleep(1)
            except:
                logger.error(traceback.format_exc())


def install_alfa_now(silent=True):
    logger.info()
    import json
    from core import ziptools
    from core import httptools

    try:
        versiones = config.get_versions_from_repo()
    except:
        versiones = {}
        logger.error(traceback.format_exc())
    if not versiones:
        return
    
    addons_path = filetools.translatePath("special://home/addons")
    alfa_addon = ['plugin.video.alfa', '3.4.2', '*']
    addonid = alfa_addon[0]
    new_version = versiones.get(addonid, alfa_addon[1])
    package = addonid + '-%s.zip' % new_version

    logger.info("Downloading %s" % package)
    url = '%s%s/%s' % (versiones.get('url', ''), addonid, package)
    response = httptools.downloadpage(url, ignore_response_code=True, alfa_s=True, json_to_utf8=False)
    if response.code == 200:
        zip_data = response.data
        pkg_updated = filetools.join(addons_path, 'packages', package)
        res = filetools.write(pkg_updated, zip_data, mode='wb')
        
        if res and filetools.exists(pkg_updated):
            logger.info("backing and removing installed version... %s" % package)
            backup_path = filetools.join(addons_path, "temp", addonid)
            if filetools.exists(backup_path):
                res = filetools.rmdirtree(backup_path, silent=silent)
                if not res: return
            time.sleep(3)
            if not filetools.exists(backup_path):
                filetools.copy(ADDON_PATH, backup_path)
                time.sleep(3)
                res = filetools.rmdirtree(ADDON_PATH, silent=silent)
                time.sleep(3)
                if filetools.exists(ADDON_PATH):
                    logger.error("backing and removing installed version FAILED ... %s" % package)
                    filetools.copy(backup_path, ADDON_PATH)
                    time.sleep(3)
                    return
            else:
                logger.error("backing and removing installed version FAILED ... %s" % package)
                return
        else:
            logger.error("Unable to download %s" % package)
            return

        # Si el .zip es correcto los extraemos e instalamos
        try:
            unzipper = ziptools.ziptools()
            unzipper.extract(pkg_updated, addons_path, silent=silent)
            time.sleep(3)
        except:
            try:
                xbmc.executebuiltin('Extract("%s", "%s")' % (pkg_updated, addons_path))
                time.sleep(3)
            except:
                filetools.copy(backup_path, ADDON_PATH)
                time.sleep(3)
                return

        logger.info("Installing %s" % package)
        xbmc.executebuiltin('UpdateLocalAddons')
        time.sleep(2)
        method = "Addons.SetAddonEnabled"
        xbmc.executeJSONRPC(
            '{"jsonrpc": "2.0", "id":1, "method": "%s", "params": {"addonid": "%s", "enabled": true}}' % (method, addonid))
        profile = json.loads(xbmc.executeJSONRPC('{"jsonrpc": "2.0", "id":1, "method": "Profiles.GetCurrentProfile"}'))
        logger.info("Reloading Profile...")
        user = profile["result"]["label"]
        xbmc.executebuiltin('LoadProfile(%s)' % user)


def create_folder_structure(custom_code_dir):
    logger.info()

    #Creamos todas las carpetas.  La importante es "custom_code".  Las otras sirven meramente de guía para evitar errores de nombres...
    filetools.mkdir(custom_code_dir)
    filetools.mkdir(filetools.join(custom_code_dir, 'channels'))
    filetools.mkdir(filetools.join(custom_code_dir, 'core'))
    filetools.mkdir(filetools.join(custom_code_dir, 'lib'))
    filetools.mkdir(filetools.join(custom_code_dir, 'platformcode'))
    filetools.mkdir(filetools.join(custom_code_dir, 'resources'))
    filetools.mkdir(filetools.join(custom_code_dir, 'servers'))

    return


def create_json(custom_code_json_path, json_name=json_data_file_name):
    logger.info()

    #Guardamaos el json con la versión de Alfa vacía, para permitir hacer la primera copia
    json_data_file = filetools.join(custom_code_json_path, json_name)
    if filetools.exists(json_data_file):
        filetools.remove(json_data_file)
    result = filetools.write(json_data_file, jsontools.dump({"addon_version": ""}))
    
    return


def verify_copy_folders(custom_code_dir, custom_code_json_path):
    logger.info()
    
    #verificamos si es una nueva versión de Alfa instalada o era la existente.  Si es la existente, nos vamos sin hacer nada
    update = None
    json_data_file = ADDON_CUSTOMCODE_JSON
    try:
        json_data = jsontools.load(filetools.read(json_data_file))
        if not json_data or not 'addon_version' in json_data: 
            create_json(custom_code_json_path)
            json_data = jsontools.load(filetools.read(json_data_file))
            if not json_data:
                return
    
        if ADDON_VERSION != json_data.get('addon_version', ''):
            update = 'version'
    except:
        logger.error(traceback.format_exc())
        json_data['addon_version'] = ADDON_VERSION
        if not filetools.write(json_data_file, jsontools.dump(json_data)):
            return
    
    #Ahora copiamos los archivos desde el área de Userdata, Custom_code, sobre las carpetas del add-on
    if update == 'version':
        for root, folders, files in filetools.walk(custom_code_dir):
            for file in files:
                input_file = filetools.join(root, file)
                output_file = input_file.replace(custom_code_dir, custom_code_json_path)
                filetools.copy(input_file, output_file, silent=True)
    
    if init_version(json_data):
        json_data['init_version'] = 'true'
        update = 'init'
    
    #Guardamaos el json con la versión actual de Alfa, para no volver a hacer la copia hasta la nueva versión
    if update:
        json_data['addon_version'] = ADDON_VERSION
        filetools.write(json_data_file, jsontools.dump(json_data))

    return


def init_version(json_data):
    
    try:
        ret = False
        if json_data.get('init_version'): return ret
        
        if config.get_setting('alfa_version', default='') == ADDON_VERSION:
            logger.info('### Reinstalación de versión Alfa %s' % ADDON_VERSION, force=True)
            return True

        kodi = config.get_platform(full_version=True)
        kodi = ',k%s' % str(kodi.get('num_version')).split('.')[0]
        
        assistant = ''
        if ADDON_PLATFORM in ['android', 'atv2']:
            assistant = config.get_setting('assistant_binary', default=False)
            if assistant and assistant != True:
                assistant = ',%s' % assistant
            elif assistant == True:
                assistant = ''
                from core import servertools
                torrent_json = servertools.get_server_json('torrent').get('clients', [])
                for client_block in torrent_json:
                    for client, value in list(client_block.items()):
                        if client != 'id': continue
                        if xbmc.getCondVisibility('System.HasAddon("%s")' % value):
                            assistant = ',AstOT'
                            if 'elementum' in value:
                                assistant = ',AstEL'
                                break
                    if assistant:
                        break
            else:
                assistant = ''
                if filetools.exists(filetools.join(ADDON_USERDATA_PATH, 'alfa-mobile-assistant.version')):
                    version = filetools.read(filetools.join(ADDON_USERDATA_PATH, 'alfa-mobile-assistant.version')).split('.')
                    if len(version) == 3:
                        assistant = ',Ast%s' % version[1]

        try:
            if not PY3: from lib import alfaresolver
            else: from lib import alfaresolver_py3 as alfaresolver
            threading.Thread(target=alfaresolver.frequency_count, args=(Item(), \
                        [ADDON_VERSION, ADDON_PLATFORM + kodi + assistant])).start()
            config.set_setting('alfa_version', ADDON_VERSION)
            ret = True
        except:
            logger.error(traceback.format_exc())
    
    except:
        logger.error(traceback.format_exc())
    
    return ret


def question_update_external_addon(addon_name):
    logger.info(addon_name)
    
    #Verificamos que el addon está instalado
    stat = False
    if xbmc.getCondVisibility('System.HasAddon("plugin.video.%s")' % addon_name):
        #Si es la primera vez que se pregunta por la actualización del addon externo, recogemos la respuesta,  
        # guardaos un .json en userdat/alfa para no volver a preguntar otra vez, y se actualiza el setting en Alfa.
        stat = platformtools.dialog_yesno('Actualización de Torrest/Quasar', '¿Quiere que actualicemos Torrest/Quasar para que sea compatible con las últimas versiones de Kodi? (recomendado: SÍ)', '', 'Si actualiza Torrest/Quasar, reinicie Kodi en un par de minutos')

        #Con la respuesta actualizamos la variable en Alfa settings.xml.  Se puede cambiar en Ajustes de Alfa, Otros
        if stat:
            config.set_setting('addon_quasar_update', True)
        else:
            config.set_setting('addon_quasar_update', False)
            
        #Creamos un .json en userdata para no volver a preguntar otra vez
        create_json(config.get_data_path(), "%s.json" % addon_name)
    
    return stat


def update_external_addon(addon_name):
    logger.info(addon_name)
    
    try:
        #Verificamos que el addon está instalado
        if xbmc.getCondVisibility('System.HasAddon("plugin.video.%s")' % addon_name):
            #Path de actualizaciones de Alfa
            alfa_addon_updates_mig = filetools.join(ADDON_PATH, "lib")
            alfa_addon_updates = filetools.join(alfa_addon_updates_mig, addon_name)
            
            #Está el addon activo?
            try:
                __settings__ = xbmcaddon.Addon(id="plugin.video." + addon_name)
            except:
                logger.error('Addon %s desactivado' % (addon_name.upper()))
                return True

            #Path de destino en addon externo
            if addon_name.lower() in ['quasar', 'elementum']:
                addon_path_root = filetools.translatePath(__settings__.getAddonInfo('Path'))
                addon_path_mig = filetools.join(addon_path_root, filetools.join("resources", "site-packages"))
                addon_path = filetools.join(addon_path_mig, addon_name)
            else:
                addon_path_root = ''
                addon_path_mig = ''
                addon_path = ''
            
            #Hay modificaciones en Alfa? Las copiamos al addon, incuidas las carpetas de migración a PY3
            if filetools.exists(alfa_addon_updates) and filetools.exists(addon_path):
                for root, folders, files in filetools.walk(alfa_addon_updates_mig):
                    if ('future' in root or 'past' in root) and not 'concurrent' in root:
                        for file in files:
                            alfa_addon_updates_mig_folder = root.replace(alfa_addon_updates_mig, addon_path_mig)
                            if not filetools.exists(alfa_addon_updates_mig_folder):
                                filetools.mkdir(alfa_addon_updates_mig_folder)
                            if file.endswith('.pyo') or file.endswith('.pyd'):
                                continue
                            input_file = filetools.join(root, file)
                            output_file = input_file.replace(alfa_addon_updates_mig, addon_path_mig)
                            if not filetools.copy(input_file, output_file, silent=True):
                                logger.error('Error en la copia de MIGRACIÓN: Input: %s o Output: %s' % (input_file, output_file))
                                return False
                
                for root, folders, files in filetools.walk(alfa_addon_updates):
                    for file in files:
                        input_file = filetools.join(root, file)
                        output_file = input_file.replace(alfa_addon_updates, addon_path_mig)
                        if file in ['addon.xml']:
                            filetools.copy(input_file, filetools.join(addon_path_root, file), silent=True)
                            continue
                        if not filetools.copy(input_file, output_file, silent=True):
                            logger.error('Error en la copia: Input: %s o Output: %s' % (input_file, output_file))
                            return False
                return True
            else:
                logger.error('Alguna carpeta no existe: Alfa: %s o %s: %s' % (alfa_addon_updates, addon_name, addon_path_mig))

        # Se ha desinstalado Quasar, reseteamos la opción
        else:
            config.set_setting('addon_quasar_update', False)
            if filetools.exists(filetools.join(config.get_data_path(), "%s.json" % addon_name)):
                filetools.remove(filetools.join(config.get_data_path(), "%s.json" % addon_name))
            return True
    except:
        logger.error(traceback.format_exc())
    
    return False


def update_libtorrent():
    logger.info()
    
    if not config.get_setting("mct_buffer", server="torrent", default=""):
        default = config.get_setting("torrent_client", server="torrent", default=0)
        config.set_setting("torrent_client", default, server="torrent")
        config.set_setting("mct_buffer", "50", server="torrent")
        if config.get_setting("mct_download_path", server="torrent", default=config.get_setting("downloadpath")):
            config.set_setting("mct_download_path", config.get_setting("downloadpath"), server="torrent")
        config.set_setting("mct_background_download", True, server="torrent")
        config.set_setting("mct_rar_unpack", True, server="torrent")
        config.set_setting("bt_buffer", "50", server="torrent")
        if config.get_setting("bt_download_path", server="torrent", default=config.get_setting("downloadpath")):
            config.set_setting("bt_download_path", config.get_setting("downloadpath"), server="torrent")
        config.set_setting("mct_download_limit", "", server="torrent")
        config.set_setting("magnet2torrent", False, server="torrent")
        
    if not filetools.exists(filetools.join(config.get_setting("bt_download_path", server="torrent"), 'BT-torrents')):
        filetools.mkdir(filetools.join(config.get_setting("bt_download_path", server="torrent"), 'BT-torrents'))
    if not filetools.exists(filetools.join(config.get_setting("mct_download_path", server="torrent"), 'MCT-torrent-videos')):
        filetools.mkdir(filetools.join(config.get_setting("mct_download_path", server="torrent"), 'MCT-torrent-videos'))
        filetools.mkdir(filetools.join(config.get_setting("mct_download_path", server="torrent"), 'MCT-torrents'))
    if not filetools.exists(ADDON_USERDATA_BIN_PATH):
        filetools.mkdir(ADDON_USERDATA_BIN_PATH)
        
    if not filetools.exists(ADDON_CUSTOMCODE_JSON) or not config.get_setting("unrar_path", server="torrent", default="") \
                    or (not 'unrar' in str(filetools.listdir(ADDON_USERDATA_BIN_PATH)).lower() and \
                    ADDON_PLATFORM not in ["android", "atv2"]) or ADDON_PLATFORM in ["android", "atv2"]:

        path = filetools.join(ADDON_PATH, 'lib', 'rarfiles')
        sufix = ''
        unrar = ''
        for device in filetools.listdir(path):
            if ADDON_PLATFORM in ["android", "atv2"] and 'android' not in device: continue
            if ADDON_PLATFORM in ['windows', 'xbox'] and 'windows' not in device: continue
            if ADDON_PLATFORM not in ['windows', 'xbox'] and ADDON_PLATFORM not in ["android", "atv2"] \
                        and ('android' in device or 'windows' in device): continue
            if 'windows' in device:
                sufix = '.exe'
            else:
                sufix = ''
            unrar = filetools.join(path, device, 'unrar%s') % sufix
            unrar_dest = filetools.join(ADDON_USERDATA_BIN_PATH, 'unrar%s') % sufix
            if not filetools.exists(unrar): unrar = ''
            
            if unrar:
                if ADDON_PLATFORM not in ['windows', 'xbox']:
                    try:
                        if ADDON_PLATFORM in ["android", "atv2"]:
                            # Para Android copiamos el binario a la partición del sistema
                            unrar_org = unrar
                            unrar = filetools.join('special://xbmc/', 'files').replace('/cache/apk/assets', '')
                            if not filetools.exists(unrar):
                                filetools.mkdir(unrar)
                            unrar = filetools.join(unrar, 'unrar')
                            res = filetools.copy(unrar_org, unrar, silent=True)
                            if not res: raise
                        
                        filetools.chmod(unrar, '777')
                    except:
                        logger.info('######## UnRAR ERROR in path: %s' % str(unrar), force=True)
                        logger.error(traceback.format_exc())
                if ADDON_PLATFORM not in ["android", "atv2"]:
                    res = filetools.copy(unrar, unrar_dest, ch_mod='777', silent=True)
                    if not res:
                        logger.info('######## UnRAR ERROR in path: %s' % str(unrar_dest), force=True)
                        continue
                    unrar = unrar_dest

                try:
                    p = execute_binary_from_alfa_assistant('openBinary', [unrar], wait=True, init=True)
                    try:
                        output_cmd, error_cmd = p.communicate()
                        if p.returncode != 0 or error_cmd:
                            logger.info('######## UnRAR returncode in module %s: %s, %s in %s' % \
                                    (device, str(p.returncode), str(error_cmd), unrar), force=True)
                            unrar = ''
                        else:
                            logger.info('######## UnRAR OK in %s: %s' % (device, unrar), force=True)
                            break
                    except:
                        if p.returncode == 0:
                            logger.info('######## UnRAR OK in %s: %s' % (device, unrar), force=True)
                            break
                except:
                    logger.info('######## UnRAR ERROR in module %s: %s' % (device, unrar), force=True)
                    logger.error(traceback.format_exc(1))
                    unrar = ''
        
        if unrar: 
            config.set_setting("unrar_path", unrar, server="torrent")
            config.set_setting("unrar_device", device, server="torrent")
        else:
            config.set_setting("unrar_path", "", server="torrent")
            config.set_setting("unrar_device", "", server="torrent")

    # Ahora descargamos la última versión disponible de Libtorrent para esta plataforma
    try:
        # Saltamos plataformas no soportadas
        if PY3 and (ADDON_PLATFORM in ['windows', 'xbox'] or ADDON_PLATFORM in ["android", "atv2"]):
            config.set_setting("libtorrent_path", "", server="torrent")
            config.set_setting("libtorrent_version", "ERROR/UNSUPPORTED", server="torrent")
            return
        
        version_base = filetools.join(ADDON_PATH, 'lib', 'python_libtorrent')
        libt_dir = filetools.listdir(filetools.join(ADDON_USERDATA_PATH, 'custom_code', 'lib'))
        if 'libtorrent' in str(libt_dir) or (not 'libtorrent' in str(filetools.listdir(ADDON_USERDATA_BIN_PATH)) and \
                    ADDON_PLATFORM not in ["android", "atv2"]):
            for libt_file in libt_dir:
                if 'libtorrent' in libt_file:
                    filetools.remove(filetools.join(ADDON_USERDATA_PATH, 'custom_code', 'lib', libt_file), silent=True)
            current_system = ''
            current_version = ''
        elif config.get_setting("libtorrent_version", server="torrent", default="") \
                    and config.get_setting("libtorrent_path", server="torrent", default=""):
            current_system, current_version = config.get_setting("libtorrent_version", server="torrent", default="").split('/')
        else:
            current_system = ''
            current_version = ''
            
        if '1.1.1' not in current_version and ('arm' in current_system or 'aarch64' in current_system): current_version = ''

        version_base = filetools.join(version_base, current_system)
        if current_version:
            old_version = current_version
            new_version = sorted(filetools.listdir(version_base))
            new_version_alt = new_version[:]
            if new_version:
                for folder in new_version_alt:
                    if not filetools.isdir(filetools.join(version_base, folder)):
                        new_version.remove(folder)
                if old_version != new_version[-1]:
                    current_version = ''
            else:
                current_version = ''
    except:
        current_version = ''
        logger.error(traceback.format_exc(1))
    
    custom_code_json = filetools.exists(ADDON_CUSTOMCODE_JSON)
    if custom_code_json and current_version:
        msg = 'Libtorrent_path: %s' % config.get_setting("libtorrent_path", server="torrent", default="")
        if current_version not in msg:
            msg += ' - Libtorrent_version: %s/%s' % (current_system, current_version)
        logger.info(msg, force=True)
        return

    try:
        logger.info('Libtorrent stored version: %s, %s' % (config.get_setting("libtorrent_version", \
                            server="torrent", default=""), str(custom_code_json)), force=True)
        from lib.python_libtorrent.python_libtorrent import get_libtorrent
    except Exception as e:
        logger.error(traceback.format_exc())
        if not PY3:
            e = unicode(str(e), "utf8", errors="replace").encode("utf8")
        config.set_setting("libtorrent_path", "", server="torrent")
        if not config.get_setting("libtorrent_error", server="torrent", default=''):
            config.set_setting("libtorrent_error", str(e), server="torrent")
    
    return
    

def verify_Kodi_video_DB():
    logger.info()
    import random
    
    platform = {}
    path = ''
    db_files = []
    
    try:
        path = filetools.join("special://masterprofile/", "Database")
        if filetools.exists(path):
            platform = config.get_platform(full_version=True)
            if platform and platform.get('video_db', ''):
                db_files = filetools.walk(path)
                if filetools.exists(filetools.join(path, platform['video_db'])):
                    for root, folders, files in db_files:
                        for file in files:
                            if platform['video_db'] not in file:
                                if file.startswith('MyVideos'):
                                    randnum = str(random.randrange(1, 999999))
                                    filetools.rename(filetools.join(path, file), 'OLD_' + randnum +'_' + file)
                                    logger.error('BD obsoleta: ' + file)
                    
                else:
                    logger.error('Video_DB: ' + str(platform['video_db']) + ' para versión Kodi ' + str(platform['num_version']) + ' NO EXISTE. Analizar carpeta: ' + str(db_files))
            else:
                logger.error('Estructura de get_platform(full_version=True) incorrecta')
        else:
            logger.error('Path a Userdata/Database (' + path + ') no encontrado')
        
    except:
        logger.error('Platform: ' + str(platform) + ' / Path: ' + str(path) + ' / Files: ' + str(db_files))
        logger.error(traceback.format_exc())
        
    return
    

def set_Kodi_video_DB_useFolderNames():
    logger.info()
    
    from platformcode.xbmc_videolibrary import execute_sql_kodi

    strPath = filetools.join(config.get_videolibrary_path(), config.get_setting("folder_movies"), ' ').strip()
    scanRecursive = 2147483647
    
    while xbmc.getCondVisibility('Library.IsScanningVideo()'):
        time.sleep(1)
        
    sql = 'UPDATE path SET useFolderNames=1 WHERE (strPath="%s" and scanRecursive=%s and strContent="movies" ' \
                        'and useFolderNames=0)' % (strPath, scanRecursive)
                      
    nun_records, records = execute_sql_kodi(sql)
    
    if nun_records > 0:
        logger.debug('MyVideos DB updated to Videolibrary %s useFolderNames=1' % config.get_setting("folder_movies"))


def reactivate_unrar(init=False, mute=True):
    logger.info()
    from servers.torrent import torrent_dirs
    
    torrent_paths = torrent_dirs()
    download_paths = []
    
    for torr_client, save_path_videos in list(torrent_paths.items()):
        if 'BT' not in torr_client and 'MCT' not in torr_client:
            torr_client = torr_client.lower()
        if '_' not in torr_client and '_web' not in torr_client and save_path_videos \
                            and save_path_videos not in str(download_paths):
            download_paths.append((torr_client, save_path_videos))              # Agregamos el path para este Cliente

            # Borramos archivos de control "zombies"
            rar_control = {}
            if filetools.exists(filetools.join(save_path_videos, '_rar_control.json')):
                rar_control = jsontools.load(filetools.read(filetools.join(save_path_videos, '_rar_control.json')))
            if rar_control and len(rar_control['rar_files']) == 1:
                ret = filetools.remove(filetools.join(save_path_videos, '_rar_control.json'), silent=True)

    config.set_setting("torrent_paths_list", download_paths, channel="downloads")
    search_for_unrar_in_error(download_paths, init=init)    


def search_for_unrar_in_error(download_paths, init=False):
    logger.info(str(init) + ' / ' + str(download_paths))
    from servers.torrent import check_rar_control
    
    rar_processed = []
    
    for torrent_client, path in download_paths:
        list_dir = filetools.listdir(path)
        for folder_w in list_dir:
            folder = filetools.join(path, folder_w)
            if filetools.isdir(folder):
                if not filetools.exists(filetools.join(folder, '_rar_control.json')):
                    continue
            else:
                if not '_rar_control.json' in folder:
                    continue

            if folder in rar_processed:
                continue
            rar_processed += [folder]

            rar_control = check_rar_control(folder, torr_client=torrent_client, init=init)
            if rar_control:
                try:
                    threading.Thread(target=call_unrar, args=(rar_control,)).start()    # Creamos un Thread independiente por UnRAR
                    time.sleep(1)                                               # Dejamos terminar la inicialización...
                except:                                                         # Si hay problemas de threading, pasamos al siguiente
                    logger.error(traceback.format_exc())

    if not init:
        sys.exit(0)


def call_unrar(rar_control):
    logger.info(str(rar_control['status']) + ' / ' + str(rar_control.get('path_control')))
    
    if rar_control['path_control']:
        item = Item().fromjson(filetools.read(filetools.join(config.get_setting("downloadlistpath"), rar_control['path_control'])))
    else:
        item = Item().fromurl(rar_control['item'])
    mediaurl = rar_control['mediaurl']
    rar_files = rar_control['rar_files']
    torr_client = rar_control['torr_client']
    password = rar_control['password']
    size = rar_control['size']
    
    # Creamos el listitem
    xlistitem = xbmcgui.ListItem(path=item.url)

    if config.get_platform(True)['num_version'] >= 16.0:
        xlistitem.setArt({'icon': item.thumbnail, 'thumb': item.thumbnail, 'poster': item.thumbnail,
                         'fanart': item.thumbnail})
    else:
        xlistitem.setIconImage(item.thumbnail)
        xlistitem.setThumbnailImage(item.thumbnail)
        xlistitem.setProperty('fanart_image', item.thumbnail)

    if config.get_setting("player_mode"):
        xlistitem.setProperty('IsPlayable', 'true')

    platformtools.set_infolabels(xlistitem, item)
    
    return platformtools.rar_control_mng(item, xlistitem, mediaurl, rar_files, \
                    torr_client, password, size, rar_control)


def reset_videolibrary_by_channel(inactive=True):

    ###### LISTA DE CANALES PARA SOBRESCRIBIR SU VIDEOTECA, o "*" PARA TODOS
    channels_list = []

    if not channels_list or not config.get_setting("update", "videolibrary") or \
                    config.get_setting("videolibrary_backup_scan", "videolibrary"):
        return

    try:
        # Vemos si ya se ha sobrescrito, si no marcamos
        if filetools.exists(ADDON_CUSTOMCODE_JSON):
            json_data = jsontools.load(filetools.read(ADDON_CUSTOMCODE_JSON))
        else:
            json_data = {}
        if json_data.get('reset_videolibrary_by_channel', ''): return
        json_data['reset_videolibrary_by_channel'] = channels_list
        if not filetools.write(ADDON_CUSTOMCODE_JSON, jsontools.dump(json_data)):
            logger.error('No se puede actualizar el .json %s' % ADDON_CUSTOMCODE_JSON)
            logger.error('Error sobrescribiendo la Videoteca para los canales: %s' % channels_list)
            return

        logger.info('Sobrescribiendo para canales: %s' % channels_list, force=True)
        from core import videolibrarytools
        from lib.generictools import verify_channel

        # SERIES
        show_list = []
        for path, folders, files in filetools.walk(videolibrarytools.TVSHOWS_PATH):
            for f in files:
                if f == "tvshow.nfo":
                    nfo_path = filetools.join(path, f)
                    head_nfo, it = videolibrarytools.read_nfo(nfo_path)
                    for channel, url in list(it.library_urls.items()):
                        if channel in channels_list or verify_channel(channel) in channels_list or '*' in channels_list:
                            show_list.extend([nfo_path])
                            break

        logger.info("Lista de SERIES a sobrescribir: %s" % show_list, force=True)
        if show_list:
            heading = config.get_localized_string(60584)
            p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(60585), heading)
            p_dialog.update(0, '')
            time.sleep(5)

            if show_list:
                t = float(100) / len(show_list)

            for i, tvshow_file in enumerate(show_list):
                videolibrarytools.reset_serie(tvshow_file, p_dialog, i, t, inactive)
            p_dialog.close()

            if config.is_xbmc():
                import xbmc
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.update(config.get_setting("folder_tvshows"), '_scan_series')      # Se cataloga SERIES en Kodi
                while xbmc.getCondVisibility('Library.IsScanningVideo()'):                          # Se espera a que acabe el scanning
                    time.sleep(1)
                for tvshow_file in show_list:
                    xbmc_videolibrary.mark_content_as_watched_on_alfa(tvshow_file)

        # MOVIES
        movies_list = []
        for path, folders, files in filetools.walk(videolibrarytools.MOVIES_PATH):
            for f in files:
                if f.endswith(".nfo"):
                    nfo_path = filetools.join(path, f)
                    head_nfo, it = videolibrarytools.read_nfo(nfo_path)
                    for channel, url in list(it.library_urls.items()):
                        if channel in channels_list or verify_channel(channel) in channels_list or '*' in channels_list:
                            movies_list.extend([nfo_path])
                            break

        logger.info("Lista de PELÍCULAS a sobrescribir: %s" % movies_list, force=True)
        if movies_list:
            heading = config.get_localized_string(60584)
            p_dialog = platformtools.dialog_progress_bg(config.get_localized_string(60585), heading)
            p_dialog.update(0, '')

            if movies_list:
                t = float(100) / len(movies_list)

            for i, movie_nfo in enumerate(movies_list):
                videolibrarytools.reset_movie(movie_nfo, p_dialog, i, t)
            p_dialog.close()

            if config.is_xbmc():
                import xbmc
                from platformcode import xbmc_videolibrary
                xbmc_videolibrary.update(config.get_setting("folder_movies"), '_scan_series')       # Se cataloga SERIES en Kodi
                while xbmc.getCondVisibility('Library.IsScanningVideo()'):                          # Se espera a que acabe el scanning
                    time.sleep(1)
                for movie_nfo in movies_list:
                    xbmc_videolibrary.mark_content_as_watched_on_alfa(movie_nfo)
    except:
        logger.error(traceback.format_exc())


def clean_videolibrary_unused_channels():

    ###### LISTA DE CANALES PARA LIMPIAR SU VIDEOTECA, o "*" PARA TODOS
    channels_list = []

    if not channels_list or not config.get_setting("update", "videolibrary") or \
                    config.get_setting("videolibrary_backup_scan", "videolibrary"):
        return

    try:
        # Vemos si ya se ha limpiado, si no marcamos
        if filetools.exists(ADDON_CUSTOMCODE_JSON):
            json_data = jsontools.load(filetools.read(ADDON_CUSTOMCODE_JSON))
        else:
            json_data = {}
        if json_data.get('clean_videolibrary_unused_channels', ''): return
        json_data['clean_videolibrary_unused_channels'] = channels_list
        if not filetools.write(ADDON_CUSTOMCODE_JSON, jsontools.dump(json_data)):
            logger.error('No se puede actualizar el .json %s' % ADDON_CUSTOMCODE_JSON)
            logger.error('Error limpiando la Videoteca para los canales: %s' % channels_list)
            return

        logger.info('Limpiando los canales: %s' % channels_list, force=True)
        from core import videolibrarytools
        from core import scrapertools
        from lib.generictools import verify_channel

        # SERIES y PELIS
        for x, video_folder in enumerate([videolibrarytools.TVSHOWS_PATH, videolibrarytools.MOVIES_PATH]):
            for path, folders, files in filetools.walk(video_folder):
                for f in files:
                    if (x == 0 and f == "tvshow.nfo") or (x == 1 and f.endswith(".nfo")):
                        nfo_path = filetools.join(path, f)
                        head_nfo, it = videolibrarytools.read_nfo(nfo_path)
                        
                        show_list = False
                        for channel, url in list(it.library_urls.items()):
                            if channel in channels_list or verify_channel(channel) in channels_list or '*' in channels_list:
                                show_list = True
                                break
                        if show_list:
                            show_list = []
                            for channel, url in list(it.library_urls.items()):
                                show_list += [channel]
                        if not show_list:
                            break
                        
                        logger.info('Limpiando los canales distintos de: %s de la serie/peli: %s' % (show_list, it.title), force=True)
                        for ff in filetools.listdir(path):
                            if '.json' in ff or '.torrent' in ff.lower():
                                if not scrapertools.find_single_match(ff, '\[([^\]]+)\]') in show_list:
                                    logger.info('Borrando archivo: %s' % ff, force=True)
                                    filetools.remove(filetools.join(path, ff))
                        break
    except:
        logger.error(traceback.format_exc())
