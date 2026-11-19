.pragma library

// The logos the menu icon can show. `themed` logos are black brands, drawn in the bar's text
// color so they show on a dark bar. The same names, in the same order, are in the `omadistro`
// script (tests/test_omadistro.py checks that). Sources and licenses: icons/LOGOS.md.

var PLUGIN_ID = "blackcode.omadistro"
var MENU_ID = "omarchy.menu"

var LOGOS = [
  { name: "Omarchy", file: "menu-omarchy" }, { name: "Arch", file: "menu-arch" },
  { name: "Debian", file: "distro-debian" }, { name: "Ubuntu", file: "distro-ubuntu" },
  { name: "Fedora", file: "distro-fedora" }, { name: "Linux Mint", file: "distro-linuxmint" },
  { name: "openSUSE", file: "distro-opensuse" }, { name: "Manjaro", file: "distro-manjaro" },
  { name: "EndeavourOS", file: "distro-endeavouros" }, { name: "Gentoo", file: "distro-gentoo" },
  { name: "Void", file: "distro-voidlinux" }, { name: "NixOS", file: "distro-nixos" },
  { name: "Alpine", file: "distro-alpinelinux" }, { name: "Pop!_OS", file: "distro-popos" },
  { name: "elementary OS", file: "distro-elementary" }, { name: "Zorin OS", file: "distro-zorin" },
  { name: "Kali", file: "distro-kalilinux" }, { name: "Rocky Linux", file: "distro-rockylinux" },
  { name: "AlmaLinux", file: "distro-almalinux", themed: true }, { name: "Red Hat", file: "distro-redhat" },
  { name: "CentOS", file: "distro-centos" }, { name: "Slackware", file: "distro-slackware", themed: true },
  { name: "CachyOS", file: "distro-cachyos" }, { name: "Garuda", file: "distro-garudalinux" },
  { name: "Artix", file: "distro-artixlinux" }, { name: "Asahi", file: "distro-asahilinux" },
  { name: "Nobara", file: "distro-nobaralinux", themed: true }, { name: "KDE neon", file: "distro-kdeneon" },
  { name: "Kubuntu", file: "distro-kubuntu" }, { name: "Xubuntu", file: "distro-xubuntu" },
  { name: "Lubuntu", file: "distro-lubuntu" }, { name: "Ubuntu MATE", file: "distro-ubuntumate" },
  { name: "deepin", file: "distro-deepin" }, { name: "Solus", file: "distro-solus" },
  { name: "MX Linux", file: "distro-mxlinux", themed: true }, { name: "Qubes OS", file: "distro-qubesos" },
  { name: "Tails", file: "distro-tails" }, { name: "Parrot", file: "distro-parrotsecurity" },
  { name: "Raspberry Pi", file: "distro-raspberrypi" }, { name: "SUSE", file: "distro-suse", themed: true },
  { name: "FreeBSD", file: "distro-freebsd" }, { name: "OpenBSD", file: "distro-openbsd" },
  { name: "NetBSD", file: "distro-netbsd" },
  { name: "Tux", file: "distro-linux" }
]

// An unknown name shows the Omarchy logo.
function logoFor(name) {
  for (var i = 0; i < LOGOS.length; i++) if (LOGOS[i].name === name) return LOGOS[i]
  return LOGOS[0]
}

// The menu's own settings: the shell keeps a widget's settings in plugins[] when the widget is
// not in the layout.
function menuSettingsFrom(config) {
  var plugins = config && Array.isArray(config.plugins) ? config.plugins : []
  for (var i = 0; i < plugins.length; i++) {
    if (plugins[i] && plugins[i].id === MENU_ID) {
      var out = {}
      for (var k in plugins[i]) if (k !== "id") out[k] = plugins[i][k]
      return out
    }
  }
  return {}
}
