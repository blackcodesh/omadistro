# OmaDistro: change the Omarchy logo on your bar

![OmaDistro: change the Omarchy logo on your bar](poster/13-alshareedah22-omadistro-detail.webp)

The icon at the top-left of Omarchy's bar is the menu button. OmaDistro lets you swap its
logo in one click: the Omarchy logo, the Arch Linux logo, or one of 42 other distro logos,
each in its official color, at the size you like. The menu itself stays Omarchy's own, so clicking it, scrolling on
it and its tooltip work as before. That is all this plugin does.

## Install

```bash
omarchy plugin add https://github.com/alshareedah22/omadistro --enable
```

Nothing else to do: when enabled, it turns the menu on your bar into the logo copy, in the
same place, with the Omarchy logo. No swap, no config.

## Change the logo

- **Right-click the logo** to open the picker: a grid of all 44 logos with a search box.
  Click one and the bar updates.
- Or from a terminal: `omadistro set Arch` (the script is in the plugin folder, and
  `omadistro list` prints every name).
- **Size**: the picker has a "Logo size %" box (60 to 150, 100 is Omarchy's full 16 px icon;
  the picker stays open while you adjust it). From a terminal: `omadistro size 120`.
- Or set `"logo": "Arch"` (and `"iconSize": 120`) on the plugin's entry in the bar layout of
  `~/.config/omarchy/shell.json`.
- Or open the picker from a keybinding. Add this to `~/.config/hypr/bindings.lua`:

```lua
o.bind("SUPER + CTRL + ALT + D", "Menu logo", "qs -p /usr/share/omarchy/shell ipc call omadistro togglePicker")
```

Right-click on the logo used to open a terminal in Omarchy; SUPER+RETURN still does.

## What it changes

On first enable it edits `~/.config/omarchy/shell.json` once: the `omarchy.menu` entry in the
bar layout becomes `{"id": "blackcode.omadistro", "logo": "Omarchy"}`, and the menu's own
settings (if any) move to the `plugins` list, where Omarchy keeps settings of a widget that is
not in the layout. Every write is atomic and keeps the previous file next to it as
`shell.json.omadistro-<time>`.

## Remove

Put Omarchy's own menu back first, while the plugin is still installed:

```bash
python3 -I ~/.config/omarchy/plugins/blackcode.omadistro/omadistro unswap
omarchy plugin remove blackcode.omadistro
```

`unswap` turns the logo back into `omarchy.menu` in the same place and changes nothing else.

## Logos

Omarchy and Arch are drawn for this plugin family; the other distro logos come from Simple
Icons. They are trademarks of their projects, shown unaltered in their brand colors. Black
brand logos (AlmaLinux, Slackware, Nobara, MX Linux, SUSE) are drawn in the bar's text color so
they show on a dark bar. Sources and licenses: [`icons/LOGOS.md`](icons/LOGOS.md).

## Tests

```bash
python3 -I -m unittest discover -s tests
```

They run in a throwaway directory and never touch your shell.json.

## Files

| File | What it is |
|------|------------|
| `manifest.json` | Plugin id `blackcode.omadistro`, the `logo` and `iconSize` settings |
| `Panel.qml` | Hosts Omarchy's menu, hides its glyph and draws the logo at your size |
| `LogoPicker.qml` | The picker (grid and search) |
| `Service.qml` | Starts the first-run setup, the IPC to open the picker |
| `Logos.js` | The 44 logos |
| `omadistro` | Command-line tool: `setup`, `set`, `size`, `list`, `unswap` |
| `icons/` | The logo drawings |
| `poster/`, `preview.png` | Cover image |

MIT licensed.
