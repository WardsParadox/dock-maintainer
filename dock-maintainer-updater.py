#!/usr/bin/python
'''
 Downloads file as needed for dock-maintainer. Sets extended attribute to be
 the last mod date for the plist according to the server. Suggested work around
 by elios on macadmins.org
'''
import urllib2
import datetime
from time import mktime
import os
import sys
import subprocess
import logging
import xattr
from Foundation import kCFPreferencesCurrentHost, \
                       kCFPreferencesAnyUser, \
                       CFPreferencesCopyValue

logging.basicConfig(format='%(asctime)s - %(levelname)s: %(message)s',
                    datefmt='%Y-%m-%d %I:%M:%S %p',
                    level=logging.INFO,
                    filename=os.path.normpath("/Library/Logs/dock-maintainer.log"))
stdout_logging = logging.StreamHandler()
stdout_logging.setFormatter(logging.Formatter())
logging.getLogger().addHandler(stdout_logging)


def downloadFile(url, filepath, attributedate):
    '''
    Downloads url to filepath
    '''
    with open(filepath, "wb") as code:
        code.write(url.read())
    xattr.setxattr(filepath, 'dock-maintainer.Last-Modified-date', str(attributedate))
    logging.info("Downloaded File to %s", filepath)
    return filepath

def wait_for_network():
    """Wait until network access is up."""
    # Wait up to 180 seconds for scutil dynamic store to register DNS
    cmd = [
        '/usr/sbin/scutil',
        '-w', 'State:/Network/Global/DNS',
        '-t', '180'
    ]
    task = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    out, err = task.communicate()
    if task.returncode != 0:
        logging.error("Network did not come up after 3 minutes. Aborting")
        sys.exit(1)
    return True


def main():
    '''
    Main Controlling Module:
    - Checks preferences set
    - Checks for Path, if not creates
    - Downloads plist if needed
    '''
    keys = {}
    keys["ManagedUser"] = CFPreferencesCopyValue("ManagedUser",
                                                 "com.github.wardsparadox.dock-maintainer",
                                                 kCFPreferencesAnyUser,
                                                 kCFPreferencesCurrentHost)

    keys["ServerURL"] = CFPreferencesCopyValue("ServerURL",
                                               "com.github.wardsparadox.dock-maintainer",
                                               kCFPreferencesAnyUser,
                                               kCFPreferencesCurrentHost)


    path = os.path.realpath("/Library/Application Support/com.github.wardsparadox.dock-maintainer")
    if os.path.exists(path):
        logging.info("Path exists at %s", path)
    else:
        logging.info("Path not found, creating at %s", path)
        os.mkdir(path, 0755)

    if keys["ManagedUser"] is None:
        logging.error("No ManagedUser Preference set")
        exit(2)
    else:
        plistfilepath = os.path.join(path, keys["ManagedUser"])
        completeurl = os.path.join(keys["ServerURL"], keys["ManagedUser"])
        try:
            fileurl = urllib2.urlopen(completeurl)
            meta = fileurl.info().getheaders("Last-Modified")[0]
            servermod = datetime.datetime.fromtimestamp(mktime(
                datetime.datetime.strptime(
                    meta, "%a, %d %b %Y %X GMT").timetuple()))
        except urllib2.HTTPError:
            logging.error("Can not connect to url")
            exit(1)

    if not os.path.isfile(plistfilepath):
        logging.info("File not found! Downloading")
        downloadFile(fileurl, plistfilepath, servermod)
        exit(0)

    if xattr.listxattr(plistfilepath):
        logging.info("Got File Attributes")
    else:
        logging.info("No Attributes found! Downloading and setting them")
        downloadFile(fileurl, plistfilepath, servermod)
        exit(0)
    filexattrdate = xattr.getxattr(plistfilepath,
                                   'dock-maintainer.Last-Modified-date')
    if str(servermod) != filexattrdate:
        logging.info("File is out of date")
        downloadFile(fileurl, plistfilepath, servermod)
    else:
        logging.info("File is synced.")
        exit(0)

if __name__ == '__main__':
    wait_for_network()
    main()
