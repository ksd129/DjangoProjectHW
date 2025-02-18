from celery.schedules import crontab, schedule



class TaskSchedule:
    def __init__(self, task_name, schedule, start_time=None, end_time=None, field_db=None, interval=None, limit=None):
        self.task_name = task_name
        self.schedule = schedule
        self.start_time = start_time
        self.end_time = end_time
        self.field_db = field_db
        self.interval = interval
        self.limit = limit

    def to_celery_schedule(self):
        return {
            'task': self.task_name,
            'schedule': self.schedule,
            'kwargs': {
                'start_time': self.start_time,
                'end_time': self.end_time,
                'field_db': self.field_db,
                'interval': self.interval,
                'limit': self.limit
            }
        }

# Definition of static tasks
static_tasks = {
    'get_binance_data_ticker_24h': {
        'task': 'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt',
        # 'schedule': crontab(minute=0, hour='*/12'),
        'schedule': schedule(60.0),
        # 'options': {'expires': 10,},
    }
}

# Definition of dynamic tasks
tasks = [
    TaskSchedule(
        'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_by_parameters',
        crontab(minute=0, hour=0, day_of_month=1),
        field_db='all_candles_1mo_in_1y',
        interval='1M',
        limit=12
    ),
    TaskSchedule(
        'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_by_parameters',
        crontab(minute=0, hour=1),
        field_db='all_candles_1d_in_1mo',
        interval='1d',
        limit=30
    ),
    TaskSchedule(
        'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_by_parameters',
        crontab(minute=20, hour='*'),
        field_db='all_candles_1hr_in_24hr',
        interval='1h',
        limit=24
    ),
    TaskSchedule(
        'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_by_parameters',
        crontab(minute=18, hour='*'),
        field_db='all_candles_5m_in_24hr',
        interval='5m',
        limit=288
    )
]

# Генерация CELERY_BEAT_SCHEDULE
CELERY_BEAT_SCHEDULE = static_tasks.copy()
CELERY_BEAT_SCHEDULE.update({
    f'get_binance_data_candles_{task.interval}': task.to_celery_schedule()
    for task in tasks
})





















# CELERY_BEAT_SCHEDULE = {
#     'get_binance_data_ticker_24h': {
#         'task': 'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt',
#         # 'schedule': crontab(hour='0', minute='0'),
#         'schedule': schedule(60.0),
#         # 'options': {'expires': 10,},
#     },
#     # 'get_binance_data_candles_1m': {
#     #     'task': 'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_1m',
#     #     'schedule': schedule(60.0),
#     #     'args': (10,),
#     #     'options': {'expires': 10,},
#     # },
# 'get_binance_data_candles_1mo_in_1year': {
#         'task': 'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_by_parameters',
#         'schedule': crontab(minute=0, hour=0, day_of_month=1),
#         'kwargs': {
#                     'start_time': None,
#                     'end_time': None,
#                     'field_db': 'all_candles_1mo_in_1y',
#                     'interval': '1M',
#                     'limit': 12
#                     },
#     },
# 'get_binance_data_candles_1d_in_1mo': {
#         'task': 'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_by_parameters',
#         'schedule': crontab(minute=0, hour=1),
#         'kwargs': {
#                     'start_time': None,
#                     'end_time': None,
#                     'field_db': 'all_candles_1d_in_1mo',
#                     'interval': '1d',
#                     'limit': 30
#                     },
#     },
# 'get_binance_data_candles_1hr_in_24hr': {
#         'task': 'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_by_parameters',
#         'schedule': crontab(minute=20, hour='*'),
#         'kwargs': {
#                     'start_time': None,
#                     'end_time': None,
#                     'field_db': 'all_candles_1hr_in_24hr',
#                     'interval': '1h',
#                     'limit': 24
#                     },
#     },
# 'get_binance_data_candles_5m_in_24hr': {
#         'task': 'apps.celery_screening.tasks.tasks.get_ticker_all_pairs_usdt_candles_by_parameters',
#         'schedule': crontab(minute=40, hour='*'),
#         'kwargs': {
#                     'start_time': None,
#                     'end_time': None,
#                     'field_db': 'all_candles_5m_in_24hr',
#                     'interval': '5m',
#                     'limit': 288
#                     },
#     },
#
# }
