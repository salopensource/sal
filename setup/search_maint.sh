#!/usr/bin/env bash

SAL_MAINT=`dirname $0`
SAL_PATH=`(cd $SAL_MAINT/.. && pwd)`
cd $SAL_PATH
export PYTHONPATH=$SAL_PATH/sal/sal:$PYTHONPATH
export DJANGO_SETTINGS_MODULE='sal.settings'
 
$SAL_PATH/sal_env/bin/python3 manage.py search_maintenance
