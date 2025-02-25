import logging

logger = logging.getLogger(__name__)
file_handler = logging.FileHandler('apps/celery_screening/logs/task_log.log')
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
