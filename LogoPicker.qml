import QtQuick
import QtQuick.Effects
import Quickshell
import Quickshell.Io
import qs.Commons
import qs.Commons as Commons
import qs.Ui
import "Logos.js" as Logos

// The logo picker: a searchable grid of every logo. Opened by right-click on the logo (or
// `omadistro togglePicker` over IPC). Choosing a logo runs `omadistro set`, which writes
// shell.json atomically; Omarchy rebuilds the bar and the new logo appears.
PopupCard {
  id: panel

  property string current: "Omarchy"
  property int size: 100
  property var service: null
  property string screenName: ""
  property string search: ""
  property string message: ""

  readonly property color foreground: bar ? bar.foreground : Commons.Color.popups.text
  readonly property color muted: Qt.darker(foreground, 1.4)
  readonly property string fontFamily: bar ? bar.fontFamily : Style.font.family

  contentWidth: panel.fittedContentWidth(Style.space(400))
  contentHeight: panel.fittedContentHeight(column.implicitHeight)

  onOpenChanged: if (open) { message = ""; search = ""; field.text = "" }

  function choose(name) {
    if (name === current || chooser.running) return
    message = ""
    chooser.command = ["python3", "-I", decodeURIComponent(String(Qt.resolvedUrl("omadistro")).replace(/^file:\/\//, "")), "set", name]
    chooser.running = true
  }

  property Timer forgetReopen: Timer {
    interval: 3000
    onTriggered: if (panel.service) panel.service.reopenLater("")
  }

  function resize(percent) {
    if (percent === size || chooser.running) return
    message = ""
    // The size change rebuilds the bar: ask for this picker to come back on the new copy.
    if (service) service.reopenLater(screenName)
    chooser.keepOpen = true
    chooser.command = ["python3", "-I", decodeURIComponent(String(Qt.resolvedUrl("omadistro")).replace(/^file:\/\//, "")), "size", String(percent)]
    chooser.running = true
  }

  property Process chooser: Process {
    property bool keepOpen: false
    stderr: StdioCollector {
      onStreamFinished: if (text.trim() !== "") panel.message = text.trim()
    }
    onExited: function(code) {
      if (code !== 0 && panel.service) panel.service.reopenLater("")
      if (code === 0 && !keepOpen) panel.open = false
      // The bar rebuilds after a real change (and this picker with it). If it did not, nothing
      // may stay queued to pop the picker open on some later rebuild.
      if (keepOpen) forgetReopen.restart()
      keepOpen = false
    }
  }

  component Logo: Image {
    property bool themed: false
    sourceSize.width: width * Math.max(2, Screen.devicePixelRatio)
    sourceSize.height: height * Math.max(2, Screen.devicePixelRatio)
    fillMode: Image.PreserveAspectFit
    smooth: true
    // Black brand logos: drawn in the text color so they show on a dark card.
    layer.enabled: themed
    layer.effect: MultiEffect { brightness: 1.0; colorization: 1.0; colorizationColor: panel.foreground }
  }

  Column {
    id: column
    width: parent.width
    spacing: Style.space(10)

    Row {
      spacing: Style.space(8)
      Logo {
        width: Style.space(22)
        height: width
        anchors.verticalCenter: parent.verticalCenter
        source: Qt.resolvedUrl("icons/" + Logos.logoFor(panel.current).file + ".svg")
        themed: Logos.logoFor(panel.current).themed === true
      }
      Text {
        anchors.verticalCenter: parent.verticalCenter
        text: "OmaDistro"
        color: panel.foreground
        font.family: panel.fontFamily
        font.pixelSize: Style.font.title
        font.bold: true
      }
    }

    TextField {
      id: field
      width: parent.width
      placeholderText: "Search " + Logos.LOGOS.length + " logos"
      onTextChanged: panel.search = text.toLowerCase()
    }

    Grid {
      id: grid
      columns: 7
      spacing: Style.space(6)
      readonly property real tile: (column.width - spacing * (columns - 1)) / columns

      Repeater {
        model: Logos.LOGOS
        delegate: Rectangle {
          required property var modelData
          readonly property bool chosen: modelData.name === panel.current
          visible: panel.search === "" || modelData.name.toLowerCase().indexOf(panel.search) !== -1
          width: grid.tile
          height: grid.tile
          radius: Style.space(6)
          color: tileHover.hovered || chosen ? Qt.rgba(panel.foreground.r, panel.foreground.g, panel.foreground.b, 0.10) : "transparent"
          border.width: chosen ? Math.max(1, Style.space(2)) : 0
          border.color: Commons.Color.accent

          Logo {
            anchors.horizontalCenter: parent.horizontalCenter
            y: parent.height * 0.14
            width: parent.width * 0.46
            height: width
            source: Qt.resolvedUrl("icons/" + parent.modelData.file + ".svg")
            themed: parent.modelData.themed === true
          }
          Text {
            anchors.horizontalCenter: parent.horizontalCenter
            anchors.bottom: parent.bottom
            anchors.bottomMargin: parent.height * 0.08
            width: parent.width - Style.space(4)
            horizontalAlignment: Text.AlignHCenter
            elide: Text.ElideRight
            text: parent.modelData.name
            textFormat: Text.PlainText
            color: panel.foreground
            font.family: panel.fontFamily
            font.pixelSize: Style.font.caption
          }
          HoverHandler { id: tileHover; cursorShape: Qt.PointingHandCursor }
          TapHandler { onTapped: panel.choose(parent.modelData.name) }
        }
      }
    }

    NumberField {
      label: "Logo size %"
      from: 60
      to: 150
      stepSize: 5
      value: panel.size
      foreground: panel.foreground
      fontFamily: panel.fontFamily
      onModified: function(value) { panel.resize(Math.max(60, Math.min(150, value))) }
    }

    Text {
      visible: panel.message !== ""
      width: parent.width
      text: panel.message
      textFormat: Text.PlainText
      wrapMode: Text.Wrap
      color: panel.muted
      font.family: panel.fontFamily
      font.pixelSize: Style.font.caption
    }
  }
}
