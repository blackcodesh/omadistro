"""Tests for the omadistro script: run with `python3 -I -m unittest discover -s tests` (all in a
throwaway directory; the real shell.json is never touched)."""
import glob
import json
import os
import re
import subprocess
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.dirname(HERE)
SCRIPT = os.path.join(ROOT, "omadistro")


def run(*args):
    env = dict(os.environ, XDG_RUNTIME_DIR=tempfile.gettempdir())
    return subprocess.run([sys.executable, "-I", SCRIPT, *args], capture_output=True, text=True, env=env)


class Case(unittest.TestCase):
    def setUp(self):
        self.dir = tempfile.mkdtemp()
        self.path = os.path.join(self.dir, "shell.json")

    def write(self, config):
        with open(self.path, "w") as f:
            json.dump(config, f)

    def read(self):
        with open(self.path) as f:
            return json.load(f)

    def bar(self, left):
        return {"bar": {"layout": {"left": left, "center": [{"id": "omarchy.clock"}], "right": [{"id": "omarchy.audio"}]}}}


class Setup(Case):
    def test_menu_becomes_the_logo_in_the_same_place(self):
        self.write(self.bar([{"id": "omarchy.menu"}, {"id": "omarchy.workspaces"}, {"id": "blackcode.omadistro"}]))
        self.assertEqual(run("setup", self.path).returncode, 0)
        left = self.read()["bar"]["layout"]["left"]
        self.assertEqual(left, [{"id": "blackcode.omadistro", "logo": "Omarchy"}, {"id": "omarchy.workspaces"}])

    def test_menu_settings_move_to_plugins(self):
        self.write(self.bar([{"id": "omarchy.menu", "extra": 1}, {"id": "blackcode.omadistro"}]))
        run("setup", self.path)
        self.assertIn({"id": "omarchy.menu", "extra": 1}, self.read()["plugins"])

    def test_bare_entry_becomes_the_logo_when_the_bar_has_no_menu(self):
        self.write(self.bar([{"id": "omarchy.workspaces"}, {"id": "blackcode.omadistro"}]))
        run("setup", self.path)
        self.assertEqual(self.read()["bar"]["layout"]["left"][1], {"id": "blackcode.omadistro", "logo": "Omarchy"})

    def test_second_run_changes_nothing(self):
        self.write(self.bar([{"id": "omarchy.menu"}, {"id": "blackcode.omadistro"}]))
        run("setup", self.path)
        before = open(self.path).read()
        out = run("setup", self.path)
        self.assertIn("already set up", out.stdout)
        self.assertEqual(open(self.path).read(), before)

    def test_not_enabled_changes_nothing(self):
        self.write(self.bar([{"id": "omarchy.menu"}]))
        before = open(self.path).read()
        run("setup", self.path)
        self.assertEqual(open(self.path).read(), before)

    def test_bad_json_is_refused(self):
        with open(self.path, "w") as f:
            f.write("{nope")
        self.assertNotEqual(run("setup", self.path).returncode, 0)
        self.assertEqual(open(self.path).read(), "{nope")


class SetLogo(Case):
    def test_sets_the_logo_and_keeps_a_copy(self):
        self.write(self.bar([{"id": "blackcode.omadistro", "logo": "Omarchy"}]))
        self.assertEqual(run("set", "Arch", self.path).returncode, 0)
        self.assertEqual(self.read()["bar"]["layout"]["left"][0]["logo"], "Arch")
        self.assertEqual(len(glob.glob(self.path + ".omadistro-2*")), 1)
        self.assertTrue(os.path.exists(self.path + ".omadistro-original"))

    def test_unknown_logo_is_refused(self):
        self.write(self.bar([{"id": "blackcode.omadistro", "logo": "Omarchy"}]))
        before = open(self.path).read()
        self.assertNotEqual(run("set", "Windows", self.path).returncode, 0)
        self.assertEqual(open(self.path).read(), before)

    def test_without_a_copy_it_says_so(self):
        self.write(self.bar([{"id": "omarchy.menu"}]))
        out = run("set", "Arch", self.path)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("enable the plugin", out.stderr)

    def test_every_logo_name_works(self):
        self.write(self.bar([{"id": "blackcode.omadistro", "logo": "Omarchy"}]))
        for name in run("list").stdout.splitlines():
            self.assertEqual(run("set", name, self.path).returncode, 0, name)
            self.assertEqual(self.read()["bar"]["layout"]["left"][0]["logo"], name)


