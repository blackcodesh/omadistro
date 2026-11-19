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
        self.assertEqual(len(glob.glob(self.path + ".omadistro-*")), 1)

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
