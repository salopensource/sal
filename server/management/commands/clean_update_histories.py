"""Remove redundant UpdateHistoryItem entries."""


from django.core.management.base import BaseCommand

from server.models import *


class Command(BaseCommand):
    help = 'Remove redundant update history items.'

    def handle(self, *args, **options):
        update_histories = UpdateHistory.objects.all()
        output_fmt = "{} {}: ({}) status: {}"
        # TODO: Remove limitation
        for update_history in update_histories:
            if update_history.updatehistoryitem_set.count() > 1:
                items = update_history.updatehistoryitem_set.order_by('recorded')
                latest = None
                for next_item in items:
                    if latest is None:
                        latest = next_item
                        action = "Keeping"
                    else:
                        if next_item.status == latest.status:
                            next_item.delete()
                            action = "Deleting"
                        else:
                            latest = next_item
                            action = "Keeping"
                    self.stdout.write(
                        output_fmt.format(
                            action, next_item.update_history.name, next_item.recorded,
                            next_item.status))
