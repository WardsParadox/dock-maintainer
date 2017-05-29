# Install Guide:
1. Deploy via either method mentioned in the README.MD document.
2. On a server create an accessible folder (I used my pre-existing Munki repo server as it was already configured as needed.) on a web server.
   ie: `http://example.com/munki_repo/docksetups`
3. Create a plist in that directory that is structured with two arrays. One named `Apps` and one named `Others`. Inside of those array's put the **full path** to the applications (~ shortcut for home also works in the `Others` directory only!) you want to be put in the dock. Something like so:
   ```xml
   <?xml version="1.0" encoding="UTF-8"?>
   <!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
   <plist version="1.0">
   <dict>
   	<key>Apps</key>
   	<array>
       <string>/Applications/Google Chrome.app</string>
       <string>~/Applications/Slack.app</string>
       <string>/Applications/Atom.app</string>
       <string>/Applications/iTerm.app</string>
       <string>/Applications/Boostnote.app</string>
       <string>/Applications/Microsoft Remote Desktop Beta.app</string>
     </array>
     <key>Others</key>
     <array>
       <string>/Applications</string>
       <string>~/Downloads</string>
     </array>
   </dict>
   </plist>
   ```
4. On the computer that you want an account's dock to be maintained, run the following, where username is a short name of the user you want maintained and ServerURL is the **url to the folder containing the dock plists, not the plists itself**:
   `/usr/bin/defaults write /Library/Preferences/com.github.wardsparadox.dock-maintainer ManagedUser "username"`
   `/usr/bin/defaults write /Library/Preferences/com.github.wardsparadox.dock-maintainer ServerURL "http://example.com/munki_repo/docksetups"`
5. You can then reboot the machine or run `/usr/local/outset/outset --boot` to update or download the cached plist on the machine.
6. Login as the user you wish to see and badaboom, dock should be the one you wish to see (note: outset can take a few seconds to startup after login.)
7. Logs for the updater are in `/Library/Logs` and the maintainer has logs in `~/Library/Logs` as it runs as the user.
