import operator
from django.conf import settings
from server.models import *
from django.shortcuts import get_object_or_404

def orderPluginOutput(pluginOutput, page='front', theID=None):
    # Sort by name initially
    output = sorted(pluginOutput, key=lambda k: k['name'])
    
    # Order by the list specified in settings
    
    # Run through all of the names in pluginOutput. If they're not in the PLUGIN_ORDER list, we'll add them to a new one
    not_ordered = []
    for item in output:
            if item['name'] not in settings.PLUGIN_ORDER:
                not_ordered.append(item['name'])
                
    search_items = settings.PLUGIN_ORDER + not_ordered
    lookup = {s: i for i, s in enumerate(search_items)}
    output = sorted(output, key=lambda o: lookup[o['name']])
    if page != 'front':
        if page == 'bu_dashboard':
            business_unit = get_object_or_404(BusinessUnit, pk=theID)
            for item in output:
                for key, ids in settings.LIMIT_PLUGIN_TO_BUSINESS_UNIT.iteritems():
                    if item['name'] == key:
                        if str(theID) in ids or int(theID) in ids:
                            output.remove(item)
        
        if page == 'group_dashboard':
            machine_group = get_object_or_404(MachineGroup, pk=theID)
            # get the group's BU. 
            business_unit = machine_group.business_unit
            for item in output:
                for key, ids in settings.LIMIT_PLUGIN_TO_BUSINESS_UNIT.iteritems():
                    if item['name'] == key:
                        if str(business_unit.id) in ids or int(business_unit.id) in ids:
                            output.remove(item)
    # Loop over all of the items, their width will have been returned 
    col_width = 12
    total_width = 0
    counter = 0
    needs_break = False
    # length of the output, but starting at 0, so subtract one
    length = len(output)-1
    for item in output:
        # reset total width if we went over last time
        # if total_width >= col_width:
#             #total_width = 0
#             needs_break = True
#         # if we've gone through all the items, just stop
        if counter >= length:
            break
#         if total_width+output[counter+1]['width'] > col_width:
#             needs_break = True
        # No point doing anything if the plugin isn't going to return any output
        if int(item['width']) != 0:
            #if total_width+output[counter+1]['width'] > col_width:
            if total_width+item['width'] > col_width:
                item['html'] = '\n</div>\n\n<div class="row">\n'+item['html']
                print 'breaking'
                total_width = item['width']
                needs_break = False
            else:
                total_width = int(item['width']) + total_width
        counter = counter +1
        print item['name']+' total: '+str(total_width)
    
    return output

def getBUmachines(theid):
    business_unit = get_object_or_404(BusinessUnit, pk=theid)
    machine_groups = MachineGroup.objects.filter(business_unit=business_unit).prefetch_related('machine_set').all()

    if machine_groups.count() != 0:    
        machines_unsorted = machine_groups[0].machine_set.all()
        for machine_group in machine_groups[1:]:
            machines_unsorted = machines_unsorted | machine_group.machine_set.all()
    else:
        machines_unsorted = None
    machines=machines_unsorted
    
    return machines