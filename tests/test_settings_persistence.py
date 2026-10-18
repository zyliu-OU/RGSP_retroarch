"""Exercise restart argv and the supervisor's persistent fallback/stop path."""
from pathlib import Path
import os
import subprocess
import tempfile
import time
import unittest

PROJECT = Path(__file__).resolve().parents[1]
SOURCE = Path(os.environ.get('RGSP_RETROARCH_SOURCE', PROJECT.parent / 'retroarch-v1.22.0-src'))


class SettingsPersistence(unittest.TestCase):
    @unittest.skipUnless((SOURCE / 'frontend/drivers/platform_unix.c').is_file(), 'RetroArch checkout needed')
    def test_restart_retains_config_and_full_executable_path(self):
        source = (SOURCE / 'frontend/drivers/platform_unix.c').read_text()
        function = source[source.index('static void frontend_unix_exec('):source.index('static void frontend_unix_exitspawn(')]
        harness = r'''
#include <assert.h>
#include <stdbool.h>
#include <stddef.h>
#include <string.h>
#include <unistd.h>
#define HAVE_RGSP 1
#define RARCH_PATH_CONFIG 1
static const char *config;
static const char *expected_path;
static int syncs;
static const char *path_get(int key) { assert(key == RARCH_PATH_CONFIG); return config; }
static bool string_is_empty(const char *s) { return !s || !*s; }
static void fake_sync(void) { ++syncs; }
static int fake_exec(const char *path, char *const argv[]) {
    assert(!strcmp(path, expected_path));
    assert(!strcmp(argv[0], expected_path));
    if (config && *config) {
        assert(!strcmp(argv[1], "--config"));
        assert(!strcmp(argv[2], config));
        assert(argv[3] == NULL);
    } else assert(argv[1] == NULL);
    return -1;
}
#define sync fake_sync
#define execv fake_exec
'''
        harness += function + r'''
int main(void) {
    expected_path = "/mnt/vendor/deep/retro/retroarch";
    config = "/mnt/shared/configfiles/retroarch/retroarch.cfg";
    frontend_unix_exec(expected_path, false);
    config = "/mnt/shared/config with spaces/retroarch-stock.cfg";
    frontend_unix_exec(expected_path, false);
    config = "";
    frontend_unix_exec(expected_path, false);
    assert(syncs == 3);
    return 0;
}
'''
        with tempfile.TemporaryDirectory() as name:
            c = Path(name) / 'restart.c'
            exe = Path(name) / 'restart'
            c.write_text(harness)
            subprocess.run(['cc', '-D_DEFAULT_SOURCE', str(c), '-o', str(exe)], check=True)
            subprocess.run([str(exe)], check=True)

    def test_fallback_saves_across_two_supervisor_sessions(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            for directory in ('vendor/deep/retro', 'shared/configfiles/retroarch', 'shared/logs', 'configroot/retroarch', 'run', 'log'):
                (root / directory).mkdir(parents=True)
            main_config = root / 'shared/configfiles/retroarch/retroarch.cfg'
            main_config.write_text('config_save_on_exit = "true"\nuser_setting = "main"\n')
            main = root / 'vendor/deep/retro/retroarch'
            main.write_text('#!/bin/sh\nexit 1\n')
            stock = main.with_name('retroarch-stock')
            stock.write_text('''#!/bin/sh
cfg=$2
trap 'sleep 0.1; printf "user_setting = \\"saved\\"\\n" >> "$cfg"; exit 0' TERM
printf '%s\\n' "$cfg" > "'''+str(root / 'ready')+'''"
while :; do sleep 0.05; done
''')
            for binary in (main, stock):
                binary.chmod(0o755)
            script = (PROJECT / 'firmware/overlay/etc/init.d/S99retroarch').read_text()
            for old, new in (('/mnt/vendor', root / 'vendor'), ('/mnt/mmc', root / 'mmc'), ('/mnt/shared', root / 'shared'), ('/.config', root / 'configroot'), ('/var/log', root / 'log'), ('/run/', str(root / 'run') + '/')):
                script = script.replace(old, str(new))
            script = script.replace('mountpoint -q ', '/bin/true ')
            script = script.replace('/usr/local/sbin/rgsp-speaker', '/bin/true')
            script = script.replace('/sbin/poweroff', str(root / 'unexpected-poweroff'))
            script = script.replace('sleep 2', 'sleep 0.05').replace('sleep 1', 'sleep 0.05')
            runner = root / 'S99retroarch'
            runner.write_text(script)
            runner.chmod(0o755)
            stock_config = main_config.with_name('retroarch-stock.cfg')
            try:
                for session in range(2):
                    (root / 'ready').unlink(missing_ok=True)
                    subprocess.run([str(runner), 'start'], check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                    deadline = time.monotonic() + 8
                    while not (root / 'ready').exists():
                        if time.monotonic() > deadline:
                            self.fail((root / 'log/rgsp-retroarch.log').read_text())
                        time.sleep(0.02)
                    self.assertEqual((root / 'ready').read_text().strip(), str(stock_config))
                    if session:
                        self.assertIn('user_setting = "saved"', stock_config.read_text())
                    subprocess.run([str(runner), 'stop'], check=True, timeout=5)
                    self.assertEqual(stock_config.read_text().count('user_setting = "saved"'), session + 1)
                self.assertEqual(main_config.read_text(), 'config_save_on_exit = "true"\nuser_setting = "main"\n')
                self.assertFalse((root / 'run/rgsp-retroarch.pid').exists())
                self.assertNotIn('powering off', (root / 'log/rgsp-retroarch.log').read_text())
            finally:
                subprocess.run([str(runner), 'stop'], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


if __name__ == '__main__':
    unittest.main()
