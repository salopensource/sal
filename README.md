# Sal

[![CircleCI](https://circleci.com/gh/salopensource/sal.svg?style=svg)](https://circleci.com/gh/salopensource/sal)

Sal is a multi-tenanted reporting dashboard for [Munki](https://github.com/munki/munki/) with the ability to display information from [Facter](https://puppet.com/docs/puppet/latest/facter.html). It has a plugin system allowing you to easily build widgets to display your custom information from Facter, Grains, Munki's [conditional items](https://github.com/munki/munki/wiki/Conditional-Items) etc.

With Sal, you are able to allow access to reports on certain sets of machines to certain people - for example, giving a manager access to the reports on the machines in their department.

Sal also features powerful search capabilities and application inventory and support for Munki's license tracking.

![Sal](https://github.com/salopensource/sal/raw/main/assets/Sal.png)

## Getting Started

First off, you're going to need to get the Server and then the Client component of Sal installed. [Instructions can be found here](https://github.com/salopensource/sal/wiki/Getting-Started).

Once you've got clients reporting in, you're probably going to want to customise what you see on the various screens. [Here is a full list](https://github.com/salopensource/sal/wiki/Settings) of the various options that can be set in `sal/settings.py`.

If you would like a demo of setting up Sal along with some of the features please watch the following presentation Graham made at the 2014 [Penn State MacAdmins Conference](http://youtu.be/BPTJnz27T44?t=21m28s). Slides available from [here](http://grahamgilbert.com/images/posts/2014-07-09/Multi_site_Munki.pdf).

## Search

Sal has full search across machines, Facts and Munki conditions. For more information, see [it's documentation](https://github.com/salopensource/sal/wiki/Search).

![Search](https://github.com/salopensource/sal/raw/main/assets/Built%20search.png)

## Plugins

You can enable, disable and re-order your plugins from the Settings page, under the 'person' menu in the main menu bar. For more information on using and installing your own plugins, visit the [Using Plugins](https://github.com/salopensource/sal/wiki/Installing-and-using-plugins) page.

After re-ordering and hiding plugins from some screens, you might even want to make your own plugins. You can base your plugin off of one of the included ones, or one of mine in the [repository of optional plugins](https://github.com/salopensource/grahamgilbert-plugins). For more information on writing plugins, check out the [wiki](https://github.com/salopensource/sal/wiki).

## External Authentication

# sal-saml

A Docker container for Sal that uses SAML

You will almost certainly need to edit `settings.py` and provide your own metadata.xml file from your SAML provider.

_The following instructions are provided as a best effort to help get started. They might require modifications to meet specific environments._

## settings.py changes you will certainly need to make

- `USE_SAML` - Set this to `True` to enable SAML
- `SAML_ATTRIBUTE_MAPPING` (These values come from OpenLDAP, Active Directory, etc)
- `SAML_CONFIG`
  - `entityid` Ex: <https://sal.example.com/saml2/metadata/>
  - `assertion_consumer_service` Ex: <https://sal.example.com/saml2/acs/>
  - `single_logout_service` Ex: <https://sal.example.com/saml2/ls/> and <https://sal.example.com/saml2/post>
  - `required_attributes` - These should match the values from SAML_ATTRIBUTE_MAPPING
  - `idp`
    - `root url` Ex: <https://app.onelogin.com/saml/metadata/1234567890>
    - `single_sign_on_service` Ex: <https://apps.onelogin.com/trust/saml2/http-post/sso/1234567890>
    - `single_logout_service` Ex: <https://apps.onelogin.com/trust/saml2/http-redirect/slo/1234567890>

## An example Docker run

Please note that this Docker run is **incomplete**, but shows where to pass the `metadata.xml` and `settings.py`. Also note, `latest` in the below run should not be used unless you have a real reason (needing a development version). When performing `docker run`, you should substitute `latest` for the latest tagged release.

```bash
docker run -d --name="sal" \
-p 80:8000 \
-v /yourpath/metadata.xml:/home/docker/sal/sal/metadata.xml \
-v /yourpath/settings.py:/home/docker/sal/sal/settings.py \
--restart="always" \
ghcr.io/salopensource/sal:latest
```

### Notes on OneLogin

1. In the OneLogin admin portal click on Apps > Add Apps.
1. Search for `SAML Test Connector (IdP)`. Click on this option.
1. Give the application a display name, upload a icon if you wish, and then click save.
1. Under "Configuration" tab, you will need at least the minimum settings shown below:
    - `Recipient`: <https://sal.example.com/saml2/acs/>
    - `ACS (Consumer) URL Validator`: .*  (Note this is a period followed by an asterisk)
    - `ACS (Consumer) URL`: <https://sal.example.com/saml2/acs/>
1. Under the "Parameters" tab, you will need to add the custom iDP Fields/Values. The process looks like:
    - Click "Add parameter"
      - `Field name`: FIELD_NAME
      - `Flags`: Check the Include in SAML assertion
    - Now click on the created field and set the appropriate FIELD_VALUE based on the table below.

    Repeat the above steps for all required fields:

    | **FIELD_NAME** | **FIELD_VALUE**   |
    |-----------|--------------|
    | urn:mace:dir:attribute-def:cn   | First Name      |
    | urn:mace:dir:attribute-def:sn   | Last Name       |
    | urn:mace:dir:attribute-def:mail | Email           |
    | urn:mace:dir:attribute-def:uid  | Email name part |

1. Under the "SSO" tab, download the "Issuer URL" metadata file. This will be mounted in your Docker container [(see above)](#an-example-docker-run).
1. Under the "SSO" tab, you will find the "SAML 2.0 Endpoint" and "SLO Endpoint" which will go into the `settings.py` > `idp` section.
1. Lastly, "Save" the SAML Test Connector (IdP).

### Notes on Okta

Okta has a slightly different implementation and a few of the tools that this container uses, specifically [`pysaml2`](https://github.com/rohe/pysaml2) and [`djangosaml2`](https://github.com/knaperek/djangosaml2), do not like this implementation by default. Please follow the setup instructions, make sure to replace the example URL:

1. Create a new app from the admin portal
    - Platform: Web
    - Sign on method: SAML 2.0
1. Under "General Settings", give the app a name, add a logo and modify app visibility as desired.
1. Under "Configure SAML" enter the following (if no value is given after the colon leave it blank):

   ##### General

    Single sign on URL: **<https://sal.example.com/saml2/acs/>**

    Use this for Recipient URL and Destination URL: **Checked**

    Allow this app to request other SSO URLs: **Unchecked** (If this option is available)

    Audience URI (SP Entity ID): **<https://sal.example.com/saml2/metadata/>**

    Default RelayState: **Unspecified**

    Application username: **Okta username**

   ##### Attribute Statements

    | **Name** | **Format** | **Value** |
    |-----------|-----------|-----------|
    | urn:mace:dir:attribute-def:cn   | Basic | ${user.firstName} |
    | urn:mace:dir:attribute-def:sn   | Basic | ${user.lastName}  |
    | urn:mace:dir:attribute-def:mail | Basic | ${user.email}     |
    | urn:mace:dir:attribute-def:uid  | Basic | ${user.login}     |

   ##### Group Attribute Statements

    Sal does not support these at this time.
1. Under "Feedback":
    - Are you a customer or partner? I'm an Okta customer adding an internal app
    - App type: This is an internal app that we have created

1. Download the metadata file from: "Sign On" tab > "Settings" > "SAML 2.0" > "Metadata details" > "Metadata URL" link
    - Rename the file to `metadata.xml` to match the Docker run example. Make sure to move this file to the correct location on your Docker host.

1. Under "Sign On" tab > "Settings > "SAML 2.0" > "Metadata details" > "More details", you will find the "Sign on URL" and "Issuer" which will go into the `settings.py` > `idp` section.

### Notes on Google

1. In the Google admin console click on Apps > SAML Apps.
1. Click the `+` (plus) button > Setup My Own Custon App.
1. Under the "Option 1" section, you will find the "SSO URL" which will go into the `settings.py` > `idp` section.
1. Under the "Option 2" section, download the "IDP metadata" metadata file. This will be mounted in your Docker container [(see above)](#an-example-docker-run).
1. Give the application a display name, upload a icon if you wish, and then click Next.
1. In the "Service Provider Details" pane, you will need at least the minimum settings shown below:
    - `ACS (Consumer) URL`: <https://sal.example.com/saml2/acs/>
    - `Entity ID`: <https://sal.example.com/saml2/metadata/>
    - Set the `Name ID Format` to `EMAIL`
1. In the "Attribute Mapping" pane, you will need to add the following mappings (NOTE: These match the default mappings in the `settings.py` file, if you changed the attribute mappings, you should use those keys here instead)
    - Click "Add New Mapping" and fill out the attributes as listed below:

##### Attribute Mappings

  | **Application Attribute** | **Category** | **User Field**   |
  |-----------|-----------|-----------|
  | mail  | Basic Information     | Primary Email  |
  | uid   | Basic Information     | Primary Email  |
  | cn    | Basic Information     | First Name     |
  | sn    | Basic Information     | Last Name      |

1. Click "Finish" to save the new SAML app in Google.
    - **NOTE**: You will likely need to enable the app for your OUs before you will be able to authenticate in using SAML auth

### Notes on Azure AD

1. Create a new Enterprise application. Choose "Non-gallery application"
1. Under "Single sign-on", choose SAML.
1. Set "Basic SAML Configuration" to:

    | **Name** | **Value** |
    |----------|-----------|
    | Identifier (Entity ID)                     | <https://sal.example.com/saml2/metadata/> |
    | Reply URL (Assertion Consumer Service URL) | <https://sal.example.com/saml2/acs/>      |
    | Sign on URL                                | <https://sal.example.com/saml2/login/>    |
    | Relay State                                | Optional                                |
    | Logout Url                                 | <https://sal.example.com/saml2/ls>        |

    Set the "Clain name" name identifier format to "Persistent".

1. Set "User Attributes & Claims" to:

    | **Claim name** | **Value** |
    |----------------|-----------|
    | urn:oid:2.5.4.42                  | user.givenname         |
    | urn:oid:0.9.2342.19200300.100.1.1 | user.userprincipalname |
    | urn:oid:2.5.4.4                   | user.surname           |
    | urn:oid:0.9.2342.19200300.100.1.3 | user.mail              |
    | Unique User Identifier            | user.userprincipalname |

1. Set the attribute mapping in settings.py to:

    ```
    SAML_ATTRIBUTE_MAPPING = {
        'uid': ('username', ),
        'mail': ('email', ),
        'givenName': ('first_name', ),
        'sn': ('last_name', ),
    }
    ```

1. Set the id section in settings.py to:

    ```
           'idp': {
              'https://sts.windows.net/[tenantId]': {
                  'single_sign_on_service': {
                      saml2.BINDING_HTTP_REDIRECT: 'https://login.microsoftonline.com/[tenantId]/saml2',
                      },
                  'single_logout_service': {
                      saml2.BINDING_HTTP_REDIRECT: 'https://login.microsoftonline.com/[tenantId]/saml2',
                      },
                  },
              },
    ```

### Help

For more information on what to put in your settings.py, look at <https://github.com/knaperek/djangosaml2>
Also, swing by the #sal channel on the MacAdmins slack team (<https://macadmins.org/>)

## Having problems?

You should check out the [troubleshooting](https://github.com/salopensource/sal/wiki/Troubleshooting) page, consider heading over the the #sal channel on the [macadmins.org Slack](http://macadmins.org).

## API

There is a simple API available for Sal. Documentation can be found at [docs/Api.md](https://github.com/salopensource/sal/wiki/API)

## Why Sal?

It's the Internet's fault! I asked on Twitter what I should call it, and Peter Bukowinski ([@pmbuko](https://twitter.com/pmbuko)) [suggested the name](https://twitter.com/pmbuko/status/377155523726290944), based on a Monkey puppet called [Sal Minella](http://muppet.wikia.com/wiki/Sal_Minella).
