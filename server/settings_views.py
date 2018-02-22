import os
import time

from yapsy.PluginManager import PluginManager

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf

import utils
from forms import *
from inventory.models import *
from models import *
from sal.decorators import *

if settings.DEBUG:
    import logging
    logging.basicConfig(level=logging.INFO)


# The database probably isn't going to change while this is loaded.
IS_POSTGRES = utils.is_postgres()


@login_required
def new_version_never(request):
    update_notify_date(request)
    return redirect(index)


@ga_required
def update_notify_date(request, length='never'):
    # Don't notify about a new version until there is a new one
    version_report = utils.check_version()
    if version_report['new_version_available']:
        next_notify_date = utils.get_setting('next_notify_date', time.time()) + length
        utils.set_setting('next_notify_date', next_notify_date)


@login_required
def new_version_week(request):
    update_notify_date(request, length=604800)
    return redirect(index)


@login_required
def new_version_day(request):
    update_notify_date(request, length=86400)
    return redirect(index)


@login_required
@ga_required
def manage_users(request):
    try:
        brute_protect = settings.BRUTE_PROTECT
    except Exception:
        brute_protect = False
    # We require you to be staff to manage users
    # TODO:
    user = request.user
    if not user.is_staff:
        return redirect(index)
    users = User.objects.all()
    c = {'user': request.user, 'users': users, 'request': request, 'brute_protect': brute_protect}
    return render(request, 'server/manage_users.html', c)


@login_required
@ga_required
def new_user(request):
    # We require you to be staff to manage users
    # TODO
    user = request.user
    if not user.is_staff:
        return redirect(index)
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile.objects.get(user=user)
            user_profile.level = request.POST['user_level']
            user_profile.save()
            return redirect('manage_users')
    else:
        form = NewUserForm()
    c = {'form': form}

    return render(request, 'forms/new_user.html', c)


@login_required
@ga_required
def edit_user(request, user_id):
    # TODO
    user = request.user
    # We require you to be staff to manage users
    if not user.is_staff:
        return redirect(index)
    the_user = get_object_or_404(User, pk=int(user_id))
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        if the_user.has_usable_password:
            form = EditUserForm(request.POST)
        else:
            form = EditLDAPUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile.objects.get(user=the_user)
            user_profile.level = request.POST['user_level']
            user_profile.save()
            if user_profile.level != 'GA':
                user.is_staff = False
                user.save()
            return redirect('manage_users')
    else:
        if the_user.has_usable_password:
            form = EditUserForm({'user_level': the_user.userprofile.level, 'user_id': the_user.id})
        else:
            form = EditLDAPUserForm(
                {'user_level': the_user.userprofile.level, 'user_id': the_user.id})

    c = {'form': form, 'the_user': the_user}

    return render(request, 'forms/edit_user.html', c)


@login_required
@ga_required
def user_add_staff(request, user_id):
    if request.user.id == int(user_id):
        # You shouldn't have been able to get here anyway
        return redirect('manage_users')
    user = get_object_or_404(User, pk=int(user_id))
    user.is_staff = True
    user.save()
    return redirect('manage_users')


@login_required
@ga_required
def user_remove_staff(request, user_id):
    if request.user.id == int(user_id):
        # You shouldn't have been able to get here anyway
        return redirect('manage_users')
    user = get_object_or_404(User, pk=int(user_id))
    user.is_staff = False
    user.save()
    return redirect('manage_users')


@ga_required
def delete_user(request, user_id):
    if request.user.id == int(user_id):
        # You shouldn't have been able to get here anyway
        return redirect('manage_users')
    user = get_object_or_404(User, pk=int(user_id))
    user.delete()
    return redirect('manage_users')


@login_required
@ga_required
def settings_page(request):
    historical_setting = utils.get_setting('historical_retention')
    historical_setting_form = SettingsHistoricalDataForm(initial={'days': historical_setting})

    senddata_setting = utils.get_setting('send_data')

    context = {
        'user': request.user,
        'request': request,
        'historical_setting_form': historical_setting_form,
        'senddata_setting': senddata_setting}
    return render(request, 'server/settings.html', context)


