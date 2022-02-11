#!/usr/local/sal/Python.framework/Versions/Current/bin/python3


import sys

import sal
sys.path.append('/usr/local/munki')
from munkilib import munkicommon


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
            # Manual check: skipping MunkiInfo Plugin
            exit(0)

    data = {pref: str(munkicommon.pref(pref)) for pref in PREFS_TO_GET}
    sal.add_plugin_results('MunkiInfo', data)


if __name__ == '__main__':
    main()
