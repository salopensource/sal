#!/usr/bin/python


import os
import sys

sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist, munkicommon


PREFS_TO_GET = (
    'ManagedInstallDir',
    'SoftwareRepoURL',
    'ClientIdentifier',
    'LogFile',
    'LoggingLevel',
    'LogToSyslog',
    'InstallAppleSoftwareUpdates',
    'AppleSoftwareUpdatesOnly',
    'SoftwareUpdateServerURL',
    'DaysBetweenNotifications',
    'LastNotifiedDate',
    'UseClientCertificate',
    'SuppressUserNotification',
    'SuppressAutoInstall',
    'SuppressStopButtonOnInstall',
    'PackageVerificationMode',
    'FollowHTTPRedirects',
    'UnattendedAppleUpdates',
    'ClientCertificatePath',
    'ClientKeyPath',
    'LastAppleSoftwareUpdateCheck',
    'LastCheckDate',
    'LastCheckResult',
    'LogFile',
    'SoftwareRepoCACertificate',
    'SoftwareRepoCAPath',
    'PackageURL',
    'CatalogURL',
    'ManifestURL',
    'IconURL',
    'ClientResourceURL',
    'ClientResourcesFilename',
    'HelpURL',
    'UseClientCertificateCNAsClientIdentifier',
    'AdditionalHttpHeaders',
    'SuppressLoginwindowInstall',
    'InstallRequiresLogout',
    'ShowRemovalDetail',
    'MSULogEnabled',
    'MSUDebugLogEnabled',
    'LocalOnlyManifest',
    'UnattendedAppleUpdates')


def main():
    # Skip a manual check
    if len(sys.argv) > 1:
        if sys.argv[1] == 'manualcheck':
            munkicommon.display_debug2("Manual check: skipping MunkiInfo Plugin")
            exit(0)

    data = {pref: str(munkicommon.pref(pref)) for pref in PREFS_TO_GET}
    add_plugin_results('MunkiInfo', data)


def add_plugin_results(plugin, data, historical=False):
    """Add data to the shared plugin results plist.

    This function creates the shared results plist file if it does not
    already exist; otherwise, it adds the entry by appending.

    Args:
        plugin (str): Name of the plugin returning data.
        data (dict): Dictionary of results.
        historical (bool): Whether to keep only one record (False) or
            all results (True). Optional, defaults to False.
    """
    plist_path = '/usr/local/sal/plugin_results.plist'
    if os.path.exists(plist_path):
        plugin_results = FoundationPlist.readPlist(plist_path)
    else:
        plugin_results = []

    plugin_results.append({'plugin': plugin, 'historical': historical, 'data': data})
    FoundationPlist.writePlist(plugin_results, plist_path)


if __name__ == '__main__':
    main()
