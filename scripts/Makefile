USE_PKGBUILD=1
include /usr/local/share/luggage/luggage.make
PACKAGE_VERSION=0.1.0
TITLE=sal_scripts
PACKAGE_NAME=sal_scripts
REVERSE_DOMAIN=com.grahamgilbert
PAYLOAD=\
	pack-yaml \
	pack-sal-submit
	
pack-yaml: l_usr_local
	@sudo mkdir -p ${WORK_D}/usr/local/sal/yaml
	@sudo ${CP} -R yaml ${WORK_D}/usr/local/sal
	@sudo chown -R root:wheel ${WORK_D}/usr/local/sal/yaml
	@sudo chmod -R 755 ${WORK_D}/usr/local/sal/yaml

pack-sal-submit: l_usr_local
	@sudo mkdir -p ${WORK_D}/usr/local/munki
	@sudo ${INSTALL} -m 755 -g wheel -o root postflight ${WORK_D}/usr/local/munki/