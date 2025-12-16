from datetime import timedelta
import random

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.utils import timezone

from parkings.models import Operator, Parking
from parkings.models.enforcement_domain import EnforcementDomain


class Command(BaseCommand):
    help = (
        "Generate test parkings with varying end times for development."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--per-bucket",
            type=int,
            default=10,
            help="How many parkings to create for each day-offset bucket.",
        )
        parser.add_argument(
            "--bucket-days",
            type=str,
            default="0,1,3,7,14,30,60,90,120",
            help=(
                "Comma-separated list of day offsets (e.g. '0,7,30') that will "
                "be subtracted from now to set time_end."
            ),
        )
        parser.add_argument(
            "--duration-hours",
            type=float,
            default=2.0,
            help="Length of each parking; start time is end minus this duration.",
        )
        parser.add_argument(
            "--open-count",
            type=int,
            default=5,
            help="How many ongoing parkings to create with time_end=None.",
        )
        parser.add_argument(
            "--operator-username",
            type=str,
            default="test-parking-operator",
            help="Username for the operator; created if missing.",
        )

    def handle(
        self,
        per_bucket,
        bucket_days,
        duration_hours,
        open_count,
        operator_username,
        **kwargs,
    ):
        operator = self._get_or_create_operator(operator_username)
        EnforcementDomain.get_default_domain()

        now = timezone.now()
        buckets = self._parse_buckets(bucket_days)
        created = 0

        for days in buckets:
            for index in range(per_bucket):
                time_end = now - timedelta(days=days, minutes=random.randint(0, 59))
                duration = timedelta(
                    hours=duration_hours, minutes=random.randint(0, 30)
                )
                time_start = time_end - duration
                Parking.objects.create(
                    operator=operator,
                    registration_number=f"TST-{days:03d}-{index:03d}",
                    time_start=time_start,
                    time_end=time_end,
                )
                created += 1

        for index in range(open_count):
            time_start = now - timedelta(hours=random.randint(1, 24))
            Parking.objects.create(
                operator=operator,
                registration_number=f"TST-OPEN-{index:03d}",
                time_start=time_start,
                time_end=None,
            )
            created += 1

        self.stdout.write(
            f"Created {created} test parkings "
            f"({len(buckets) * per_bucket} ended, {open_count} open)."
        )

    def _parse_buckets(self, bucket_days):
        buckets = []
        for part in bucket_days.split(","):
            part = part.strip()
            if not part:
                continue
            try:
                buckets.append(int(part))
            except ValueError:
                raise ValueError(f"Invalid bucket value '{part}', expected integers")
        return buckets

    def _get_or_create_operator(self, username):
        user_model = get_user_model()
        user_defaults = {"email": f"{username}@example.invalid", "is_active": True}
        user, _ = user_model.objects.get_or_create(
            username=username, defaults=user_defaults
        )
        operator, _ = Operator.objects.get_or_create(
            user=user, defaults={"name": "Test Parking Operator"}
        )
        return operator

