# Ahem
Simple Notifications Framework

# Quickstart

## Notifications

```python
from ahem import Notification, QuerySetScope, SingleUserScope

class SystemBroadcast(Notification):
    """
    A notification type that broadcasts to the entire system.
    """
    name = 'system_broadcast' # a unique identifier for the notification
    
    scope = QuerySetScope(Shopper.objects) # the scope of the notification - this one goes to every Shopper
    trigger_type = CalendarSchedule(timedelta(day_of_month=1))

    backends = ['email']

    templates = {
    	'default':'example/system_broadcast.html', 
    	'email': 'example/system_broadcast_email.html' # 'email' is the backend name
    }


class AdminReport(Notification):
	"""
	Weekly report to system admins
	"""

	name = 'admin_report'

	scope = SingleUserScope(lookup_context_key='email', lookup_field='email')
	trigger_type = CalendarSchedule(timedelta(day_of_week=2))
	defatult_context = {'email': 'admin@axilent.com'}

	backends = ['email']
	templates = {
    	'default':'example/admin_report.html', 
    	'email': 'example/admin_report_email.html'
    }

    def get_template_context_data(self, user, context, backend, notification_settings):
    	# returns a dictionary with the context to be passed when rendering the template
    	# - user -> the user being notified
    	# - context -> the context passed when the notification was triggered
    	# - backend -> the backend name
    	# - notification_settings -> a dictionary with the key values settings for the user in the backend
    	return {}


class AbandonedCartReachout(Notification):
    """
    A notification received after someone abandons a shopping cart.
    """
    name = 'abandoned_cart_reachout'
    
    scope = SingleUserScope() # requires a non-anonymous user, 'user_id' must be in the context
    trigger_type = NotificationEvent(
    	'cart-abandoned',
    	default_delay=timedelta(days=2))

    required_template_context = ['cart_item_ids']

    backends = ['mobile']
    templates = {
    	'default':'example/abandoned_cart_reachout.html',
        'mobile':'example/abandoned_cart_reachout_mobile.html'
   	}

   	def get_template_context_data(self, user, context, backend, notification_settings):
   		context['cart_items'] = CartItem.objects.filter(id__in=context['cart_item_ids'])
   		return context


class NewProductsAvailable(Notification):
	"""
	Notifies all users about a new products. It's also possible to filter
	only female or male users.
	"""
	name = 'new_products_available'

	scope = QuerySetScope(Users.objects)
	trigger_type = NotificationEvent('new-product')

	required_template_context = ['product_ids']

	backends = ['mobile']
    templates = {
    	'default':'example/new_products_available.html',
   	}

	def get_recipient_users(self, queryset, context):
		gender_filter = context.get('gender_filter', None)

		if gender_filter:
			queryset = queryset.filter(gender__in=gender_filter)

		return queryset.all()


class SumupNotification(Notification):
	"""
	Notifies updates according to choosen user frequency
	"""
	name = 'sumup'

	scope = QuerySetScope(User.objects)
	trigger_type = CalendarSchedule(timedelta(day_of_week=[2,3,4,5,6]))

	default_notification_settings = {
		'frequency': 'daily'
	}

	backends = ['email']
	templates = {
    	'default':'example/sumup.html',
   	}

   	def get_template_context_data(self, user, context, backend, notification_settings):
   		if notification_settings['frequency'] == 'daily':
   			context['items'] = # filter only the updates for the day
   		if notification_settings['frequency'] == 'weekly':
   			context['items'] = # filter only the updated of the week
   		return context

   	def should_be_sent(self, user, context, backend, notification_settings):
   		# allows conditional logic before sending the notification
   		# returns True if it should be sent
   		if notification_settings['frequency'] == 'daily':
   			return True
   		if notification_settings['frequency'] == 'weekly' and timedelta(day_of_week=1):
   			return True
   		return False
```

Notifications with a NotificationEvent will generate an entry in the "DeferredNotification" table, and will be scheduled directly in Celery.   
```CalendarSchedule``` notifications will be verified according to the ```AHEM_CALENDAR_SCHEDULE_PERIODICITY```.   

## Backends

Ahem cames with the following default backends:

```python
AHEM_BACKENDS = (
	'ahem.backends.EmailBackend',
	'ahem.backends.MobileBackend'
)
```
### Custom backends
```
from ahem.backends import BaseBackend

class ParseBackend(BaseBackend):
	name = 'parse'
	settings = ['user_id']

	def send_notification(self, recipient, deferred_notificaion):
	    # the specific code to send the notification using your backend
	    ...
```
and overwrite ```AHEM_BACKENDS``` in your settings file:
```python
AHEM_BACKENDS = (
	'ahem.backends.EmailBackend',
	'ahem.backends.MobileBackend',
	'my.app.backends.ParseBackend'
)
```
### Registering users
To register a user in a backend do:
```python
ParseBackend.register_user(user, user_id=user.id)
```
The first param is the user to be registerd, the following kwargs will be saved as ```BackendSetting```s.
If the user is successfully registered, ```register_user``` will return ```True```. If some setting is not 
provided or something goes wrong it will return ```False```.

## Triggering notifications:

```python
AbandonedCartReachout.trigger(
	context={'id': 1, 'cart_items': [34, 23, 12]}, 
	delay=timedelta(days=0),
	backends=['email', 'mobile'])
```

The ```backends``` param specifies which backends should be triggered. If the notification does not have a template 
for the specified backend, it will not be triggered.   
If ```backends``` is not passed, notifications will be sent to all backends registered in the Notification ```backends``` variable.   
Users will only receive notifications on the backends they are registered on.  
```delay``` is an optional parameter that allows the default notification delay to be overwriten.   
