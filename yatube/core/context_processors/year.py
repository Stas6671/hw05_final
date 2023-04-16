from django.utils import timezone


def year(request):
    todays_date = timezone.now()
    return {'year': todays_date.year}
