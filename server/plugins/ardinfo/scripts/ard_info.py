#!/usr/local/sal/Python.framework/Versions/3.8/bin/python3


import sal

from Foundation import CFPreferencesCopyAppValue


def main():
    bundle_id = "com.apple.RemoteDesktop.plist"

    sal_key = "ARD_Info_{}"
    prefs_key_prefix = "Text{}"

    data = {
        sal_key.format(i): CFPreferencesCopyAppValue(prefs_key_prefix.format(i), bundle_id) or ""
        for i in range(1, 5)}

    sal.add_plugin_results('ARD_Info', data)


if __name__ == "__main__":
    main()
