#!/usr/bin/python
'''
A wrapper for dockutil that manages a specified users dock with a server based plist for the list.
'''
import subprocess
import plistlib
import os
import logging
from Foundation import kCFPreferencesCurrentHost, \
                       CFPreferencesCopyAppValue, \
                       CFPreferencesSetMultiple, \
                       kCFPreferencesCurrentUser

from SystemConfiguration import SCDynamicStoreCopyConsoleUser

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p',
                    level=logging.INFO,
                    filename=os.path.expanduser('~/Library/Logs/dock-maintainer.log'))
stdout_logging = logging.StreamHandler()
stdout_logging.setFormatter(logging.Formatter())
logging.getLogger().addHandler(stdout_logging)

if os.path.exists("/usr/local/bin/dockutil"):
    dockutil = "/usr/local/bin/dockutil"
else:
    logging.error("dock-maintainer: dockutil not installed!")
    exit(4)

killall = ['/usr/bin/killall', 'Dock']

def addItemToSection(Section):
    '''
    Adds item to specified section of dock via dockutil
    '''
    for item in Section:
        try:
            subprocess.Popen([dockutil, "--add", item, "--no-restart"],
                             stderr=subprocess.PIPE, shell=False).communicate()
        except subprocess.CalledProcessError:
            subprocess.Popen([dockutil, "--add", item, "--no-restart",
                              "--replacing", item],
                             stderr=subprocess.PIPE, shell=False).communicate()
        logging.info("dock-maintainer: Adding to Dock: " + item)

def matchList(inputPlist, outputPlist, SectionName):
    '''
    matches inputPlist and outputPlist
    '''
    if not outputPlist[SectionName]:
        logging.info("outPlist[%s] is empty, setting to value of inputPlist", SectionName)
        return inputPlist[SectionName]

    missingItems = list(set(inputPlist[SectionName]) -
                        set(outputPlist[SectionName]))
    if len(missingItems) > 0:
        for item in missingItems:
            outputPlist[SectionName].insert(inputPlist[SectionName].index(item), item)
            logging.info("Adding %s to current", item)
        return outputPlist[SectionName]
    else:
        logging.info("None missing in outputPlist[%s], exiting", SectionName)

def setPreferences():
    '''
    Sets dock preferences to keep dock as is.
    '''
    preferences = {}
    preferences["contents-immutable"] = True
    preferences["size-immutable"] = True
    preferences["orientation"] = "bottom"
    preferences["position-immutable"] = True
    preferences["magnify-immutable"] = True
    preferences["autohide"] = False
    preferences["autohide-immutable"] = True
    preferences["tilesize"] = int(60)
    CFPreferencesSetMultiple(preferences, None,
                             "com.apple.dock",
                             kCFPreferencesCurrentUser,
                             kCFPreferencesCurrentHost)
    logging.info("dock-maintainer: Setting secure preferences")

def main():
    '''
    Main Stuff
    '''
    keys = {}
    keys["ManagedUser"] = CFPreferencesCopyAppValue("ManagedUser",
                                                 "com.github.wardsparadox.dock-maintainer")
    if keys["ManagedUser"] is None:
        logging.error("No ManagedUser Preference set!"
                      "Please set that via defaults write"
                      "com.github.wardsparadox.dock-maintainer ManagedUser nameofuser")
        exit(2)
    inpath = os.path.realpath(
        "/Library/Application Support/com.github.wardsparadox.dock-maintainer/")
    try:
        inplist = plistlib.readPlist(os.path.join(inpath, keys["ManagedUser"]))
        logging.info("dock-maintainer: Input plist found. Matching docks.")
    except IOError:
        logging.error("dock-maintainer: No input found! Make sure the updater is functioning!")
        exit(3)
    username = (SCDynamicStoreCopyConsoleUser(None, None, None) or [None])[0]
    username = [username, ""][username in [u"loginwindow", None, u""]]
    if username != keys["ManagedUser"]:
        logging.info("dock-maintainer: Exiting as user is not the right user")
        exit(0)
    else:
        outpath = os.path.expanduser(
            "~/Library/Application Support/com.github.wardsparadox.dock-maintainer")
        if os.path.exists(outpath):
            logging.debug("dock-maintainer: Path exists")
        else:
            logging.info("Path not found, creating at %s", outpath)
            os.mkdir(outpath)
        try:
            outplist = plistlib.readPlist(os.path.join(outpath, keys["ManagedUser"]))
        except IOError:
            outplist = {}
            outplist["Apps"] = []
            outplist["Others"] = []
        final = {}
        final["Apps"] = matchList(inplist, outplist, "Apps")
        final["Others"] = matchList(inplist, outplist, "Others")
        if not final["Apps"] and not final["Others"]:
            logging.info("%s's dock not needing an update", keys["ManagedUser"])
            exit(0)
        else:
            if not final["Apps"]:
                print "Mirroring Apps"
                final["Apps"] = inplist["Apps"]
            if not final["Others"]:
                print "Mirroring Others"
                final["Others"] = inplist["Others"]
            with open(os.path.join(outpath, keys["ManagedUser"]), 'wb') as f:
                plistlib.writePlist(final, f)
        subprocess.call([dockutil, "--remove", "all", "--no-restart"], shell=False)
        logging.info("dock-maintainer: Clearing Dock for processing for user %s", username)
        addItemToSection(final["Apps"])
        addItemToSection(final["Others"])
        subprocess.call(killall, shell=False)
        logging.info("dock-maintainer: Killing Dock to finalize")
        #setPreferences()

if __name__ == '__main__':
    main()
