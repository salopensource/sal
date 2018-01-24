from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.template.context_processors import csrf
from django.db.models import CharField, Q
from django.http import JsonResponse, StreamingHttpResponse
import sal.settings as settings

import search.utils as utils
from server.models import *
from search.models import *
from search.forms import *
import search.views
import server.utils
from inventory.models import *

import json
import re
import unicodecsv as csv

@login_required
@csrf_exempt
def index(request):
    user = request.user
    user_level = user.userprofile.level
    if ('q' in request.GET) and request.GET['q'].strip():
        query_string = request.GET['q'].strip()
    else:
        return redirect(search.views.list)
    # Make sure we're searching across Machines the user has access to:
    machines = Machine.objects.all()
    if user_level != 'GA':
        for business_unit in BusinessUnit.objects.all():
            if business_unit not in request.user.businessunit_set.all():
                machines = machines.exclude(machine_group__business_unit = business_unit)

    template = 'search/basic_search.html'

    machines = quick_search(machines, query_string)

    title = "Search results for %s" % query_string
    c = {'user': request.user, 'machines': machines, 'title':title, 'request':request}
    return render(request, template, c)

def quick_search(machines, query_string):
    skip_fields = [
        'id',
        'machine_group',
        'report',
        'activity',
        'errors',
        'warnings',
        'install_log',
        'puppet_errors',
        'install_log_hash',
        'deployed',
        'report_format',
        'broken_client',
        'hd_percent',
        'memory',
        'memory_kb',
        'hd_space',
        'hd_total',
        'cpu_type',
        'cpu_speed',
        'first_checkin',
        'last_checkin'
    ]

    fields = []
    for f in Machine._meta.fields:
        if f.name not in skip_fields:
            fields.append(f)

    queries = [Q(**{"%s__icontains" % f.name: query_string}) for f in fields]

    # for f in settings.SEARCH_FACTS:
    #     query = {
    #             'facts__fact_name': f,
    #             'facts__fact_data__icontains': query_string
    #         }
    #     queries.append(Q(**query))

    # for f in settings.SEARCH_CONDITIONS:
    #     query = {
    #         'conditions__condition_name': f,
    #         'conditions__condition_data__icontains': query_string
    #     }
    #     queries.append(Q(**query))

    query = {'searchcache__search_item__icontains': query_string}
    queries.append(Q(**query))
    qs = Q()
    for query in queries:
        qs = qs | query

    return machines.filter(qs).values('id','serial', 'hostname', 'console_user', 'last_checkin').distinct()

# All saved searches
@login_required
def list(request):
    saved_searches = SavedSearch.objects.filter(save_search=True)
    user = request.user
    user_level = user.userprofile.level
    c = {'request': request,
        'user': request.user,
        'saved_searches': saved_searches,
        'user_level': user_level
        }
    return render(request, 'search/list.html', c)

