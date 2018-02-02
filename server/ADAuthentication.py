# -*- coding: utf-8 -*-
"""
# MS Active Directory (AD) Authentication

> ActiveDirectory/LDAP authentication backend for SAL with ldap group to business unit mapping.

This class is a django authentication backend with ActiveDirectory/LDAP integration for [SAL](https://github.com/salopensource).
* It binds to the configured AD/LDAP server with username and password from the SAL/django user login.
* Creates a SAL/django user with field information from AD/LDAP (no password is stored in django!)
* Sets SAL user profile (GA, RW, RO) based on their AD/LDAP group.
* Assigns users to SAL business units based on their AD/LDAP group.
* Updates the user profile and business unit assignment at every login of the user.

## Requirements

* **python-ldap**: pip install python-ldap

## Settings

Following settings can/need to be configured in the django `settings.py` file to get this ActiveDirectory authentication backend to work.

### AUTHENTICATION_BACKENDS (important)

Make sure that the Active Directory authentication is configured as authentication backend.

```Python

AUTHENTICATION_BACKENDS = [
    'server.ADAuthentication.ADAuthentication',
    'django.contrib.auth.backends.ModelBackend',
]
```

### AUTH_LDAP_SERVER_URI (mandatory)

URL of the AD/LDAP server.

```Python
AUTH_LDAP_SERVER_URI = 'ldaps://hostname.domain.com:636'
```

### AUTH_LDAP_USER_DOMAIN

Domain of the AD/LDAP server. This domain will be added to the username if not yet specified.

```Python
AUTH_LDAP_USER_DOMAIN = ‘domain.com’
```

`username` will be converted to `username@domain.com` (domain.com = `AUTH_LDAP_USER_DOMAIN`) for the AD/LDAP authentication. The domain will only get appended to the username if the username does **not** end with the configured domain.

### AUTH_LDAP_USER_SEARCH (mandatory)

AD/LDAP search base for the user object.

```Python
AUTH_LDAP_USER_SEARCH = 'DC=department,DC=ads,DC=company,DC=com'
```

### AUTH_LDAP_USER_ATTR_MAP

Mapping of the AD/LDAP attributes to django attributes. If these settings are not configured, these default values are used.

```Python
AUTH_LDAP_USER_ATTR_MAP = {
    "username": "sAMAccountName",
    "first_name": "givenName",
    "last_name": "sn",
    "email": "mail"
}
```

### AUTH_LDAP_TRUST_ALL_CERTIFICATES

If you have a self signed certificate or an unknown certificate to the django server, you need to disable the certificate check.
```Python
AUTH_LDAP_TRUST_ALL_CERTIFICATES = True
```

### AUTH_LDAP_USER_PREFIX

Django users that where created via AD/LDAP recieve the ldap_ preffix. (`username` becomes `ldap_username`). This allows to have local django users and AD/LDAP users in coexistence. Furthermore, local django users and AD/LDAP users are distinguished very easy.

```Python
AUTH_LDAP_USER_PREFIX = 'ldap_'
```

### AUTH_LDAP_USER_PROFILE (important)

Mapping of the user profile level (`GA` = Global Admin, `RW` = Read & Write, `RO` = Read Only, `SO` = Stats Only (*not implemented in SAL*)) to AD/LDAP groups. Mapping is a dictionary, where the key is the user profile level and the value corresponds to the AD/LDAP group. The group can be a single group or a list/tuple of AD/LDAP groups.

```Python
AUTH_LDAP_USER_PROFILE = {
                            'RO': ('CN=users-all,DC=department,DC=ad,DC=company,DC=com',),
                            'RW': ('CN=service-desk,DC=department,DC=ad,DC=company,DC=com',
                                   'CN=group-leader,OU=group,DC=department,DC=ad,DC=company,DC=com'),
                            'GA': 'CN=admin,DC=department,DC=ad,DC=company,DC=com',
                        }
```

The order of the user profile check is from `GA` to `RO` respectively `SO`. If a user is member of the `GA` **and** `RO` group, the assigned user profile level is `GA`.

### AUTH_LDAP_USER_TO_BUSINESS_UNIT (important)

Mapping of AD/LDAP groups to business units. Mapping is a dictionary, where the key is the name of the business unit and the value corresponds to the AD/LDAP group. The group can be a single group or a list/tuple of AD/LDAP groups.

```Python
AUTH_LDAP_USER_TO_BUSINESS_UNIT = {
                            '#ALL_BU':          ('CN=service-desk,DC=department,DC=ad,DC=company,DC=com',
                                                 'CN=group-leader,DC=department,DC=ad,DC=company,DC=com',),
                            'BusinessUnitU1':   ('CN=group-member,OU=group1,DC=department,DC=ad,DC=company,DC=com',),
                            'BusinessUnitU1':   ('CN=group-member,OU=group2,DC=department,DC=ad,DC=company,DC=com',),
                            'BusinessUnitU3':    'CN=group-member,OU=group3,DC=department,DC=ad,DC=company,DC=com',
                        }
```

**Attention**: `#ALL_BU` is a special business unit. All users in this configured groups get access to all existing business units.

## Logging

If something does not work as expected, an extensive debug logging can be turned on. This is implemented with the python logging module and can be configured in the django settings.

```Python
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '%(asctime)-15s %(levelname)-7s %(filename)s:%(lineno)-4d: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': '/tmp/sal.log',
            'formatter': 'standard',
        },
    },
    'loggers': {
        'server': {
            'handlers': ['file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}
```
With this configuration everything is logged to `/tmp/sal.log`. Make sure that you turn off this option in production environment!

## FAQ

### Can existing django users with identical usernames coexist with new AD/LDAP users?

Yes: This can be accomplished with the setting `AUTH_LDAP_USER_PREFIX` very easily.
This configured prefix will be added to the django username, therefore existing django users with the same username as users in the AD/LDAP should still be able to login (the local django authentication should have a higher priority).

### Is it possible to have a user with readonly rights in specific business unit and with write rights in a different one?

No: Unfortunately this is not possible by design of SAL. A user does always have **one** user profile which is valid for all assigned business unit.

### What happens if the authenticated user is not in any of the configured user profiles (GA, RW, RO)?

Then the default user profile is set, which is read only (RO). Defined at `UserProfile._meta.get_field('level').get_default()`.

### Can a user get assigned to all existing business units?

This is possible with business unit `#ALL_BU` in the `AUTH_LDAP_USER_TO_BUSINESS_UNIT` configuration.

### Assigned business units in SAL get reset every time a user logs in?

The user profile and all assigned business units of a user get a reset every time a user logs in.
Otherwise it is not possible to ensure that users get removed from business units from they should have no access anymore.
Therefore it is not possible and recommended to mix the assignment between SAL and the AD/LDAP configuration.

### Does this authentication work with another ldap implementation than AD/LDAP as well?

May be! But it is not tested or guaranteed. There are some AD/LDAP specific notations used to get nested groups (`memberOf:1.2.840.113556.1.4.1941:=`),
therefore I would not trust on a connection to another ldap implementation.

## Possible improvements

There are always things which can be improved!

* **Bind with service account**. At the moment the AD/LDAP connection is initiated with the authenticated user. It could be that this user does not have the permissions to access the group memberships. Therefore AD/LDAP bind with a service account could be very useful.
* **Make it work with other ldap implementations than AD/LDAP**. At the moment, this authentication works with AD/LDAP only. May be someone can test and adapt it for other ldap implementation as well. Note: Take care of the nested groups.

"""

