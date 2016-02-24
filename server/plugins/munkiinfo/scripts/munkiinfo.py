#!/usr/bin/python

import sys
sys.path.append('/usr/local/munki')
from munkilib import FoundationPlist
from munkilib import munkicommon

def main():
    # Skip a manual check
    if len(sys.argv) > 1:
    if sys.argv[1] == 'manualcheck':
        munkicommon.display_debug2("Manual check: skipping")
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
        'LocalOnlyManifest'
    ]

    for the_pref in prefs_to_get:
        print the_pref, munkicommon.pref(the_pref)

if __name__ == '__main__':
    main()