def search_machines(search_id, machines, full=False):
    saved_search = get_object_or_404(SavedSearch, pk=search_id)
    search_groups = saved_search.searchgroup_set.all()
    queries = Q()
    queries_list = []
    search_group_counter = 0
    for search_group in search_groups:
        if search_group_counter != 0:
            group_operator = search_group.and_or
        else:
            group_operator = None

        search_row_counter = 0
        row_queries = Q()
        row_queries_list = []
        for search_row in search_group.searchrow_set.all():
            if search_row_counter != 0:
                row_operator = search_row.and_or
            else:
                row_operator = None
            search_row_counter = search_row_counter + 1
            # Get the operator
            operators = {
                'Contains': '__icontains',
                '=': '__exact',
                '!=': '', # We negate this later on
                '<': '__lt',
                '<=': '__lte',
                '>': '__gt',
                '>=': '__gte',
            }
            for display_operator, actual_operator in operators.iteritems():
                if search_row.operator == display_operator:
                    operator = actual_operator
                    break
            # Get the model & field
            model = None
            if search_row.search_models == 'Machine':
                model = Machine
                querystring = {
                    '%s%s' % (search_row.search_field, operator): search_row.search_term
                }
                if operator != '':
                    q_object = Q(**querystring)
                else:
                    q_object = ~Q(**querystring)
            elif search_row.search_models == 'Facter':
                model = Fact
                prepend = 'facts__'
                querystring = {
                    'facts__fact_name': search_row.search_field,
                    'facts__fact_data%s' % (operator): search_row.search_term
                }
                if operator != '':
                    q_object = Q(**querystring)
                else:
                    q_object = ~Q(**querystring)

            elif search_row.search_models == 'Condition':
                model = Condition
                querystring = {
                    'conditions__condition_name': search_row.search_field,
                    'conditions__condition_data%s' % (operator): search_row.search_term
                }
                if operator != '':
                    q_object = Q(**querystring)
                else:
                    q_object = ~Q(**querystring)


            elif search_row.search_models == 'Application Inventory':
                model = Application
                if search_row.search_field == 'Name':
                    search_field = 'name'
                elif search_row.search_field == 'Bundle ID':
                    search_field = 'bundleid'
                querystring = {
                    'inventoryitem__application__%s%s' % (search_field, operator): search_row.search_term
                }

                if operator != '':
                    q_object = Q(**querystring)
                else:
                    q_object = ~Q(**querystring)

            elif search_row.search_models == 'External Script':
                # It must be an exernal thingie if we're here
                model = PluginScriptRow
                # get the name of the plugin and row
                plugin_name, row = search_row.search_field.split('=>')
                submission_and_script_name = '%s: %s' % (plugin_name, row)
                querystring = {

                    'pluginscriptsubmission__pluginscriptrow__submission_and_script_name': submission_and_script_name,
                    'pluginscriptsubmission__pluginscriptrow__pluginscript_data%s'% (operator): search_row.search_term
                }
                if operator != '':
                    q_object = Q(**querystring)

                else:
                    q_object = ~Q(**querystring)

            elif search_row.search_models == 'Application Version':

                model = InventoryItem
                app_name, bundleid = search_row.search_field.split('=>')
                querystring = {
                    'inventoryitem__application__name': app_name,
                    'inventoryitem__application__bundleid': bundleid,
                    'inventoryitem__version%s' % (operator): search_row.search_term
                }
                if operator != '':
                    q_object = Q(**querystring)

                else:
                    q_object = ~Q(**querystring)


            # Add a row operator if needed
            if row_operator != None:
                if row_operator == 'AND':
                    row_queries.add(q_object, Q.AND)

                elif row_operator == 'OR':
                    row_queries.add(q_object, Q.OR)
            else:
                # Add to row_queries
                # row_queries.add(q_object, Q.AND)
                row_queries = q_object

        if group_operator != None:
            if group_operator == 'AND':
                queries.add(row_queries, Q.AND)
            elif group_operator == 'OR':
                queries.add(row_queries, Q.OR)
        else:

            queries = row_queries

        search_group_counter = search_group_counter + 1
    print queries

    if full == True:
        machines = machines.filter(queries).distinct()
    else:
        machines = machines.filter(queries).values('id','serial', 'hostname', 'console_user', 'last_checkin').distinct()
    return machines

# Show search
@login_required
def run_search(request, search_id):
    # Placeholder
    user_level = request.user.userprofile.level
    machines = Machine.objects.all()
    if user_level != 'GA':
        for business_unit in BusinessUnit.objects.all():
            if business_unit not in request.user.businessunit_set.all():
                machines = machines.exclude(
                    machine_group__business_unit = business_unit
                    )

    machines = search_machines(search_id, machines)
    saved_search = get_object_or_404(SavedSearch, pk=search_id)
    c = {'request': request, 'user': request.user, 'search': saved_search, 'machines':machines}
    return render(request, 'search/search_machines.html', c)

# New search
@login_required
def new_search(request):
    # Create a new search
    new_search = SavedSearch()
    new_search.save()

    # Create a new search group
    search_group = SearchGroup(
        saved_search=new_search,
        position=utils.next_position(new_search)
    )
    search_group.save()

    return redirect(search.views.build_search, new_search.id)

# Save search
@login_required
def save_search(request, search_id):
    saved_search = get_object_or_404(SavedSearch, pk=search_id)

    if request.method == 'POST':
        form = SaveSearchForm(request.POST, instance=saved_search)
        if form.is_valid():
            row = form.save(commit=False)
            row.save_search = True
            row.save()
            return redirect(search.views.build_search, saved_search.id)
    else:
        form = SaveSearchForm(instance=saved_search)

    c = {'form': form, 'saved_search':saved_search}
    return render(request, 'search/save_search_form.html', c)

# Build search
@login_required
def build_search(request, search_id):
    user = request.user
    user_level = user.userprofile.level
    new_search = get_object_or_404(SavedSearch, pk=search_id)
    search_groups = SearchGroup.objects.filter(saved_search=new_search)
    c = {
        'request': request,
        'user': request.user,
        'search': new_search,
        'search_groups':search_groups
    }
    return render(request, 'search/build_search.html', c)

