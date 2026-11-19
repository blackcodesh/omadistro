import QtQuick
import QtQuick.Effects
import QtQuick.Window
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Ui
import "Logos.js" as Logos

// Hosts Omarchy's own menu widget, built from the shell's widget registry the way the bar
// builds it, and draws the chosen logo in place of its glyph. Clicks, scroll and the menu
// itself stay Omarchy's. Right-click opens the logo picker (Omarchy's own right-click there
// opened a terminal; SUPER+RETURN still does).
Item {
  id: root

  // Injected by the bar.
  property var bar: null
  property var settings: ({})
  property string moduleName: Logos.PLUGIN_ID

  function setting(name, fallback) {
    var value = settings ? settings[name] : undefined
    return value === undefined || value === null ? fallback : value
  }

  readonly property string screenName: QsWindow.window && QsWindow.window.screen ? String(QsWindow.window.screen.name) : ""
  readonly property int iconPercent: Math.max(60, Math.min(150, Math.round(Number(setting("iconSize", 100)) || 100)))
  // 100% is Omarchy's full icon size (16 px); its own menu glyph paints at 12.
  readonly property real logoSize: Style.bar.iconCanvas * iconPercent / 100
  readonly property var logo: Logos.logoFor(String(setting("logo", "Omarchy")))
  readonly property string logoSource: Qt.resolvedUrl("icons/" + logo.file + ".svg").toString()

  // The registry reaches a plugin only through its own service (Service.qml).
  property var registry: null
  property var service: null
  property int registryAttempts: 0
  readonly property bool registryLost: registry === null && registryAttempts >= 20
  readonly property var hostComponent: componentFor(Logos.MENU_ID, registry ? registry.revision : 0)
  readonly property string problem: registryLost ? "OmaDistro could not reach the widget registry"
    : registry !== null && hostComponent === null ? "Omarchy has no menu widget"
    : ""

  // The menu's own settings, from shell.json's plugins[] entry for omarchy.menu.
  property var hostSettings: ({})
  property var button: null
  property int attachTries: 0

  implicitWidth: problem !== "" ? warning.implicitWidth : slot.implicitWidth
  implicitHeight: problem !== "" ? warning.implicitHeight : slot.implicitHeight

  function resolveRegistry() {
    var own = bar && bar.shell && typeof bar.shell.serviceFor === "function" ? bar.shell.serviceFor(moduleName) : null
    if (own && service !== own) service = own
    var direct = bar && bar.barWidgetRegistry ? bar.barWidgetRegistry : null
    if (direct) { registry = direct; return }
    registry = own && own.barWidgetRegistry ? own.barWidgetRegistry : null
  }

  function componentFor(id, revision) {
    if (!registry || !registry.widgets) return null
    var key = bar && typeof bar.canonicalWidgetId === "function" ? bar.canonicalWidgetId(id) : id
    var entry = registry.widgets[key]
    return entry ? entry.component : null
  }

  // What Bar.qml injects into every widget; the hosted menu is not told it is hosted.
  function inject(item) {
    if (!item) return
    if ("bar" in item) item.bar = root.bar
    if ("moduleName" in item) item.moduleName = Logos.MENU_ID
    if ("settings" in item) item.settings = root.hostSettings
  }

  // The menu's button: the BarIconButton, found by its icon slot and glyph metrics (older
  // Omarchy versions: a plain button with a glyph label).
  function findButton(item, depth) {
    if (!item || depth > 8) return null
    if ("iconComponent" in item && "glyphPaintedWidth" in item) return item
    if ("labelVisible" in item && "fontFamily" in item && "text" in item) return item
    var kids = item.children || []
    for (var i = 0; i < kids.length; i++) {
      var found = findButton(kids[i], depth + 1)
      if (found) return found
    }
    return null
  }

  function attach() {
    var found = findButton(loader.item, 0)
    if (!found) {
      if (attachTries++ < 20) attachRetry.restart()
      else console.warn("[omadistro] no menu button found; leaving Omarchy's own logo")
      return
    }
    button = found
    // Omarchy rescales any custom icon of a BarIconButton to its own 12 px, so the logo cannot
    // be sized from there. An empty icon hides the button's glyph instead, and the logo is
    // drawn over the button at the size chosen here.
    if ("iconComponent" in found) found.iconComponent = emptyIcon
    else found.labelVisible = false
    glyphOverlay.createObject(found, {})
  }

  function readShell() {
    var config
    try { config = JSON.parse(shellView.text()) } catch (e) { return }
    hostSettings = Logos.menuSettingsFrom(config)
  }

  onHostSettingsChanged: if (loader.item && "settings" in loader.item) loader.item.settings = hostSettings
  onServiceChanged: if (service) { service.register(root); claimPending() }
  onScreenNameChanged: claimPending()
  Component.onCompleted: resolveRegistry()
  Component.onDestruction: if (service) service.unregister(root)

  // A copy without a logo is the bare entry `omarchy plugin enable` just placed. Omarchy
  // starts plugin services only at shell start, so this copy runs the first setup itself
  // (omadistro setup is a no-op once the copy has a logo). The delay lets the bar inject
  // `settings` first.
  property Timer setupTimer: Timer {
    interval: 1000
    running: true
    onTriggered: if (String(root.setting("logo", "")) === "") root.setupRun.running = true
  }
  property Process setupRun: Process {
    command: ["python3", "-I", decodeURIComponent(String(Qt.resolvedUrl("omadistro")).replace(/^file:\/\//, "")), "setup"]
  }

  Timer {
    interval: 250
    repeat: true
    running: (root.registry === null || root.service === null) && root.registryAttempts < 20
    onTriggered: { root.registryAttempts++; root.resolveRegistry() }
  }

  Timer {
    id: attachRetry
    interval: 100
    onTriggered: root.attach()
  }

  FileView {
    id: shellView
    path: Quickshell.env("HOME") + "/.config/omarchy/shell.json"
    watchChanges: true
    printErrors: false
    onLoaded: root.readShell()
    onFileChanged: reload()
  }

  Component { id: emptyIcon; Item {} }

  Component {
    id: glyphOverlay
    Image {
      anchors.centerIn: parent
      width: root.logoSize
      height: root.logoSize
      source: root.logoSource
      // Black brand logos: drawn in the bar's text color so they show on a dark bar.
      layer.enabled: root.logo.themed === true
      layer.effect: MultiEffect { brightness: 1.0; colorization: 1.0; colorizationColor: root.bar ? root.bar.foreground : Color.foreground }
      sourceSize.width: width * Math.max(2, Screen.devicePixelRatio)
      sourceSize.height: height * Math.max(2, Screen.devicePixelRatio)
      fillMode: Image.PreserveAspectFit
      smooth: true
    }
  }

  readonly property bool verticalBar: bar ? bar.vertical === true : false

  Item {
    id: slot
    visible: root.problem === ""
    implicitWidth: loader.item && loader.item.visible ? loader.item.implicitWidth : 0
    implicitHeight: loader.item && loader.item.visible ? loader.item.implicitHeight : 0
    width: implicitWidth
    height: implicitHeight

    Loader {
      id: loader
      width: slot.implicitWidth
      height: root.verticalBar ? slot.implicitHeight : parent.height
      active: root.problem === ""
      sourceComponent: root.hostComponent
      onLoaded: {
        attachRetry.stop()
        root.attachTries = 0
        root.button = null
        root.inject(item)
        // Again on the next frame, as the bar does: some widgets read these while building.
        Qt.callLater(function() {
          root.inject(loader.item)
          root.attach()
        })
      }
    }
  }

  BarIconButton {
    id: warning
    visible: root.problem !== ""
    anchors.fill: parent
    bar: root.bar
    tooltipText: root.problem
    iconComponent: Component {
      Image {
        source: Qt.resolvedUrl("icons/warning.svg")
        sourceSize.width: width * Math.max(2, Screen.devicePixelRatio)
        sourceSize.height: height * Math.max(2, Screen.devicePixelRatio)
        fillMode: Image.PreserveAspectFit
        smooth: true
      }
    }
  }

  // A size change rebuilds the bar; the copy that replaces this one on the same screen opens
  // the picker again, so the size can be adjusted step by step.
  function claimPending() {
    if (!service || screenName === "") return
    if (service.takePending(screenName)) reopenTimer.restart()
  }
  Timer {
    id: reopenTimer
    interval: 250
    onTriggered: picker.open = true
  }

  function close() { picker.open = false }
  function togglePicker() { picker.open = !picker.open }

  // Right-click opens the picker. Left click, scroll and hover still reach the menu.
  MouseArea {
    anchors.fill: parent
    z: 10
    acceptedButtons: Qt.RightButton
    onPressed: root.togglePicker()
  }

  LogoPicker {
    id: picker
    anchorItem: root
    bar: root.bar
    owner: root
    current: root.logo.name
    size: root.iconPercent
    service: root.service
    screenName: root.screenName
  }
}
