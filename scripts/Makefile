USE_PKGBUILD=1
include /usr/local/share/luggage/luggage.make
PACKAGE_VERSION=0.4.0
TITLE=sal_scripts
PACKAGE_NAME=sal_scripts
REVERSE_DOMAIN=com.github.salopensource
PAYLOAD=\
	pack-yaml \
	pack-sal-submit

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

pack-sal-submit: l_munki
	@sudo ${CP} postflight ${WORK_D}/usr/local/munki/postflight
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/postflight
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/postflight
	@sudo ${CP} preflight ${WORK_D}/usr/local/munki/preflight
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/preflight
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/preflight
	@sudo ${CP} sal-postflight ${WORK_D}/usr/local/munki/postflight.d/sal-postflight
	@sudo chown -R root:wheel ${WORK_D}/usr/local/munki/postflight.d/sal-postflight
	@sudo chmod -R 755 ${WORK_D}/usr/local/munki/postflight.d/sal-postflight