class Size(Case):
    def test_sets_and_resets_the_size(self):
        self.write(self.bar([{"id": "blackcode.omadistro", "logo": "Omarchy"}]))
        self.assertEqual(run("size", "120", self.path).returncode, 0)
        self.assertEqual(self.read()["bar"]["layout"]["left"][0]["iconSize"], 120)
        run("size", "100", self.path)
        self.assertNotIn("iconSize", self.read()["bar"]["layout"]["left"][0])

    def test_out_of_range_or_not_a_number_is_refused(self):
        self.write(self.bar([{"id": "blackcode.omadistro", "logo": "Omarchy"}]))
        before = open(self.path).read()
        for bad in ("59", "151", "big", "-5", "100.5"):
            self.assertNotEqual(run("size", bad, self.path).returncode, 0, bad)
        self.assertEqual(open(self.path).read(), before)

    def test_logo_change_keeps_the_size(self):
        self.write(self.bar([{"id": "blackcode.omadistro", "logo": "Omarchy", "iconSize": 130}]))
        run("set", "Arch", self.path)
        self.assertEqual(self.read()["bar"]["layout"]["left"][0], {"id": "blackcode.omadistro", "logo": "Arch", "iconSize": 130})

    def test_unswap_drops_the_size(self):
        self.write(self.bar([{"id": "blackcode.omadistro", "logo": "Omarchy", "iconSize": 130}]))
        run("unswap", self.path)
        self.assertEqual(self.read()["bar"]["layout"]["left"], [{"id": "omarchy.menu"}])


