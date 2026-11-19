import QtQuick
import Quickshell
import Quickshell.Hyprland
import Quickshell.Io

// The shell injects its bar widget registry only into a plugin's service entry point, never
// into a bar widget. Panel.qml reads it back with bar.shell.serviceFor(), which a plugin may
// call for its own id.
QtObject {
  id: service

  property var barWidgetRegistry: null
  property var pluginRegistry: null
  property var shell: null
  property var manifest: ({})
  property string omarchyPath: ""

  // Live copies (Panel.qml items), one per monitor.
  property var copies: []

  // The screen whose picker should open again after a size change rebuilds the bar.
  property string pendingScreen: ""

  function reopenLater(screenName) { pendingScreen = screenName }

  function takePending(screenName) {
    if (pendingScreen === "" || pendingScreen !== screenName) return false
    pendingScreen = ""
    return true
  }

  function register(copy) {
    if (copies.indexOf(copy) === -1) copies = copies.concat([copy])
  }

  function unregister(copy) {
    copies = copies.filter(function(c) { return c !== copy })
  }

  function focusedScreen() {
    var monitor = Hyprland.focusedMonitor
    return monitor ? String(monitor.name) : ""
  }

  // The logo on the focused monitor, else any copy.
  function panelCopy() {
    var here = copies.filter(function(c) { return c.screenName === focusedScreen() })
    return here.length > 0 ? here[0] : (copies.length > 0 ? copies[0] : null)
  }

  // No setup step for the user: `omarchy plugin add ... --enable` puts one bare entry on the
  // bar, which starts this service, and `omadistro setup` turns the menu into the logo copy.
  // It changes nothing once the copy has a logo, so it is safe on every start.
  property Process setup: Process {
    command: ["python3", "-I", decodeURIComponent(String(Qt.resolvedUrl("omadistro")).replace(/^file:\/\//, "")), "setup"]
    stdout: StdioCollector { onStreamFinished: if (text.trim() !== "already set up") console.info("OmaDistro: " + text.trim()) }
    stderr: StdioCollector { onStreamFinished: if (text.trim() !== "") console.warn("OmaDistro: " + text.trim()) }
  }

  Component.onCompleted: setup.running = true

  // Open the logo picker from a keybinding or a script:
  //   qs -p /usr/share/omarchy/shell ipc call omadistro togglePicker
  property IpcHandler ipc: IpcHandler {
    target: "omadistro"

    function togglePicker(): string {
      var copy = service.panelCopy()
      if (!copy) return "no OmaDistro logo on the bar"
      copy.togglePicker()
      return "ok"
    }
  }
}
