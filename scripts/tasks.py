from celery import shared_task

@shared_task(name="scripts.cleanup_logs.cleanup_logs_task")
def cleanup_logs_task():
    from scripts.cleanup_logs import ClenaupLogs
    ClenaupLogs()

@shared_task(name="scripts.pending_order_state_checker.scan_and_process")
def scan_and_process():
    from scripts.pending_order_state_checker import scan_and_process
    scan_and_process()

@shared_task(name="scripts.provider_change.provider_change_task")
def provider_change_task():
    from scripts.provider_change import ProviderChange
    ProviderChange()