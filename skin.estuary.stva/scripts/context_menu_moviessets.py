import xbmc
import xbmcgui

home = xbmcgui.Window(10000)
skin=home.getProperty("CurrentSkin")
if skin == "skin.estuary.stva":
    xbmc.executebuiltin("ActivateWindow(1132)")
else:
    pass 