__author__ = "Basil Neff"
__email__ = "basil.neff@unibas.ch"
__version__ = "1.0.0"



from django.contrib.auth.models import User
from models import UserProfile, BusinessUnit

from django.conf import settings

import logging
import ldap

class ADAuthentication:

    logger = logging.getLogger(__name__)

    # Authentication Method: This is called by the standard Django login procedure
    def authenticate(self, username=None, password=None):

        # Check if ldap server is set
        if settings.AUTH_LDAP_SERVER_URI is None:
            self.logger.error('AUTH_LDAP_SERVER_URI not defined in settings!')
            raise Exception("AUTH_LDAP_SERVER_URI not defined in settings!")

        self.logger.info('Authenticate user %s in AD/LDAP %s' % (username, settings.AUTH_LDAP_SERVER_URI))

        # Check if authentication should trust all AD certificates
        if settings.AUTH_LDAP_TRUST_ALL_CERTIFICATES:
            ldap.set_option(ldap.OPT_X_TLS_REQUIRE_CERT, ldap.OPT_X_TLS_ALLOW)

        ldap_connection = ldap.initialize(settings.AUTH_LDAP_SERVER_URI)
        # https://stackoverflow.com/questions/18793040/python-ldap-not-able-to-bind-successfully
        ldap_connection.set_option(ldap.OPT_REFERRALS, 0)

        # Check if domain is already at the end of the username
        try:
            if str(username).lower().endswith(str(settings.AUTH_LDAP_USER_DOMAIN).lower()):
                username_ldap_bind = username
            else:
                username_ldap_bind = "%s@%s" % (username, settings.AUTH_LDAP_USER_DOMAIN)
                self.logger.debug('Domain %s is not part of the given username %s, add it to bind to ldap: %s' %
                                  (settings.AUTH_LDAP_USER_DOMAIN, username, username_ldap_bind))
        except Exception as ex:
            self.logger.warn('AUTH_LDAP_USER_DOMAIN not defined in django settings. Do not append domain to username for ldap authentication')
            username_ldap_bind = username

        # Bind to ldap
        ##############
        try:
            self.__ldap_bind(ldap_connection=ldap_connection, username=username_ldap_bind, password=password)
        except Exception as ex:
            self.logger.error('Could not bind to ldap (%s) as user %s. User therefore not authenticated.' %
                              (settings.AUTH_LDAP_SERVER_URI, username))
            self.logger.info('Bind exception message: %s' % ex.message)
            self.logger.debug(ex)
            return None

        # Get Ldap User Object
        ldap_user_fields = self.__get_user_from_ldap(ldap_connection, username)
        if ldap_user_fields is None:
            self.logger.error('Could not get ldap user with username %s. User therefore not authorized!' % username)
            return None
        else:
            self.logger.debug('User %s from ldap received.' % (username))

        try:
            ldap_username = ldap_user_fields[settings.AUTH_LDAP_USER_ATTR_MAP['username']][0]
            self.logger.debug('Username of %s in ldap: %s' % (username, ldap_username))
        except NameError as ne:
            self.logger.warn('Could not get username from ldap fields for user %s: %s' % (username, ne.message))
            self.logger.debug('Probably AUTH_LDAP_USER_ATTR_MAP["username"] in settings not defined, use normal username %s as ldap_username.' % username)
            ldap_username = username

        # Django username, may have a prefix (AUTH_LDAP_USER_PREFIX) compared to login
        try:
            username_django = '%s%s' % (settings.AUTH_LDAP_USER_PREFIX, ldap_username)
        except NameError:
            username_django = ldap_username
        self.logger.debug('Username of %s in django: %s' % (ldap_username, username_django))


        # Get fields for django user from ldap
        ######################################
        # first_name
        try:
            first_name = ldap_user_fields[settings.AUTH_LDAP_USER_ATTR_MAP['first_name']][0]
        except Exception as ex:
            self.logger.warn('Could not get first_name from ldap fields (several reasons: ldap field not set, AUTH_LDAP_USER_ATTR_MAP for first_name): %s' % ex.message)
            first_name = None
        #  last_name
        try:
            last_name = ldap_user_fields[settings.AUTH_LDAP_USER_ATTR_MAP['last_name']][0]
        except Exception as ex:
            self.logger.warn('Could not get last_name from ldap fields (several reasons: ldap field not set, AUTH_LDAP_USER_ATTR_MAP for last_name): %s' % ex.message)
            last_name = None
        # Email
        try:
            email = ldap_user_fields[settings.AUTH_LDAP_USER_ATTR_MAP['email']][0]
        except Exception as ex:
            self.logger.warn('Could not get last_name from ldap fields (several reasons: ldap field not set, AUTH_LDAP_USER_ATTR_MAP for email): %s' % ex.message)
            email = None

        # Get/Create django user
        ########################
        django_user = self.__get_or_create_django_user(username_django, first_name=first_name, last_name=last_name, email=email)
        # Reset staff und superuser fields at login
        django_user.is_staff = False
        django_user.is_superuser = False

        # User Profile (level: GA/RW/RO/SO)
        ###################################
        user_profile = None
        # GA = Global Admin
        #------------------
        user_profile_groups = None
        try: # Check if setting exist
            user_profile_groups = settings.AUTH_LDAP_USER_PROFILE['GA']
        except Exception as ex:
            self.logger.warn('Could not get ldap group(s) of user profile GA in setting AUTH_LDAP_USER_PROFILE.')

        if user_profile_groups is not None:
            if not isinstance(user_profile_groups, (list, tuple)):  # Check if it is a list, otherwise convert to list
                self.logger.debug('Given setting for user profile "GA" is not a list (%s), convert it to a list.' % type(user_profile_groups))
                user_profile_groups = (user_profile_groups,)  # trailing comma: https://wiki.python.org/moin/TupleSyntax

            for group in user_profile_groups:
                if self.__is_user_member_of_ldap_group(ldap_connection=ldap_connection, username=ldap_username, group_dn=group):
                    self.logger.debug('User %s is member of GA group %s' % (ldap_username, group))
                    self.__set_userprofile(username_django, 'GA')
                    user_profile = 'GA'
                    self.logger.debug('Set django user %s field "is_staff" to True.')
                    django_user.is_staff = True
                    django_user.save()
                    self.logger.debug('User profile to "GA" = Global Admin set. Do not check for other profiles anymore.')
                    break
            if user_profile is None:
                self.logger.debug('User %s is not part of a GA group.' % ldap_username)
        else:
            self.logger.debug('No ldap group for user profile "GA" defined in settings.')


        # RW = Read & Write
        #------------------
        user_profile_groups = None # temporary variable with ldap groups
        try: # Check if setting exist
            user_profile_groups = settings.AUTH_LDAP_USER_PROFILE['RW']
        except Exception as ex:
            self.logger.warn('Could not get ldap group(s) of user profile RW in setting AUTH_LDAP_USER_PROFILE.')

        if user_profile_groups is not None and user_profile is None:
            if not isinstance(user_profile_groups, (list, tuple)):  # Check if it is a list, otherwise convert to list
                self.logger.debug('Given setting for user profile "RW" is not a list (%s), convert it to a list.' % type(user_profile_groups))
                user_profile_groups = (user_profile_groups,)  # trailing comma: https://wiki.python.org/moin/TupleSyntax

            for group in user_profile_groups:
                if self.__is_user_member_of_ldap_group(ldap_connection=ldap_connection, username=ldap_username, group_dn=group):
                    self.logger.debug('User %s is member of RW group %s' % (ldap_username, group))
                    self.__set_userprofile(username_django, 'RW')
                    user_profile = 'RW'
                    self.logger.debug('User profile to "RW" = "Read Write" set. Do not check for other profiles anymore.')
                    break
            if user_profile is None:
                self.logger.debug('User %s is not part of a RW group.' % ldap_username)
        else:
            self.logger.debug('No ldap group for user profile "RW" defined in settings OR user profile already set to GA.')

        # RO = Read Only
        #---------------
        user_profile_groups = None  # temporary variable with ldap groups
        try: # Check if setting exist
            user_profile_groups = settings.AUTH_LDAP_USER_PROFILE['RO']
        except Exception as ex:
            self.logger.warn('Could not get ldap group(s) of user profile RO in setting AUTH_LDAP_USER_PROFILE.')

        if user_profile_groups is not None and user_profile is None:
            if not isinstance(user_profile_groups, (list, tuple)):  # Check if it is a list, otherwise convert to list
                self.logger.debug('Given setting for user profile "RO" is not a list (%s), convert it to a list.' % type(user_profile_groups))
                user_profile_groups = (user_profile_groups,)  # trailing comma: https://wiki.python.org/moin/TupleSyntax

            for group in user_profile_groups:
                if self.__is_user_member_of_ldap_group(ldap_connection=ldap_connection, username=ldap_username, group_dn=group):
                    self.logger.debug('User %s is member of RO group %s' % (ldap_username, group))
                    self.__set_userprofile(username_django, 'RO')
                    user_profile = 'RO'
                    self.logger.debug('User profile to "RO" = "Read Only" set. Do not check for other profiles anymore.')
                    break
            if user_profile is None:
                self.logger.debug('User %s is not part of a RO group.' % ldap_username)
        else:
            self.logger.debug('No ldap group for user profile "RO" defined in settings OR user profile already set to GA or RW.')

        # SO = Stats Only (not implemented (yet?) in SAL)
        #------------------------------------------------
        user_profile_groups = None # temporary variable with ldap groups
        try: # Check if setting exist
            user_profile_groups = settings.AUTH_LDAP_USER_PROFILE['SO']
        except Exception as ex:
            self.logger.warn('Could not get ldap group(s) of user profile SO in setting AUTH_LDAP_USER_PROFILE.')

        if user_profile_groups is not None and user_profile is None:
            if not isinstance(user_profile_groups, (list, tuple)):  # Check if it is a list, otherwise convert to list
                self.logger.debug('Given setting for user profile "SO" is not a list (%s), convert it to a list.' % type(user_profile_groups))
                user_profile_groups = (user_profile_groups,)  # trailing comma: https://wiki.python.org/moin/TupleSyntax

            for group in user_profile_groups:
                if self.__is_user_member_of_ldap_group(ldap_connection=ldap_connection, username=ldap_username, group_dn=group):
                    self.logger.debug('User %s is member of SO group %s' % (ldap_username, group))
                    self.__set_userprofile(username_django, 'SO')
                    user_profile = 'SO'
                    self.logger.debug('User profile to "SO" = "Stats Only" set. Do not check for other profiles anymore.')
                    break
            if user_profile is None:
                self.logger.debug('User %s is not part of a SO group.')
        else:
            self.logger.debug('No ldap group for user profile "SO" defined in settings OR user profile already set to GA, RW or RO.')

        # If the user does not exist in any of the given AUTH_LDAP_USER_PROFILE groups, set to default UserProfile level
        if user_profile is None:
            self.logger.warn('User %s authenticated in AD/LDAP, but not part of any configured GA/RW/RO/SO group. Set to %s.' %
                             (django_user, UserProfile._meta.get_field('level').get_default()))
            self.__set_userprofile(username_django, '%s' % UserProfile._meta.get_field('level').get_default())
            user_profile = UserProfile._meta.get_field('level').get_default()


        # Business Units
        ################
        # remove from all existing Business units, before assigne to new business units.
        self.logger.debug('Remove all business units of %s, assign the configured ones afterwards.' % username_django)
        for business_unit in self.__get_business_units(username=username_django):
            self.logger.debug('Remove business unit "%s" from user %s.' % (business_unit, username_django))
            self.__remove_user_from_business_unit(username_django, business_unit)

        # assign Business units
        self.logger.debug('Get all existing business units.')
        all_business_units = self.__get_business_units()
        user_business_units = [] # business units of user.
        business_units_settings = None # Configured Business units in the settings
        try:
            business_units_settings = settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT.keys()
        except Exception as ex:
            self.logger.debug('AUTH_LDAP_USER_TO_BUSINESS_UNIT not configured in settings as dictionary.')

        if business_units_settings is not None and user_profile != 'GA': # GA (Global Admin does not need assigned business units)
            for business_unit in business_units_settings:
                # Handle all business units for key #ALL_BU
                if business_unit == '#ALL_BU': # Special case: users in the group #ALL_BU get access to all Business units.
                    self.logger.debug('Check if user %s has access to all business units ("%s").' % (ldap_username, business_unit))
                    if not isinstance(settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT[business_unit], (list, tuple)):  # Check if it is a list, otherwise convert to list
                        self.logger.debug('Given setting for business unit "%s" is not a list, convert it to a list.' % business_unit)
                        # trailing comma: https://wiki.python.org/moin/TupleSyntax
                        settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT[business_unit] = (settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT[business_unit],)
                    for group in settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT[business_unit]: # Loop over groups
                        self.logger.debug('Check if user %s is in ldap group %s.' % (ldap_username, group))
                        if self.__is_user_member_of_ldap_group(ldap_connection=ldap_connection, username=ldap_username, group_dn=group):
                            self.logger.debug('User %s is member of group %s, assign user to all existing business units!' % (ldap_username, group))
                            for one_of_all_business_units in all_business_units:
                                self.logger.debug('Assign business unit %s to user %s with access to all existing business units.' % (one_of_all_business_units, username_django))
                                self.__add_user_to_business_unit(username_django, one_of_all_business_units) # Assign user to business unit
                                user_business_units.append(one_of_all_business_units)
                            break
                        else:
                            self.logger.debug('User %s is NOT member of group %s.' % (ldap_username, group))
                # Check if business unit is an existing one
                elif business_unit in all_business_units:
                    if not isinstance(settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT[business_unit], (list, tuple)):  # Check if it is a list, otherwise convert to list
                        self.logger.debug('Given setting for business unit "%s" is not a list, convert it to a list.' % business_unit)
                        # trailing comma: https://wiki.python.org/moin/TupleSyntax
                        settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT[business_unit] = (settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT[business_unit],)
                    for group in settings.AUTH_LDAP_USER_TO_BUSINESS_UNIT[business_unit]: # Loop over groups
                        self.logger.debug('Check if user %s is in ldap group %s.' % (ldap_username, group))
                        if self.__is_user_member_of_ldap_group(ldap_connection=ldap_connection, username=ldap_username, group_dn=group):
                            self.logger.debug('User %s is member of group %s, assign user to business unit %s' % (ldap_username, group, business_unit))
                            self.__add_user_to_business_unit(username_django, business_unit) # Assign user to business unit
                            user_business_units.append(business_unit)
                            break
                        else:
                            self.logger.debug('User %s is NOT member of group %s.' % (ldap_username, group))
                else:
                    self.logger.warn('Business unit in settings (AUTH_LDAP_USER_TO_BUSINESS_UNIT) %s does not exist in existing SAL business units (%s)' %
                                     (business_unit, ''.join(all_business_units)))
        elif user_profile == 'GA':
            self.logger.debug('User %s has user profile GA (Global Admin), therefore not necessary to assign business units to the user.' % username_django)
        elif business_units_settings is None:
            self.logger.debug('AUTH_LDAP_USER_TO_BUSINESS_UNIT not correct configured in settings, therefore not possible to assign business units to user %s.' % username_django)

        self.logger.info('Everything fine! Found user with username "%s" in ldap. User has user profile "%s" and access to following business units: %s' %
                         (username, user_profile, ', '.join(user_business_units)))
        django_user.save()
        return django_user

    # LDAP Stuff
    ############

    def __ldap_bind(self, ldap_connection, username, password):
        """
        Bind to ldap (Version 3) with given username and password.
        Returns the binded ldap connection. If the bind fails, the function raises an exception.
        """
        try:
            self.logger.debug('Set ldap to VERSION3.')
            ldap_connection.protocol_version = ldap.VERSION3
            self.logger.debug('Bind (simple_bind_s) with user %s.' % username)
            bind_result = ldap_connection.simple_bind_s(username, password)
            self.logger.info('User %s authenticated in ldap (%s, %s).' % (username, bind_result, ldap_connection.whoami_s()))
            return ldap_connection
        except Exception as ex:
            self.logger.error('Could not bind to ldap (%s) as user %s.' % (ldap_connection, username))
            self.logger.debug(ex.message)
            raise ex


    def __get_user_from_ldap(self, ldap_connection, username, ldap_base = settings.AUTH_LDAP_USER_SEARCH):
        """
        Returns a dictionary with all fields stored in ldap.
        Username can be uid (neffba00) or email (basil.neff@unibas.ch)
        If no user is found, the function returns None.

        Args:
            ldap_connection:
            username:
            ldap_base: base dn where the user can be found, with subtree scope.

        Returns: A dictionary with all fields stored in ldap, None if no user is found.
        """

        assert ldap_connection is not None
        assert username is not None
        assert username != ''
        assert username != 'root' # root should not be in ldap
        assert ldap_base is not None

        # Check Base DN
        if ldap_base is None or len(ldap_base) == 0:
            self.logger.error('Base DN (ldap_base) for user search in ldap is not defined (AUTH_LDAP_USER_SEARCH in settings). '
                              'Therefore it is not possible to get the user object from ldap. Authentication does not work')
            return None

        # Get fields from AUTH_LDAP_USER_ATTR_MAP, if possible
        try:
            searchFilter = "(|(%s=%s)(%s=%s) )" % \
                           (settings.AUTH_LDAP_USER_ATTR_MAP['username'] , username, settings.AUTH_LDAP_USER_ATTR_MAP['email'], username)
        except NameError as ne:
            self.logger.warn('Could not get user attributes username or email from AUTH_LDAP_USER_ATTR_MAP in settings. Use default ones: sAMAccountName and mail')
            searchFilter = "(|(sAMAccountName=%s)(mail=%s) )" % (username, username)

        searchScope = ldap.SCOPE_SUBTREE

        user_fields = None
        try:
            self.logger.debug('Get user object of user %s from ldap. BaseDN: %s; Filter: %s; scope: %s' %
                              (username, ldap_base, searchFilter, searchScope))
            ldap_result = ldap_connection.search_s(ldap_base, searchScope, searchFilter)
            self.logger.debug('LDAP search result: %s' % ldap_result)
            if ldap_result is None:
                self.logger.warn('Could not find user %s in ldap.' % username)
                return None

            for entry in ldap_result:
                if entry[0] is not None:
                    self.logger.debug('User LDAP Path (DN): %s' % entry[0])
                    self.logger.debug('User fields: %s' % entry[1])
                    user_fields = entry[1]
                    user_fields['dn'] = entry[0] # Add dn as field
        except Exception as ex:
            self.logger.warn('Could not get user %s in ldap: %s' % (username, ex.message))
            self.logger.debug(ex)
            return None

        if user_fields is None:
            self.logger.warn['Could not get fields from ldap for user %s.' % username]
            return None

        self.logger.debug('User %s has following ldap fields: %s' % (username, user_fields))
        return user_fields

    def __is_user_member_of_ldap_group(self, ldap_connection, username, group_dn, ldap_base = settings.AUTH_LDAP_USER_SEARCH):
        """
        Checks if the given user is member of the given ldap group dn.
        Search is done recursive.

        Args:
            ldap_base: base dn where the user can be found, with subtree scope.

        Returns: True if the user is member of given group, False if not.
        """

        assert username is not None
        assert username != ''
        assert group_dn is not None
        assert group_dn != ''

        # Check Base DN
        if ldap_base is None or len(ldap_base) == 0:
            self.logger.error('Base DN (ldap_base) for user search in ldap is not defined (AUTH_LDAP_USER_SEARCH in settings). '
                              'Therefore it is not possible to get the user object from ldap. Authentication does not work')
            return None

        # Get fields from AUTH_LDAP_USER_ATTR_MAP, if possible
        try:
            # Recursive Lookup, with input from here: https://stackoverflow.com/questions/6195812/ldap-nested-group-membership
            filter = '(&(memberOf:1.2.840.113556.1.4.1941:=%s)(objectCategory=person)(objectClass=user)(%s=%s))' % \
                     (group_dn, settings.AUTH_LDAP_USER_ATTR_MAP['username'], username)
        except NameError as ne:
            self.logger.warn('Could not get user attributes username from AUTH_LDAP_USER_ATTR_MAP in settings. Use default one: sAMAccountName')
            filter = '(&(memberOf:1.2.840.113556.1.4.1941:=%s)(objectCategory=person)(objectClass=user)(sAMAccountName=%s))' % (group_dn, username)


        try:
            self.logger.debug('Check if user %s is member of group %s, filter: %s' % (username, group_dn, filter))
            # search_s: http://python-ldap.readthedocs.io/en/python-ldap-3.0.0b1/reference/ldap.html#ldap.LDAPObject.search_s
            ldap_result = ldap_connection.search_s(ldap_base, ldap.SCOPE_SUBTREE, filter)
        except Exception as ex:
            self.logger.warn('Could not get group %s in ldap: %s' % (group_dn, ex.message))
            self.logger.debug(ex)
            return False

        self.logger.debug('LDAP search result: %s' % ldap_result)
        if ldap_result is None:
            self.logger.warn('Could not find group %s in ldap.' % group_dn)
            return False

        try:
            if ldap_result[0][0] is None:
                self.logger.debug('Could not find user %s in group %s: %s' % (username, group_dn, ldap_result))
                return False
            else:
                self.logger.debug('User %s in group %s found: %s' % (username, group_dn, ldap_result[0][0]))
                return True

        except Exception as ex:
            self.logger.warn('Could not get user entry for %s in group %s from ldap search: %s' % (username, group_dn, ex.message))
            return False


    # SAL Stuff - profile and business unit permissions
    ###################################################

    def __set_userprofile(self, username, level):
        """
        Sets the given level (GA, RW, RO, SO) to the user with the given usernam.
        If the user does not exist, raise an exception.
        If the userprofile does not yet exist in the database, create it.

        Args:
            username: django username
            level: GA, RW, RO, SO; has to be in the list of UserProfile.LEVEL_CHOICES

        Returns: Nothing

        """
        assert str(level).upper() in dict(UserProfile.LEVEL_CHOICES).keys()
        assert username is not None

        # Get django user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as udne:
            self.logger.error('Django user %s does not exist!' % username)
            raise udne
        self.logger.debug('Set level "%s" in userprofile for user %s' % (level.upper(), username))

        userprofile, created = UserProfile.objects.get_or_create(user = user)
        if created:
            self.logger.debug('UserProfile for user %s created.' % username)
        userprofile.level = level.upper()
        userprofile.save()


    def __get_business_units(self, username = None):
        """
        Returns a list with all business unit names as string.
        If a username is given, only business units of the given user is returned. Otherwise all business units are returned.
        If the user does not exist, raise an exception.
        Returns: a list with all business unit names as string.
        """

        if username is None:
            self.logger.debug('No username given, return all existing business units.')
            business_units = BusinessUnit.objects.all()
            business_units_names = [str(unit.name) for unit in business_units]
            self.logger.debug('All Business units: %s' % ', '.join(business_units_names))
        else:
            # Get django user
            try:
                self.logger.debug('Get all business units of user %s.' % username)
                user = User.objects.get(username=username)
            except User.DoesNotExist as udne:
                self.logger.error('Django user %s does not exist!' % username)
                raise udne

            business_units = BusinessUnit.objects.filter(users=user)
            business_units_names = [str(unit.name) for unit in business_units]
            self.logger.debug('Business units of user %s: %s' % (user, ', '.join(business_units_names)))
        return business_units_names


    def __add_user_to_business_unit(self, username, business_unit_name):
        """
        Assign business unit to user.
        If the user does not exist, raise an exception.
        Args:
            username: django username (NOT a django user object!)
            business_unit_name: Name of the business unit (Not a django BusinessUnit object)

        Returns: Nothing

        """

        assert username is not None
        assert business_unit_name is not None

        # Get django user
        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as udne:
            self.logger.error('Django user %s does not exist!' % username)
            raise udne

        business_unit = BusinessUnit.objects.get(name=business_unit_name)
        self.logger.debug('Add user %s to business unit %s' % (user, business_unit))
        business_unit.users.add(user)

    def __remove_user_from_business_unit(self, username, business_unit_name):
        """
        Remove business unit of user. If the business unit is not assigned to the user, the assignment can't get removed.
        If the user does not exist, raise an exception.
        Args:
            username: django username (NOT a django user object!)
            business_unit_name: Name of the business unit (Not a django BusinessUnit object)

        Returns: Nothing

        """

        assert username is not None
        assert business_unit_name is not None

        try:
            user = User.objects.get(username=username)
        except User.DoesNotExist as udne:
            self.logger.error('Django user %s does not exist!' % username)
            raise udne

        business_unit = BusinessUnit.objects.get(name=business_unit_name)
        self.logger.debug('Remove user %s from business unit %s' % (user, business_unit))
        business_unit.users.remove(user)

    # DJANGO Stuff
    ##############

    def __get_or_create_django_user(self, username, first_name = None, last_name = None, email = None):
        """
        Get or create a django user. If a dango user with the given username does already exist,
        update the given fields and return the django user object. If a user with the given username does not yet exist,
        create a user with all given fields.

        Args:
            username:
            first_name:
            last_name:
            email:

        Returns: A django user object.

        """

        assert username is not None

        self.logger.debug('Get or create django user %s (fist_name: %s, last_name: %s, email: %s)' %
                          (username, first_name, last_name, email))

        try:
            # Check if the user exists in Django's local database
            self.logger.debug('Check if local user with username %s does exist.' % username)
            user = User.objects.get(username=username)
            self.logger.debug('User %s did already exist in internal database, update given fields.' % username)
            # Update fields if given
            if first_name is not None:
                user.first_name = first_name
            if last_name is not None:
                user.last_name = last_name
            if email is not None:
                user.email = email
        except User.DoesNotExist:
            # Create a user in Django's local database
            self.logger.debug('User %s does not yet exist in internal database, create internal user.' % username)
            user = User.objects.create_user(username, email=email, last_name=last_name, first_name=first_name)
        return user


    # Required for your backend to work properly - unchanged in most scenarios
    def get_user(self, user_id):
        self.logger.debug('Get django user %s' % user_id)
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
