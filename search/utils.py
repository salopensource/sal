from search.models import *
from django.db.models import Max

def next_position(search_object, model='search_group'):
    """returns the next highest position integer
    for creating a new search group"""

    if model=='search_group':
        search_groups = SearchGroup.objects.filter(saved_search=search_object)
    elif model=='search_row':
        search_groups = SearchRow.objects.filter(search_group=search_object)


    print search_groups.count()
    if search_groups.count() == 0:
        return 0
    else:
        # position = 0
        # for search_group in search_groups:
        #     if search_group.position > position:
        #         position = search_group.position
        # return position
        print search_groups.aggregate(Max('position'))['position__max'] + 1
        return search_groups.aggregate(Max('position'))['position__max'] + 1
