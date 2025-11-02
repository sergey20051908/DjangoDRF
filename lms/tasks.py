from celery import shared_task
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from .models import Subscription, Course

User = get_user_model()

@shared_task
def send_course_update_emails(course_id):
    course = Course.objects.get(id=course_id)
    subs = Subscription.objects.filter(course=course)
    for sub in subs:
        send_mail(
            subject=f'Обновление курса: {course.title}',
            message=f'Курс "{course.title}" был обновлён. Проверьте новые материалы!',
            from_email='admin@example.com',
            recipient_list=[sub.user.email],
            fail_silently=True,
        )
        print('Письмо отправлено!')