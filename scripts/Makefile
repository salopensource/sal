USE_PKGBUILD=1
include /usr/local/share/luggage/luggage.make
PACKAGE_VERSION=0.2.0
TITLE=munki_scripts
PACKAGE_NAME=munki_scripts
REVERSE_DOMAIN=de.hires-berlin
PAYLOAD=\
	pack-yaml \
	pack-munki-submit

pack-yaml: l_usr_local
	@sudo find . -name "*.pyc" -exec rm -rf {} \;
	@sudo mkdir -p ${WORK_D}/usr/local/sal/yaml
	@sudo ${CP} -R yaml ${WORK_D}/usr/local/sal
	@sudo chown -R root:wheel ${WORK_D}/usr/local/sal/yaml
	@sudo chmod -R 755 ${WORK_D}/usr/local/sal/yaml

l_munki: l_usr_local
	@sudo mkdir -p ${WORK_D}/usr/local/munki/postflight.d
	@sudo chown root:wheel ${WORK_D}/usr/local/munki/postflight.d
	@sudo mkdir -p ${WORK_D}/usr/local/munki/preflight.d
	@sudo chown root:wheel ${WORK_D}/usr/local/munki/preflight.d

pack-munki-submit: l_munki
	@sudo ${CP} postflight ${WORK_D}/usr/local/munki/postflight
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/postflight
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/postflight
	@sudo ${CP} preflight ${WORK_D}/usr/local/munki/preflight
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/preflight
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/preflight
	@sudo ${CP} sal-postflight ${WORK_D}/usr/local/munki/postflight.d/sal-postflight
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/postflight.d/sal-postflight
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/postflight.d/sal-postflight
	@sudo ${CP} mwa-postflight ${WORK_D}/usr/local/munki/postflight.d/mwa-postflight
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/postflight.d/mwa-postflight
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/postflight.d/mwa-postflight
	@sudo ${CP} munkiwebadmin-config ${WORK_D}/usr/local/munki/postflight.d/munkiwebadmin-config
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/postflight.d/munkiwebadmin-config
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/postflight.d/munkiwebadmin-config
	@sudo ${CP} mwa-preflight ${WORK_D}/usr/local/munki/preflight.d/mwa-preflight
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/preflight.d/mwa-preflight
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/preflight.d/mwa-preflight
