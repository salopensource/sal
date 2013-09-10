# Create your views here.
from models import *
from django.contrib.auth.decorators import login_required, permission_required
from django.template import RequestContext, Template, Context
from django.utils import simplejson
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.http import HttpResponse, Http404
from django.contrib.auth.models import Permission, User
from django.conf import settings
from django.core.context_processors import csrf
from django.shortcuts import render_to_response, get_object_or_404, redirect
from datetime import datetime, timedelta


#from forms import *

@login_required 
def index(request):
    # Get the current user's Business Units
    user = request.user
    import logging
    logger = logging.getLogger(__name__)
    logger.info(user.businessunit_set.count())
    if user.businessunit_set.count() == 1:
        # user only has one BU, redirect to it
        for bu in user.businessunit_set.all():
            return redirect('server.views.bu_dashboard', bu_id=bu.id)
            break
    else:
        # user has many BU's display them all in a friendly manner
        business_units = user.businessunit_set.all()
        c = {'user': request.user, 'business_units': business_units}
        return render_to_response('server/index.html', c, context_instance=RequestContext(request)) 

# New BU
   
# BU Dashboard
# Need a filter to make sure that the user has access to the BU
@login_required 
def bu_dashboard(request, bu_id):
    user = request.user
    user_level = user.userprofile.level
    business_unit = get_object_or_404(BusinessUnit, pk=bu_id)
    if business_unit not in user.businessunit_set.all():
        return redirect(index)
    # Get the groups within the Business Unit
    machine_groups = business_unit.machinegroup_set.all
    c = {'user': request.user, 'machine_groups': machine_groups, 'user_level': user_level}
    return render_to_response('server/bu_dashboard.html', c, context_instance=RequestContext(request))

# Machine Group Dashboard

# New Group

# Edit Group

# Delete Group

# Machine detail

# checkin