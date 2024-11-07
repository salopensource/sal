#!/bin/bash

current_version="4.4.0"
pushd `dirname $0` > /dev/null
SCRIPTPATH=`pwd`


# based on http://tgoode.com/2014/06/05/sensible-way-increment-bundle-version-cfbundleversion-xcode
if git rev-parse --is-inside-work-tree 2> /dev/null > /dev/null; then
    echo "Setting Version to Git rev-list --count"
    build_number=$(git rev-list HEAD --count)
    # This will always be one commit behind, so this makes it current
    build_number=$((build_number+1))
    /usr/bin/defaults write "${SCRIPTPATH}/sal/version.plist" version "$current_version.$build_number"
    /usr/bin/plutil -convert xml1 "${SCRIPTPATH}/sal/version.plist"
else
    echo "Not in a Git repo, not setting Version"
fi
popd > /dev/null