@login_required
@ga_required
def senddata_enable(request):
    utils.set_setting('send_data', True)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
@ga_required
def senddata_disable(request):
    utils.set_setting('send_data', False)
    return HttpResponseRedirect(request.META.get('HTTP_REFERER'))


@login_required
@ga_required
def settings_historical_data(request):
    if request.method == 'POST':
        form = SettingsHistoricalDataForm(request.POST)
        if form.is_valid():
            utils.set_setting('historical_retention', form.cleaned_data['days'])
            messages.success(request, 'Data retention settings saved.')

            return redirect('settings_page')

    else:
        return redirect('settings_page')


@login_required
@ga_required
def plugins_page(request):
    # Load the plugins
    utils.reload_plugins_model()
    enabled_plugins = Plugin.objects.all()
    disabled_plugins = utils.disabled_plugins(plugin_kind='main')
    c = {'user': request.user, 'request': request,
         'enabled_plugins': enabled_plugins, 'disabled_plugins': disabled_plugins}
    return render(request, 'server/plugins.html', c)


@login_required
@ga_required
def settings_reports(request):
    # Load the plugins
    utils.reload_plugins_model()
    enabled_plugins = Report.objects.all()
    disabled_plugins = utils.disabled_plugins(plugin_kind='report')
    c = {'user': request.user, 'request': request,
         'enabled_plugins': enabled_plugins, 'disabled_plugins': disabled_plugins}
    return render(request, 'server/reports.html', c)


@login_required
@ga_required
def settings_machine_detail_plugins(request):
    # Load the plugins
    utils.reload_plugins_model()
    enabled_plugins = MachineDetailPlugin.objects.all()
    disabled_plugins = utils.disabled_plugins(plugin_kind='machine_detail')
    c = {'user': request.user, 'request': request,
         'enabled_plugins': enabled_plugins, 'disabled_plugins': disabled_plugins}
    return render(request, 'server/machine_detail_plugins.html', c)


@login_required
def plugin_plus(request, plugin_id):
    _swap_plugin(request, plugin_id, 1)
    return redirect('plugins_page')


@login_required
def plugin_minus(request, plugin_id):
    _swap_plugin(request, plugin_id, -1)
    return redirect('plugins_page')


@login_required
@ga_required
def _swap_plugin(request, plugin_id, direction):
    # get current plugin order
    current_plugin = get_object_or_404(Plugin, pk=plugin_id)

    # Since it is sorted by order, we can swap the order attribute
    # of the selected plugin with the adjacent object in the queryset.

    # get all plugins (ordered by their order attribute).
    plugins = Plugin.objects.all()

    # Find the index in the query of the moving plugin.
    index = 0
    for plugin in plugins:
        if plugin.id == int(plugin_id):
            break
        index += 1

        # Perform the swap.
    temp_id = current_plugin.order
    current_plugin.order = plugins[index + direction].order
    current_plugin.save()
    plugins[index + direction].order = temp_id
    plugins[index + direction].save()


@login_required
@ga_required
def plugin_disable(request, plugin_id):
    plugin = get_object_or_404(Plugin, pk=plugin_id)
    plugin.delete()
    return redirect('plugins_page')


@login_required
def plugin_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        plugin = Plugin.objects.get(name=plugin_name)
    except Plugin.DoesNotExist:
        plugin = Plugin(name=plugin_name, order=utils.UniquePluginOrder())
        plugin.save()
    return redirect('plugins_page')


@login_required
@ga_required
def machine_detail_plugin_plus(request, plugin_id):
    # get current plugin order
    current_plugin = get_object_or_404(MachineDetailPlugin, pk=plugin_id)

    # get 'old' next one
    old_plugin = get_object_or_404(Plugin, order=(int(current_plugin.order) + 1))
    current_plugin.order = current_plugin.order + 1
    current_plugin.save()

    old_plugin.order = old_plugin.order - 1
    old_plugin.save()
    return redirect('settings_machine_detail_plugins')


