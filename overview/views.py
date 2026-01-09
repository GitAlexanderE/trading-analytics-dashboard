from django.db.models import Count, Sum, Q, FloatField, F, ExpressionWrapper, Case, When, Value
from django.db.models.functions import ExtractMonth, ExtractYear
from django.db.models.fields import IntegerField
from django.shortcuts import render
from django.http import HttpResponse
from .models import ClosedPositions, OpenPositions, Account
import json
from datetime import date, timedelta


def index(request):
    return HttpResponse("Hello world")


def dashboard(request):
    open_positions = OpenPositions.objects.all()
    closed_position = ClosedPositions.objects.all()
    return render(request, 'overview/dashboard.html', {
        'closed_positions': closed_position,
        'open_positions': open_positions,
    })


def statistics(request):
    # Counters for dashboard cards
    open_positions = OpenPositions.objects.all()
    closed_positions = ClosedPositions.objects.order_by('time_close')
    open_count = open_positions.count()
    closed_count = closed_positions.count()

    # Build last equity per day (multiple snapshots)
    account_history = Account.objects.order_by('time_last_update')

    starting_capital = 100000
    last_equity = starting_capital
    equity_by_day = {}

    for a in account_history:
        day = a.time_last_update.date()  # cutting off the time
        last_equity = float(
            round(a.equity or last_equity, 2))  # if a.equity exists take that and if not take last known equity value
        equity_by_day[day] = last_equity  # store the last equity per day date(2026,1,1): 100000,

    # Fill equity every day
    start_date = date(2025, 8, 1)
    end_date = date.today()

    equity_data = []
    previous_equity = starting_capital
    current = start_date

    while current <= end_date:
        if current in equity_by_day:
            previous_equity = equity_by_day[current]

        equity_data.append({
            'time_close': current.strftime('%Y-%m-%d'),
            'equity': previous_equity,
        })  # { "time_close": "2026-01-01", "equity": 100000 }

        current += timedelta(days=1)

    # Compute daily changes
    equity_values = [d['equity'] for d in equity_data]
    equity_change = [0] + [round(equity_values[i] - equity_values[i - 1], 2) for i in range(1, len(equity_values))]
    for i, d in enumerate(equity_data):
        d['equity_change'] = equity_change[i]


    # Weekdays stats

    weekdays = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday']
    # Initialize starting stats
    stats_dict_weekday = {day: {'total_positions': 0, 'wins': 0, 'total_profit': 0, 'winrate': 0}  for day in weekdays}

    '''{
    'Monday': {'total_trades': 0, 'wins': 0, 'profit': 0.0, 'winrate': 0.0},
    'Tuesday': {...},
    }
    '''

    weekday_order = Case(
        When(weekday = 'Monday', then=Value('1')),
        When(weekday = 'Tuesday', then=Value('2')),
        When(weekday = 'Wednesday', then=Value('3')),
        When(weekday = 'Thursday', then=Value('4')),
        When(weekday = 'Friday', then=Value('5')),
        output_field = IntegerField()
    )

    weekday_stats = (
        ClosedPositions.objects
        .values('weekday')
        .annotate(
            total_positions=Count('position_id'),
            wins=Count('position_id', filter=Q(profit__gt=0)),
            # Query condition: profit greater than 0; filter: only if profit > 0 count position_id
            total_profit=Sum('profit'),
            winrate=Case( # Case so no /0 if total_positions = 0
                When(total_positions=0, then=Value(0.0)), # SQL: CASE WHEN...THEN ELSE -> when, then, default
                default=ExpressionWrapper(
                    F('wins') * 100.0 / F('total_positions'),
                    output_field=FloatField()  # no matter result of win/trades it's always a float result
                ),
                output_field=FloatField()  # no matter "when" or "default" result is always a float

            ),
            weekday_sort = weekday_order,
        )
        .order_by('weekday_sort')
    )

    '''
    {
    'weekday': Monday, 
    'total_positions': 12,
    'wins': 7,
    'total_profit': 400,
    'winrate': 60
    }
    '''

    for stats in weekday_stats:
        day = stats['weekday']
        stats_dict_weekday[day] = {
            'total_positions': stats['total_positions'],
            'wins': stats['wins'],
            'total_profit': stats['total_profit'],
            'winrate': stats['winrate'],
        }


    # Sessions

    sessions = ['Asia', 'London', 'Lunch', 'New York', 'London Close', 'Out of Session']
    stats_dict_session = {session: {'total_positions': 0, 'wins': 0, 'total_profit': 0, 'winrate': 0} for session in sessions}

    '''
    {
    'Asia': {'total_positions': 0, 'wins': 0, 'total_profit': 0, 'winrate': 0},
    'London': {...},
    }
    '''

    session_order = Case(
        When(session = 'Asia', then=Value('1')),
        When(session = 'London', then=Value('2')),
        When(session = 'New York', then=Value('3')),
        When(session = 'London Close', then=Value('4')),
        When(session = 'Out of Session', then=Value('5')),
        output_field = IntegerField()
    )

    sessions_stats = (
        ClosedPositions.objects
        .values('session')
        .annotate(
            total_positions=Count('position_id'),
            wins=Count('position_id', filter=Q(profit__gt=0)),
            total_profit=Sum('profit'),
            winrate= Case(
                When(total_positions=0, then=Value(0.0)),
                default=ExpressionWrapper(
                    F('wins') * 100.0 / F('total_positions'),
                    output_field=FloatField()
                ),
                output_field=FloatField()
            )
        )
    )

    for stats in sessions_stats:
        session = stats['session']
        stats_dict_session[session] = {
            'total_positions': stats['total_positions'],
            'wins': stats['wins'],
            'total_profit': stats['total_profit'],
            'winrate': stats['winrate'],
        }


    # Monthly winrate

    month_names = {
        1: 'January',
        2: 'February',
        3: 'March',
        4: 'April',
        5: 'May',
        6: 'June',
        7: 'July',
        8: 'August',
        9: 'September',
        10: 'October',
        11: 'November',
        12: 'December'
    }

    stats_dict_monthly = {month: {'total_positions': 0, 'wins': 0, 'total_profit': 0, 'winrate': 0} for month in month_names.values()}

    monthly_stats = (
        ClosedPositions.objects
        .annotate(month = ExtractMonth('time_open'))
        .values('month')
        .annotate(
            total_positions=Count('position_id'),
            wins=Count('position_id', filter=Q(profit__gt=0)),
            total_profit=Sum('profit'),
            winrate= Case(
                When(total_positions=0, then=Value(0.0)),
                default=ExpressionWrapper(
                    F('wins') * 100.0 / F('total_positions'),
                    output_field=FloatField(),
                ),output_field=FloatField()
            )
        )
        .order_by('month')
    )

    for stats in monthly_stats:
        month_num = stats['month']
        month_name = month_names[month_num]

        stats_dict_monthly[month_name] = {
            'total_positions': stats['total_positions'],
            'wins': stats['wins'],
            'total_profit': stats['total_profit'],
            'winrate': stats['winrate'],
        }



    # Yearly winrate

    years = ['2025','2026', '2027']
    stats_dict_year = {year: {'total_positions': 0, 'wins': 0, 'total_profit': 0, 'winrate': 0} for year in years}


    yearly_stats = (
        ClosedPositions.objects
        .annotate(year = ExtractYear('time_open'))
        .values('year')
        .annotate(
            total_positions=Count('position_id'),
            wins=Count('position_id', filter=Q(profit__gt=0)),
            total_profit=Sum('profit'),
            winrate=Case(
                When(total_positions=0, then=Value(0.0)),
                default=ExpressionWrapper(
                    F('wins') * 100.0 / F('total_positions'),
                    output_field=FloatField()
                ), output_field=FloatField(),
            )
        )
        .order_by('year')
    )

    for stats in yearly_stats:
        year = str(stats['year']) # str because ExtractYear gives back an integer but the stats_dict_year looks for a string
        stats_dict_year[year] = {
            'total_positions': stats['total_positions'],
            'wins': stats['wins'],
            'total_profit': stats['total_profit'],
            'winrate': stats['winrate'],
        }

    total_profit_all_years = sum(stats['total_profit'] for stats in stats_dict_year.values())

    # Account trade mode
    account = Account.objects.last()

    # Mapping
    stats_dict_account = {
        0: 'Demo',
        1: 'Live',
        2: 'Strategy Tester',
        3: 'Contest Mode'
    }

    trade_mode = stats_dict_account.get(account.trade_mode, 'Unknown')


    return render(request, 'overview/statistics.html', {
        'open_count': open_count,
        'closed_count': closed_count,
        'equity_data_json': json.dumps(equity_data),
        'weekday_stats': stats_dict_weekday,
        'sessions_stats': stats_dict_session,
        'monthly_stats': stats_dict_monthly,
        'yearly_stats': stats_dict_year,
        'trade_mode': trade_mode,
        'total_profit_all_years': total_profit_all_years,
    })



def closed_positions(request):
    closed_position = ClosedPositions.objects.all().order_by('time_close')
    return render(request, 'overview/closed_positions.html', {'closed_positions': closed_position})
