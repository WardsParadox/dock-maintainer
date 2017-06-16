# dockutil-server
Manages dock for a specified account. I recommend using this with [Outset](https://github.com/chilcote/outset) and [Munki](https://github.com/munki/munki) (Outset for launching files as needed, Munki for hosting the `docksetup` files as it's web server requirements mirror the ones here)

Article explaining this tool: https://wardsparadox.github.io/2017/05/29/dock-maintainer-defined/

SSTP Install Guide: [Install Guide.md](dock-maintainer/Install Guide.md)

**Please file an issue if you have issues. I am not the best of programmers.

TODO:
- [x] Check Preferences
- [x] Check if file is newer on server (download then instead of always downloading)
- [x] Break into two parts.
- [x] Write out which apps have been added to dock. (Only add items as needed instead of always flushing dock)

***Edge Case:
When running this utility if you update the plist on the computer or manually modify the dock. Things may not work as intended if either of those options are used.***

## Two Methods of Deployment:
`dock-maintainer.py` needs to run as a user. I recommend using Outset but I have included `launchctl` files for the appropriate files in the right zones.

`dock-maintainer-updater.py` needs to run as root. This is due to storing the server copy file in the AllUsers Library (`/Library`) as well as logs.

### Use Outset:
1. Deploy `dock-maintainer.py` to `/usr/local/outset/login-every`
2. Deploy `dock-maintainer-updater.py` to `/usr/local/outset/boot-every`
3. `chmod 755 /path/to/files/above && chown root:wheel /path/to/files/above`
4. Clap your hands with a job well done! 👏🏻

### Deploy it w/o Outset
1. Deploy both files to: `/usr/local/bin/dock-maintainer`
2. `chmod -R 755 /usr/local/bin/dock-maintainer && chown -R root:wheel /usr/local/bin/dock-maintainer`
3. Deploy the LaunchAgent and LaunchDaemon included or write your own
4. Go contemplate why you don't use Outset. 😡 **(I jest!😛)**

I recommend using [Munki-Pkg](https://github.com/munki/munki-pkg) with both scenarios above!

## Preferences Needing to be set on the machine:
domain: com.github.wardsparadox.dock-maintainer
ManagedUser - Which user to run for
ServerURL - path to web server folder holding all plists for user
```
{
    ManagedUser = "student";
    ServerURL = "http://example.com/munki_repo/docksetups";
}
```