@login_required
@ga_required
def machine_detail_plugin_minus(request, plugin_id):
    # get current plugin order
    current_plugin = get_object_or_404(MachineDetailPlugin, pk=plugin_id)
    # print current_plugin
    # get 'old' previous one

    old_plugin = get_object_or_404(MachineDetailPlugin, order=(int(current_plugin.order) - 1))
    current_plugin.order = current_plugin.order - 1
    current_plugin.save()

    old_plugin.order = old_plugin.order + 1
    old_plugin.save()
    return redirect('settings_machine_detail_plugins')


@login_required
@ga_required
def machine_detail_plugin_disable(request, plugin_id):
    plugin = get_object_or_404(MachineDetailPlugin, pk=plugin_id)
    plugin.delete()
    return redirect('settings_machine_detail_plugins')


@login_required
def machine_detail_plugin_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        plugin = MachineDetailPlugin.objects.get(name=plugin_name)
    except MachineDetailPlugin.DoesNotExist:
        enabled_plugins = MachineDetailPlugin.objects.all()  # noqa: F841
        # Build the manager
        manager = PluginManager()
        # Tell it the default place(s) where to find plugins
        manager.setPluginPlaces([settings.PLUGIN_DIR, os.path.join(
            settings.PROJECT_DIR, 'server/plugins')])
        # Load all plugins
        manager.collectPlugins()

        default_families = ['Darwin', 'Windows', 'Linux', 'ChromeOS']
        for plugin in manager.getAllPlugins():
            if plugin.name == plugin_name:

                try:
                    supported_os_families = plugin.plugin_object.supported_os_families()
                except Exception:
                    supported_os_families = default_families
        plugin = MachineDetailPlugin(name=plugin_name,
                                     order=utils.UniquePluginOrder(plugin_type='machine_detail'),
                                     os_families=utils.flatten_and_sort_list(supported_os_families))
        plugin.save()
    return redirect('settings_machine_detail_plugins')


@login_required
@ga_required
def settings_report_disable(request, plugin_id):
    plugin = get_object_or_404(Report, pk=plugin_id)
    plugin.delete()
    return redirect('settings_reports')


@login_required
def settings_report_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        plugin = Report.objects.get(name=plugin_name)
    except Report.DoesNotExist:
        plugin = Report(name=plugin_name)
        plugin.save()
    return redirect('settings_reports')


@login_required
@ga_required
def api_keys(request):
    api_keys = ApiKey.objects.all()
    c = {'user': request.user, 'api_keys': api_keys, 'request': request}
    return render(request, 'server/api_keys.html', c)


@login_required
@ga_required
def new_api_key(request):
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = ApiKeyForm(request.POST)
        if form.is_valid():
            new_api_key = form.save()
            return redirect('display_api_key', key_id=new_api_key.id)
    else:
        form = ApiKeyForm()
    c = {'form': form}
    return render(request, 'forms/new_api_key.html', c)


@login_required
@ga_required
def display_api_key(request, key_id):
    api_key = get_object_or_404(ApiKey, pk=int(key_id))
    if api_key.has_been_seen:
        return redirect(index)
    else:
        api_key.has_been_seen = True
        api_key.save()
        c = {'user': request.user, 'api_key': api_key, 'request': request}
        return render(request, 'server/api_key_display.html', c)


@login_required
@ga_required
def edit_api_key(request, key_id):
    api_key = get_object_or_404(ApiKey, pk=int(key_id))
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':

        form = ApiKeyForm(request.POST, instance=api_key)
        if form.is_valid():
            api_key = form.save()
            return redirect(api_keys)
    else:
        form = ApiKeyForm(instance=api_key)
    c = {'form': form, 'api_key': api_key}
    return render(request, 'forms/edit_api_key.html', c)


@login_required
@ga_required
def delete_api_key(request, key_id):
    api_key = get_object_or_404(ApiKey, pk=int(key_id))
    api_key.delete()
    return redirect(api_keys)

