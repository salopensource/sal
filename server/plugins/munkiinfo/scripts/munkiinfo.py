#!/usr/bin/python

import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
from munkilib import munkicommon
import os


def main():
    # Skip a manual check
    if len(sys.argv) > 1:
        if sys.argv[1] == 'manualcheck':
            munkicommon.display_debug2("Manual check: skipping MunkiInfo Plugin")
            exit(0)

    prefs_to_get = [
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
        'UnattendedAppleUpdates'
    ]
    plist_path = '/usr/local/sal/plugin_results.plist'
    if os.path.exists(plist_path):
        plist = FoundationPlist.readPlist(plist_path)
    else:
        plist = []
    result = {}
    result['plugin'] = 'MunkiInfo'
    result['historical'] = False
    data = {}
    for the_pref in prefs_to_get:
        data[the_pref] = str(munkicommon.pref(the_pref))

    result['data'] = data
    plist.append(result)
    FoundationPlist.writePlist(plist, plist_path)


if __name__ == '__main__':
    main()
