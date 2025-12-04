#!/usr/bin/osascript
# PDF TOC Splitter GUI Launcher - AppleScript Version
# This can be saved as an .app file for easy double-clicking

tell application "Terminal"
    activate
    set currentPath to do shell script "dirname " & quoted form of (POSIX path of (path to me))
    do script "cd " & quoted form of currentPath & " && ./run_pdf_splitter_gui.sh"
end tell