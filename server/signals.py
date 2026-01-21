from django.dispatch import receiver

from djangosaml2.signals import pre_user_save

from server.models import UserProfile, ProfileLevel
from server.utils import get_django_setting


READ_ONLY_GROUPS = set(get_django_setting('SAML_READ_ONLY_GROUPS', []))
READ_WRITE_GROUPS = set(get_django_setting('SAML_READ_WRITE_GROUPS', []))
GLOBAL_ADMIN_GROUPS = set(get_django_setting('SAML_GLOBAL_ADMIN_GROUPS', []))
GROUPS_ATTRIBUTE = get_django_setting('SAML_GROUPS_ATTRIBUTE', 'memberOf')


@receiver(pre_user_save)
def update_group_membership(
        sender, instance, attributes: dict, user_modified: bool, **kwargs) -> bool:
    """Update user's group membership based on passed SAML groups

    Sal access level is based on the highest access level granted across
    all groups a user is a member of. For example, if you are in a group
    with RO access and a group with GA access, the GA level "wins".

    Users who have no group membership in any of the configured
    SAML_X_GROUPS settings will be unchanged, allowing changes to these
    users via the admin panel to persist.

    Args:
        sender: The class of the user that just logged in.
        instance: User instance
        attributes: SAML attributes dict.
        user_modified: Bool whether the user has been modified
        kwargs:
            signal: The signal instance

    Returns:
        Whether or not the user has been modified. This allows the user
        instance to be saved once at the conclusion of the auth process
        to keep the writes to a minimum.
    """
    assertion_groups = set(attributes.get(GROUPS_ATTRIBUTE, []))
    if GLOBAL_ADMIN_GROUPS.intersection(assertion_groups):
        instance.userprofile.delete()
        user_profile = UserProfile(user=instance, level=ProfileLevel.global_admin)
        user_profile.save()
        instance.is_superuser = True
        instance.is_staff = True
        instance.is_active = True
        user_modified = True
    elif READ_WRITE_GROUPS.intersection(assertion_groups):
        instance.userprofile.delete()
        user_profile = UserProfile(user=instance, level=ProfileLevel.read_write)
        user_profile.save()
        instance.is_superuser = False
        instance.is_staff = False
        instance.is_active = True
        user_modified = True
    elif READ_ONLY_GROUPS.intersection(assertion_groups):
        instance.userprofile.delete()
        user_profile = UserProfile(user=instance, level=ProfileLevel.read_only)
        user_profile.save()
        instance.is_superuser = False
        instance.is_staff = False
        instance.is_active = True
        user_modified = True
    return user_modified