class Hardening(Case):
    def layout(self, **sections):
        return {"bar": {"layout": {"left": [], "centerBegin": [], "center": [], "centerEnd": [], "right": [], "tray": [], **sections}}}

    def test_menu_and_copy_in_any_of_the_six_sections(self):
        for section in ("left", "centerBegin", "center", "centerEnd", "right", "tray"):
            self.write(self.layout(**{section: [{"id": "omarchy.menu"}], "right": [{"id": "blackcode.omadistro"}]}
                                   if section != "right" else {"right": [{"id": "omarchy.menu"}, {"id": "blackcode.omadistro"}]}))
            self.assertEqual(run("setup", self.path).returncode, 0, section)
            layout = self.read()["bar"]["layout"]
            self.assertEqual(layout[section][0], {"id": "blackcode.omadistro", "logo": "Omarchy"}, section)
            flat = [e["id"] if isinstance(e, dict) else e for v in layout.values() for e in v]
            self.assertNotIn("omarchy.menu", flat, section)
            self.assertEqual(flat.count("blackcode.omadistro"), 1, section)
            self.assertEqual(run("set", "Arch", self.path).returncode, 0, section)
            self.assertEqual(run("size", "120", self.path).returncode, 0, section)
            self.assertEqual(run("unswap", self.path).returncode, 0, section)
            self.assertEqual(self.read()["bar"]["layout"][section], [{"id": "omarchy.menu"}], section)

    def test_bare_string_entries_are_understood_and_kept(self):
        self.write(self.layout(left=["omarchy.menu", "omarchy.workspaces", "blackcode.omadistro"], right=["omarchy.clock"]))
        self.assertEqual(run("setup", self.path).returncode, 0)
        layout = self.read()["bar"]["layout"]
        self.assertEqual(layout["left"], [{"id": "blackcode.omadistro", "logo": "Omarchy"}, "omarchy.workspaces"])
        self.assertEqual(layout["right"], ["omarchy.clock"])

    def test_a_symlinked_shell_json_stays_a_symlink(self):
        target = os.path.join(self.dir, "dotfiles.json")
        with open(target, "w") as f:
            json.dump(self.layout(left=[{"id": "blackcode.omadistro", "logo": "Omarchy"}]), f)
        os.symlink(target, self.path)
        self.assertEqual(run("set", "Tux", self.path).returncode, 0)
        self.assertTrue(os.path.islink(self.path))
        self.assertEqual(json.load(open(target))["bar"]["layout"]["left"][0]["logo"], "Tux")

    def test_backups_keep_the_original_and_the_newest_three(self):
        self.write(self.layout(left=[{"id": "blackcode.omadistro", "logo": "Omarchy"}]))
        original = open(self.path).read()
        for n, name in enumerate(["Arch", "Debian", "Fedora", "Gentoo", "Kali", "Tux"]):
            run("set", name, self.path)
        self.assertEqual(len(glob.glob(self.path + ".omadistro-2*")), 3)
        self.assertEqual(open(self.path + ".omadistro-original").read(), original)

    def test_old_timestamped_backups_are_promoted_not_lost(self):
        self.write(self.layout(left=[{"id": "blackcode.omadistro", "logo": "Omarchy"}]))
        old = self.path + ".omadistro-20260101-000000"
        with open(old, "w") as f:
            f.write("the true original")
        run("set", "Arch", self.path)
        self.assertEqual(open(self.path + ".omadistro-original").read(), "the true original")

    def test_unswap_moves_the_menu_settings_back(self):
        self.write(self.layout(left=[{"id": "omarchy.menu", "extra": 1}, {"id": "blackcode.omadistro"}]))
        run("setup", self.path)
        self.assertIn({"id": "omarchy.menu", "extra": 1}, self.read()["plugins"])
        run("unswap", self.path)
        data = self.read()
        self.assertEqual(data["bar"]["layout"]["left"], [{"id": "omarchy.menu", "extra": 1}])
        self.assertNotIn("plugins", data)

    def test_non_ascii_is_kept_as_is(self):
        config = self.layout(left=[{"id": "blackcode.omadistro", "logo": "Omarchy"}])
        config["note"] = "مرحبا"
        self.write(config)
        run("set", "Arch", self.path)
        self.assertIn("مرحبا", open(self.path, encoding="utf-8").read())

    def test_comments_give_a_clear_message(self):
        with open(self.path, "w") as f:
            f.write('{ // comment\n "bar": {} }')
        out = run("set", "Arch", self.path)
        self.assertNotEqual(out.returncode, 0)
        self.assertIn("comments", out.stderr)


class Unswap(Case):
    def test_puts_the_menu_back_in_the_same_place(self):
        self.write(self.bar([{"id": "blackcode.omadistro", "logo": "Tux"}, {"id": "omarchy.workspaces"}]))
        run("unswap", self.path)
        self.assertEqual(self.read()["bar"]["layout"]["left"], [{"id": "omarchy.menu"}, {"id": "omarchy.workspaces"}])

    def test_swap_then_unswap_round_trips(self):
        self.write(self.bar([{"id": "omarchy.menu"}, {"id": "omarchy.workspaces"}, {"id": "blackcode.omadistro"}]))
        run("setup", self.path)
        run("unswap", self.path)
        self.assertEqual(self.read()["bar"]["layout"]["left"], [{"id": "omarchy.menu"}, {"id": "omarchy.workspaces"}])


class Assets(unittest.TestCase):
    def test_logo_list_matches_logos_js_and_manifest(self):
        js = open(os.path.join(ROOT, "Logos.js")).read()
        js_names = re.findall(r'name: "([^"]+)"', js)
        self.assertEqual(run("list").stdout.splitlines(), js_names)
        manifest = json.load(open(os.path.join(ROOT, "manifest.json")))
        self.assertEqual(manifest["barWidget"]["schema"][0]["options"], js_names)

    def test_every_logo_has_its_icon_file(self):
        js = open(os.path.join(ROOT, "Logos.js")).read()
        for file in re.findall(r'file: "([^"]+)"', js):
            self.assertTrue(os.path.exists(os.path.join(ROOT, "icons", file + ".svg")), file)


if __name__ == "__main__":
    unittest.main()