# Delete search
@login_required
def delete_search(request, search_id):
    user_level = request.user.userprofile.level
    saved_search = get_object_or_404(SavedSearch, pk=search_id)
    if user_level == 'GA' or request.user == saved_search.created_by:
        saved_search.delete()
    return redirect(search.views.list)

@login_required
def edit_search(request, search_id):
        saved_search = get_object_or_404(SavedSearch, pk=search_id)
        user = request.user
        user_level = user.userprofile.level
        if user_level != 'GA' and saved_search.created_by != request.user:
            return redirect(search.views.list)
        if request.method == 'POST':
            form = SearchRowForm(request.POST, instance=search_row)
            if form.is_valid():
                row = form.save(commit=False)
                row.save_search = True
                row.save()
                return redirect(search.views.build_search, search_row.search_group.saved_search.id)
        else:
            form = SearchRowForm(instance=search_row)
        c = {'form': form, 'saved_search':saved_search}
        return render(request, 'search/edit_search_name_form.html', c)

# New Group
@login_required
def new_search_group(request, search_id):
    new_search = get_object_or_404(SavedSearch, pk=search_id)
    search_group = SearchGroup(
        saved_search=new_search,
        position=utils.next_position(new_search)
    )
    search_group.save()
    return redirect(search.views.build_search, new_search.id)

# Edit group - not required at the moment as we have a toggle for and / or
# @login_required
# def edit_group(request, search_group_id):
#     search_group = get_object_or_404(SearchGroup, pk=search_group_id)
#     saved_search = search_group.saved_search
#     user_level = request.user.userprofile.level
#     if user_level == 'GA' or request.user == saved_search.created_by:
#         search_group.delete()
#     return redirect(search.views.build_search, saved_search.id)

# And or toggle for group
@login_required
def group_and_or(request, search_group_id):
    search_group = get_object_or_404(SearchGroup, pk=search_group_id)
    saved_search = search_group.saved_search
    user_level = request.user.userprofile.level
    if user_level == 'GA' or request.user == saved_search.created_by:
        if search_group.and_or == 'AND':
            search_group.and_or = 'OR'
        else:
            search_group.and_or = 'AND'
        search_group.save()
    return redirect(search.views.build_search, saved_search.id)

# Delete group
@login_required
def delete_group(request, search_group_id):
    search_group = get_object_or_404(SearchGroup, pk=search_group_id)
    saved_search = search_group.saved_search
    user_level = request.user.userprofile.level
    if user_level == 'GA' or request.user == saved_search.created_by:
        search_group.delete()
    return redirect(search.views.build_search, saved_search.id)

# New row
@login_required
def new_search_row(request, search_group_id):
    search_group = get_object_or_404(SearchGroup, pk=search_group_id)
    if request.user.userprofile.level != 'GA' and search_group.saved_search.created_by != request.user:
        return redirect(search.views.list)
    if request.method == 'POST':
        form = SearchRowForm(request.POST)
        if form.is_valid():
            row = form.save(commit=False)
            row.search_group = search_group
            row.position = utils.next_position(search_group, model='search_row')
            row.save()
            return redirect(search.views.build_search, search_group.saved_search.id)
    else:
        form = SearchRowForm(search_group=search_group)

    c = {'form': form, 'search_group':search_group}

    return render(request, 'search/new_search_form.html', c)

# Edit row
@login_required
def edit_search_row(request, search_row_id):
    search_row = get_object_or_404(SearchRow, pk=search_row_id)

    if request.method == 'POST':
        form = SearchRowForm(request.POST, instance=search_row)
        if form.is_valid():
            row = form.save(commit=False)
            row.save_search = True
            row.save()
            return redirect(search.views.build_search, search_row.search_group.saved_search.id)
    else:
        form = SearchRowForm(instance=search_row)
        search_fields = []
        if search_row.search_models.lower() == 'facter':
            rows = SearchFieldCache.objects.filter(search_model='Facter').distinct()

        elif search_row.search_models.lower() == 'condition':
            rows = SearchFieldCache.objects.filter(search_model='Condition').distinct()

        elif search_row.search_models.lower() == 'external script':
            rows = SearchFieldCache.objects.filter(search_model='External Script').distinct()

        elif search_row.search_models.lower() == 'application inventory':
            rows = SearchFieldCache.objects.filter(search_model='Application Inventory').distinct()

        elif search_row.search_models.lower() == 'application version':
            rows = SearchFieldCache.objects.filter(search_model='Application Version').distinct()

        elif search_row.search_models.lower() == 'machine':
            rows = SearchFieldCache.objects.filter(search_model='Machine').distinct()

        for row in rows:
            search_fields.append((row.search_field, row.search_field,))

        if len(search_fields) != 0:
            form.fields['search_field'].choices = sorted(search_fields)

        form.fields['search_field'].initial = search_row.search_field
    c = {'form': form, 'search_row':search_row}
    return render(request, 'search/edit_search_form.html', c)

