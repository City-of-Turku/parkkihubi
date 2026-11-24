from dateutil.relativedelta import relativedelta
from django.core.management.base import BaseCommand
from django.db.models import Count, Max, Min
from django.utils import timezone

from parkings.models import ArchivedPermit, Permit


class Command(BaseCommand):
    help = "Archive Permits that ended more than given number of days ago."

    def add_arguments(self, parser):
        parser.add_argument(
            "--limit", "-l", type=int, metavar="N",
            help="Number of permits to archive. This will archive "
                 "at most N oldest permits.")
        parser.add_argument(
            "--keep-days", "-m", type=int, required=True, metavar="N",
            help="Number of days to keep untouched. This will archive "
                 "all permits that have ended more than N days ago.")
        parser.add_argument(
            "--dry-run", "-n", action="store_true",
            help="Do a dry-run, i.e. nothing is actually archived.")
        parser.add_argument(
            "--batch-size", "-b", type=int, default=10000,
            help="Batch size: How many permits to process at a time")

    def handle(self, limit=None, keep_days=None, batch_size=10000,
               dry_run=False, verbosity=1, **kwargs):
        self.verbosity = verbosity
        end_time = timezone.now() - relativedelta(days=keep_days)
        to_archive = Permit.objects.all_items_end_before(end_time)

        total_count = to_archive.count()
        count = limit if limit and total_count > limit else total_count

        if not count or limit == 0:
            self.stdout.write("Nothing to archive")
            return

        if verbosity >= 1:
            self.stdout.write("{} archive {}{} permits...".format(
                "Would" if dry_run else "Will", count,
                " (out of {})".format(total_count)
                if count != total_count else ""))
        self._show_stats()

        try:
            archived = to_archive.archive(
                batch_size=batch_size, limit=limit, dry_run=dry_run)
        except KeyboardInterrupt:
            self.stdout.write("\n  -> Interrupted!\n")
        else:
            self.stdout.write(
                ("Would have archived" if dry_run else "Archived")
                + " {} permits".format(archived))
        self._show_stats()

    def _show_stats(self):
        if self.verbosity < 1:
            return
        for model in [ArchivedPermit, Permit]:
            stats = model.objects.aggregate(
                a=Min("created_at"), b=Max("created_at"), c=Count("*"))
            self.stdout.write(
                "{:15} objects:   Count: {:11,.0f}   Created: {} -- {}".format(
                    model.__name__, stats["c"], stats["a"], stats["b"]))
