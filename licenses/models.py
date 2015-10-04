from django.db import models

from inventory.models import InventoryItem

from urllib import quote_plus

class License(models.Model):
    item_name = models.CharField(max_length=64, unique=True, primary_key=True)
    total = models.IntegerField(default=0)
    cost_per_seat = models.IntegerField(default=0)
    inventory_name = models.CharField(max_length=256, blank=True)
    inventory_version = models.CharField(max_length=32, blank=True)
    inventory_bundleid = models.CharField(max_length=256, blank=True)
    inventory_bundlename = models.CharField(max_length=256, blank=True)
    inventory_path = models.CharField(max_length=1024, blank=True)
    notes = models.TextField(blank=True)
    
    def used(self):
        # query inventory items to determine how many licenses have been used.
        items = InventoryItem.objects.all()
        if self.inventory_name:
            items = items.filter(name__exact=self.inventory_name)
        if self.inventory_version:
            if self.inventory_version.endswith('*'):
                items = items.filter(
                    version__startswith=self.inventory_version[0:-1])
            else:
                items = items.filter(version__exact=self.inventory_version)
        if self.inventory_bundleid:
            items = items.filter(bundleid__exact=self.inventory_bundleid)
        if self.inventory_bundlename:
            items = items.filter(
                bundlename__exact=self.inventory_bundlename)
        if self.inventory_path:
            items = items.filter(path__exact=self.inventory_path)
        # return a count of distinct machines 
        # that have the item we are looking for
        return items.values('machine').distinct().count()
        
    def inventory_query_string(self):
        '''Returns a web query string for use in building URLs that link to
        the inventory objects being counted'''
        parts = []
        if self.inventory_name:
            parts.append("name=%s" % self.inventory_name)
        if self.inventory_version:
            parts.append("version=%s" % self.inventory_version)
        if self.inventory_bundleid:
            parts.append("bundleid=%s" % self.inventory_bundleid)
        if self.inventory_bundlename:
            parts.append("bundlename=%s" % self.inventory_bundlename)
        if self.inventory_path:
            parts.append("path=%s" % self.inventory_path)
        if parts:
            return quote_plus('?%s' % '&'.join(parts), safe='?&=')
        else:
            return ''
        
    def available(self):
        return self.total - self.used()
        
    class Meta:
        ordering = ['item_name']
