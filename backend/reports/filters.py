import django_filters

from reports.models import Report


class ReportFilter(django_filters.FilterSet):
    """Фильтр для отчётов."""

    status = django_filters.ChoiceFilter(choices=Report.Status.choices)
    report_type = django_filters.ChoiceFilter(choices=Report.ReportType.choices)
    organization = django_filters.NumberFilter(
        field_name="organization_id",
        label="Organization ID",
    )
    created_from = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="gte",
        label="Created from",
    )
    created_to = django_filters.DateTimeFilter(
        field_name="created_at",
        lookup_expr="lte",
        label="Created to",
    )
    period_start_from = django_filters.DateTimeFilter(
        field_name="period_start",
        lookup_expr="gte",
        label="Period start from",
    )
    period_start_to = django_filters.DateTimeFilter(
        field_name="period_start",
        lookup_expr="lte",
        label="Period start to",
    )

    class Meta:
        model = Report
        fields = [
            "status",
            "report_type",
            "organization",
            "created_from",
            "created_to",
            "period_start_from",
            "period_start_to",
        ]
