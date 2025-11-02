from django.core.management import BaseCommand

from lms.models import Course, Lesson
from usersapp.models import Payment, User


class Command(BaseCommand):
    help = 'Создание тестовых платежей'

    def handle(self, *args, **kwargs):
        user = User.objects.first()
        course = Course.objects.first()
        lesson = Lesson.objects.first()
        Payment.objects.create(
            user = user,
            course = course,
            amount = 2000,
            method = Payment.TRANSFER
        )
        Payment.objects.create(
            user=user,
            lesson=lesson,
            amount=150,
            method=Payment.CASH
        )
        self.stdout.write(self.style.SUCCESS("Тестовые платежи созданы"))