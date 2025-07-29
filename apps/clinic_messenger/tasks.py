from celery import shared_task

from .models import SMSMessage
from .sms import send_sms


@shared_task(bind=True, name="send_sms_async")
def send_sms_async(self, message_id):
    try:
        message = SMSMessage.objects.get(id=message_id)
        result = send_sms(message.to, message.body)

        message.status = "sent" if result["success"] else "failed"
        message.response_message = str(result["response"])
        message.save()

        return f"SMS to {message.to} | status: {message.status}"

    except SMSMessage.DoesNotExist:
        return f"❌ SMSMessage with ID {message_id} not found"

    except Exception as e:
        self.retry(exc=e, countdown=10, max_retries=3)
