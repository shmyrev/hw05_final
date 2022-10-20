from datetime import date


def year(request):
    today = date.today()
    year = today.year
    return {'year': int(year)}