# Delete Row
@login_required
def delete_row(request, search_row_id):
    search_row = get_object_or_404(SearchRow, pk=search_row_id)
    search_group = search_row.search_group
    saved_search = search_group.saved_search
    user_level = request.user.userprofile.level
    if user_level == 'GA' or request.user == saved_search.created_by:
        search_row.delete()
    return redirect(search.views.build_search, saved_search.id)

# Response for ajax to pupulate dropdown
@login_required
@csrf_exempt
def get_fields(request, model):
    search_fields = []
    if model.lower() == 'machine':
        cache_items = SearchFieldCache.objects.filter(search_model='Machine')
        for cache_item in cache_items:
            search_fields.append(cache_item.search_field)

    elif model.lower() == 'facter':
        cache_items = SearchFieldCache.objects.filter(search_model='Facter')
        for cache_item in cache_items:
            search_fields.append(cache_item.search_field)

    elif model.lower() == 'condition':
        cache_items = SearchFieldCache.objects.filter(search_model='Condition')
        for cache_item in cache_items:
            search_fields.append(cache_item.search_field)

    elif model.lower() == 'external script':
        cache_items = SearchFieldCache.objects.filter(search_model='External Script')
        for cache_item in cache_items:
            search_fields.append(cache_item.search_field)

    elif model.lower() == 'application inventory':
        cache_items = SearchFieldCache.objects.filter(search_model='Application Inventory')
        for cache_item in cache_items:
            search_fields.append(cache_item.search_field)

    elif model.lower() == 'application version':
        cache_items = SearchFieldCache.objects.filter(search_model='Application Version')
        for cache_item in cache_items:
            search_fields.append(cache_item.search_field)

    output = {}
    output['fields'] = sorted(search_fields)
    return JsonResponse(output)

class Echo(object):
    """An object that implements just the write method of the file-like interface.
    """
    def write(self, value):
        """Write the value by returning it, instead of storing in a buffer."""
        return value

def get_csv_row(machine, facter_headers, condition_headers, plugin_script_headers):
    row = []
    for name, value in machine.get_fields():
        if name != 'id' and name !='machine_group' and name != 'report' and name != 'activity' and name != 'os_family' and name != 'install_log' and name != 'install_log_hash':
            try:
                row.append(server.utils.safe_unicode(value))
            except:
                row.append('')

    row.append(machine.machine_group.business_unit.name)
    row.append(machine.machine_group.name)
    return row

def stream_csv(header_row, machines, facter_headers, condition_headers, plugin_script_headers): # Helper function to inject headers
    if header_row:
        yield header_row
    for machine in machines:
        yield get_csv_row(machine, facter_headers, condition_headers, plugin_script_headers)

@login_required
def export_csv(request, search_id):
    user = request.user
    title = None
    machines = Machine.objects.all().defer('report','activity','os_family','install_log', 'install_log_hash')

    machines = search_machines(search_id, machines, full=True)

    saved_search = get_object_or_404(SavedSearch, pk=search_id)
    pseudo_buffer = Echo()
    writer = csv.writer(pseudo_buffer)

    # Fields
    header_row = []
    fields = Machine._meta.get_fields()
    for field in fields:
        if not field.is_relation and field.name != 'id' and field.name != 'report' and field.name != 'activity' and field.name != 'os_family' and field.name != 'install_log' and field.name != 'install_log_hash':
            header_row.append(field.name)


    facter_headers = []
    condition_headers = []
    plugin_script_headers = []

    header_row.append('business_unit')
    header_row.append('machine_group')

    response = StreamingHttpResponse(
            (writer.writerow(row) for row in stream_csv(
                                            header_row=header_row,
                                            machines=machines,
                                            facter_headers=facter_headers,
                                            condition_headers=condition_headers,
                                            plugin_script_headers=plugin_script_headers)),
            content_type="text/csv")
    # Create the HttpResponse object with the appropriate CSV header.
    if getattr(settings, 'DEBUG_CSV', False):
        pass
    else:
        response['Content-Disposition'] = 'attachment; filename="%s.csv"' % saved_search.name


    return response
