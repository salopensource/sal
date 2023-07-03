import time

from django.conf import settings
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.models import User
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.template.context_processors import csrf
from django.urls import reverse

import sal.plugin
from sal.decorators import ga_required, staff_required
from server import utils
from server import forms
from server.models import ProfileLevel, Plugin, ApiKey, Report, MachineDetailPlugin, UserProfile
from server.views import index as index_view


# The database probably isn't going to change while this is loaded.
IS_POSTGRES = utils.is_postgres()


@login_required
@ga_required
def new_version_never(request):
    update_notify_date()
    return redirect(reverse('home'))


def update_notify_date(length='never'):
    # Don't notify about a new version until there is a new one
    version_report = utils.check_version()
    if version_report['new_version_available']:
        if isinstance(length, int):
            next_notify_date = utils.get_setting('next_notify_date', time.time()) + length
        else:
            next_notify_date = length
        utils.set_setting('next_notify_date', next_notify_date)


@login_required
@ga_required
def new_version_week(request):
    update_notify_date(length=604800)
    return redirect(index_view)


@login_required
@ga_required
def new_version_day(request):
    update_notify_date(length=86400)
    return redirect(index_view)


@login_required
@ga_required
@staff_required
def manage_users(request):
    try:
        brute_protect = settings.BRUTE_PROTECT
    except Exception:
        brute_protect = False
    users = User.objects.order_by('username')
    c = {'user': request.user, 'users': users, 'request': request, 'brute_protect': brute_protect}
    return render(request, 'server/manage_users.html', c)


@login_required
@ga_required
@staff_required
def new_user(request):
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        form = forms.NewUserForm(request.POST)
        if form.is_valid():
            user = form.save()
            user_profile = UserProfile.objects.get(user=user)
            user_profile.level = request.POST['user_level']
            user_profile.save()
            return redirect('manage_users')
    else:
        form = forms.NewUserForm()
    c = {'form': form}

    return render(request, 'forms/new_user.html', c)


@login_required
@ga_required
@staff_required
def edit_user(request, user_id):
    the_user = get_object_or_404(User, pk=int(user_id))
    c = {}
    c.update(csrf(request))
    if request.method == 'POST':
        if the_user.has_usable_password:
            form = forms.EditUserForm(request.POST)
        else:
            form = forms.EditLDAPUserForm(request.POST)
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
            form = forms.EditUserForm(
                {'user_level': the_user.userprofile.level, 'user_id': the_user.id})
        else:
            form = forms.EditLDAPUserForm(
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


@login_required
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
    historical_setting_form = forms.SettingsHistoricalDataForm(initial={'days': historical_setting})

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
        form = forms.SettingsHistoricalDataForm(request.POST)
        if form.is_valid():
            utils.set_setting('historical_retention', form.cleaned_data['days'])
            messages.success(request, 'Data retention settings saved.')

            return redirect('settings_page')

    else:
        return redirect('settings_page')


@login_required
@ga_required
def plugins_page(request):
    utils.reload_plugins_model()
    context = {'plugins': utils.get_active_and_inactive_plugins('machines')}
    return render(request, 'server/plugins.html', context)


@login_required
@ga_required
def settings_reports(request):
    utils.reload_plugins_model()
    context = {'plugins': utils.get_active_and_inactive_plugins('report')}
    return render(request, 'server/reports.html', context)


@login_required
@ga_required
def settings_machine_detail_plugins(request):
    utils.reload_plugins_model()
    plugins = utils.get_active_and_inactive_plugins('machine_detail')
    context = {'user': request.user, 'plugins': plugins}
    return render(request, 'server/machine_detail_plugins.html', context)


@login_required
@ga_required
def plugin_plus(request, plugin_id):
    _swap_plugin(plugin_id, 1)
    return redirect('plugins_page')


@login_required
@ga_required
def plugin_minus(request, plugin_id):
    _swap_plugin(plugin_id, -1)
    return redirect('plugins_page')


def _swap_plugin(plugin_id, direction, plugin_model=Plugin):
    # get current plugin order
    current_plugin = get_object_or_404(plugin_model, pk=plugin_id)

    # Since it is sorted by order, we can swap the order attribute
    # of the selected plugin with the adjacent object in the queryset.

    # get all plugins (ordered by their order attribute).
    plugins = plugin_model.objects.all()

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
@ga_required
def plugin_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        _ = Plugin.objects.get(name=plugin_name)
    except Plugin.DoesNotExist:
        plugin = sal.plugin.PluginManager.get_plugin_by_name(plugin_name)
        if plugin:
            sal_plugin = Plugin(name=plugin_name, order=utils.unique_plugin_order())
            sal_plugin.save()
    return redirect('plugins_page')


@login_required
@ga_required
def machine_detail_plugin_plus(request, plugin_id):
    _swap_plugin(plugin_id, 1, MachineDetailPlugin)
    return redirect('settings_machine_detail_plugins')


@login_required
@ga_required
def machine_detail_plugin_minus(request, plugin_id):
    _swap_plugin(plugin_id, -1, MachineDetailPlugin)
    return redirect('settings_machine_detail_plugins')


@login_required
@ga_required
def machine_detail_plugin_disable(request, plugin_id):
    plugin = get_object_or_404(MachineDetailPlugin, pk=plugin_id)
    plugin.delete()
    return redirect('settings_machine_detail_plugins')


@login_required
@ga_required
def machine_detail_plugin_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        _ = MachineDetailPlugin.objects.get(name=plugin_name)
    except MachineDetailPlugin.DoesNotExist:
        plugin = sal.plugin.PluginManager.get_plugin_by_name(plugin_name)
        if plugin:
            db_plugin = MachineDetailPlugin(
                name=plugin_name, order=utils.unique_plugin_order(plugin_type='machine_detail'))
            db_plugin.save()
    return redirect('settings_machine_detail_plugins')


@login_required
@ga_required
def settings_report_disable(request, plugin_id):
    plugin = get_object_or_404(Report, pk=plugin_id)
    plugin.delete()
    return redirect('settings_reports')


@login_required
@ga_required
def settings_report_enable(request, plugin_name):
    # only do this if there isn't a plugin already with the name
    try:
        _ = Report.objects.get(name=plugin_name)
    except Report.DoesNotExist:
        plugin = sal.plugin.PluginManager.get_plugin_by_name(plugin_name)
        if plugin:
            report = Report(name=plugin_name)
            report.save()
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
        form = forms.ApiKeyForm(request.POST)
        if form.is_valid():
            new_api_key = form.save()
            return redirect('display_api_key', key_id=new_api_key.id)
    else:
        form = forms.ApiKeyForm()
    c = {'form': form}
    return render(request, 'forms/new_api_key.html', c)


@login_required
@ga_required
def display_api_key(request, key_id):
    api_key = get_object_or_404(ApiKey, pk=int(key_id))
    if api_key.has_been_seen:
        return redirect(index_view)
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

        form = forms.ApiKeyForm(request.POST, instance=api_key)
        if form.is_valid():
            api_key = form.save()
            return redirect(api_keys)
    else:
        form = forms.ApiKeyForm(instance=api_key)
    c = {'form': form, 'api_key': api_key}
    return render(request, 'forms/edit_api_key.html', c)


@login_required
@ga_required
def delete_api_key(request, key_id):
    api_key = get_object_or_404(ApiKey, pk=int(key_id))
    api_key.delete()
    return redirect(api_keys)
