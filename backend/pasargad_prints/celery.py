import os
from celery import Celery
from django.conf import settings

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'pasargad_prints.settings')

app = Celery('pasargad_prints')

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
app.config_from_object('django.conf:settings', namespace='CELERY')

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure task routing
app.conf.task_routes = {
    'products.tasks.*': {'queue': 'products'},
    'orders.tasks.*': {'queue': 'orders'},
    'utils.tasks.*': {'queue': 'default'},
    'cart.tasks.*': {'queue': 'cart'},
    'payments.tasks.*': {'queue': 'payments'},
    # Goshippo shipping tasks use dedicated queue for priority
    'orders.tasks.track_goshippo_shipments': {'queue': 'shipping'},
    'orders.tasks.purchase_goshippo_label': {'queue': 'shipping'},
    'orders.tasks.create_goshippo_shipment': {'queue': 'shipping'},
}

# Task time limits
app.conf.task_annotations = {
    '*': {'rate_limit': '10/s'},
    'utils.email.*': {'rate_limit': '20/m'},
}

@app.task(bind=True)
def debug_task(self):
    print(f'Request: {self.request!r}')