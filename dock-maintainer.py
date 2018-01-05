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
                       CFPreferencesSetAppValue, \
                       CFPreferencesSetMultiple, \
                       kCFPreferencesCurrentUser, \
                       CFPreferencesAppSynchronize, \
                       NSURL

from SystemConfiguration import SCDynamicStoreCopyConsoleUser

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p',
                    level=logging.INFO,
                    filename=os.path.expanduser('~/Library/Logs/dock-maintainer.log'))
stdout_logging = logging.StreamHandler()
stdout_logging.setFormatter(logging.Formatter())
logging.getLogger().addHandler(stdout_logging)

class DockError(Exception):
    '''Basic exception'''
    pass

class Dock():
    '''Class to handle Dock operations'''
    _DOMAIN = 'com.apple.dock'
    _DOCK_PLIST = os.path.expanduser(
        '~/Library/Preferences/com.apple.dock.plist')
    _DOCK_LAUNCHAGENT_ID = 'com.apple.Dock.agent'
    _DOCK_LAUNCHAGENT_FILE = '/System/Library/LaunchAgents/com.apple.Dock.plist'
    _SECTIONS = ['persistent-apps', 'persistent-others']
    items = {}

    def __init__(self):
        for key in self._SECTIONS:
            try:
                section = CFPreferencesCopyAppValue(key, self._DOMAIN)
                self.items[key] = section.mutableCopy()
            except Exception:
                raise

    def save(self):
        '''saves our (modified) Dock preferences'''
        # unload Dock launchd job so we can make our changes unmolested
        subprocess.call(
            ['/bin/launchctl', 'unload', self._DOCK_LAUNCHAGENT_FILE])

        for key in self._SECTIONS:
            try:
                CFPreferencesSetAppValue(key, self.items[key], self._DOMAIN)
            except Exception:
                raise DockError
        if not CFPreferencesAppSynchronize(self._DOMAIN):
            raise DockError

        # restart the Dock
        subprocess.call(['/bin/launchctl', 'load', self._DOCK_LAUNCHAGENT_FILE])
        subprocess.call(['/bin/launchctl', 'start', self._DOCK_LAUNCHAGENT_ID])

    def findExistingLabel(self, test_label, section='persistent-apps'):
        '''returns index of item with label matching test_label
            or -1 if not found'''
        for index in range(len(self.items[section])):
            if (self.items[section][index]['tile-data'].get('file-label') ==
                    test_label):
                return index
        return -1

    def removeDockEntry(self, label, section=None):
        '''Removes a Dock entry with matching label, if any'''
        if section:
            sections = [section]
        else:
            sections = self._SECTIONS
        for section in sections:
            found_index = self.findExistingLabel(label, section=section)
            if found_index > -1:
                del self.items[section][found_index]

    def replaceDockEntry(self, thePath, label=None, section='persistent-apps'):
        '''Replaces a Dock entry. If label is None, then a label is derived
            from the item path. The new entry replaces an entry with the given
            or derived label'''
        if section == 'persistent-apps':
            new_item = self.makeDockAppEntry(thePath)
        else:
            new_item = self.makeDockOtherEntry(thePath)
        if new_item:
            if not label:
                label = os.path.splitext(os.path.basename(thePath))[0]
            found_index = self.findExistingLabel(label, section=section)
            if found_index > -1:
                self.items[section][found_index] = new_item

    def makeDockAppEntry(self, thePath):
        '''returns a dictionary corresponding to a Dock application item'''
        label_name = os.path.splitext(os.path.basename(thePath))[0]
        ns_url = NSURL.fileURLWithPath_(thePath).absoluteString()
        return {'tile-data': {'file-data': {'_CFURLString': ns_url,
                                            '_CFURLStringType': 15},
                              'file-label': label_name,
                              'file-type': 41},
                'tile-type': 'file-tile'}

    def makeDockOtherEntry(self, thePath,
                           arrangement=0, displayas=1, showas=0):
        '''returns a dictionary corresponding to a Dock folder or file item'''
        # arrangement values:
        #     1: sort by name
        #     2: sort by date added
        #     3: sort by modification date
        #     4: sort by creation date
        #     5: sort by kind
        #
        # displayas values:
        #     0: display as stack
        #     1: display as folder
        #
        # showas values:
        #     0: auto
        #     1: fan
        #     2: grid
        #     3: list

        label_name = os.path.splitext(os.path.basename(thePath))[0]
        if arrangement == 0:
            if label_name == 'Downloads':
                # set to sort by date added
                arrangement = 2
            else:
                # set to sort by name
                arrangement = 1
        ns_url = NSURL.fileURLWithPath_(thePath).absoluteString()
        if os.path.isdir(thePath):
            return {'tile-data':{'arrangement': arrangement,
                                 'displayas': displayas,
                                 'file-data':{'_CFURLString': ns_url,
                                              '_CFURLStringType': 15},
                                 'file-label': label_name,
                                 'dock-extra': False,
                                 'showas': showas
                                },
                    'tile-type':'directory-tile'}
        else:
            return {'tile-data':{'file-data':{'_CFURLString': ns_url,
                                              '_CFURLStringType': 15},
                                 'file-label': label_name,
                                 'dock-extra': False},
                    'tile-type':'file-tile'}

dock = Dock()

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
    keys["ManagedUser"] = \
    CFPreferencesCopyAppValue("ManagedUser",
                             "com.github.wardsparadox.dock-maintainer")
    if keys["ManagedUser"] is None:
        logging.error("No ManagedUser Preference set!"
                      "Please set that via defaults write"
                      "com.github.wardsparadox.dock-maintainer ManagedUser nameofuser")
        exit(2)
    configPath = os.path.realpath(
        "/Library/Application Support/com.github.wardsparadox.dock-maintainer/")
    try:
        configPlist = plistlib.readPlist(os.path.join(configPath, keys["ManagedUser"]))
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
        persistent_apps = dock.items['persistent-apps']
        persistent_others = dock.items['persistent-others']
        dock_apps = []
        dock_others = []
        config_apps = []
        config_others = []
        for dockapp in persistent_apps:
            dock_apps.append(str(dockapp["tile-data"]["file-label"]))
        for configapp in configPlist['Apps']:
            config_apps.append(os.path.splitext(os.path.basename(configapp))[0])
        for dockother in persistent_others:
            dock_others.append(str(dockother["tile-data"]["file-label"]))
        for configother in configPlist['Others']:
            config_others.append(os.path.splitext(os.path.basename(configother))[0])

        final_apps = []
        final_others = []
        if len(list(set(dock_apps) ^ set(config_apps))) > 0:
            logging.info("dock-maintainer: App missing from dock, setting dock to config")
            for app in configPlist['Apps']:
                final_apps.append(dock.makeDockAppEntry(app))
            dock.items['persistent-apps'] = final_apps
        else:
            logging.info("dock-maintainer: Dock Apps match Config Apps, nothing to change")
        if len(list(set(dock_others) ^ set(config_others))) > 0:
            logging.info("dock-maintainer: Other Item missing from dock, setting dock to config")
            for item in configPlist['Others']:
                final_others.append(dock.makeDockOtherEntry(os.path.expanduser(item), 0, 1, 3))
                print item
            dock.items['persistent-others'] = final_others
        else:
            logging.info("dock-maintainer: Dock Other Items match Config Other Items, nothing to change")

        if len(final_apps) or len(final_others) > 0:
            dock.save()
        else:
            print "dock does not need to be reloaded"
        logging.info("dock-maintainer: Killing Dock to finalize")
        #setPreferences()

if __name__ == '__main__':
    main()
