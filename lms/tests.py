from django.contrib.auth import get_user_model
from django.contrib.auth.models import Group
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase, APIClient

from lms.models import Course, Lesson, Subscription

User = get_user_model()


class LessonCRUDAndSubscriptionTests(APITestCase):
    def setUp(self):
        # пользователи
        self.user_owner = User.objects.create_user(email="owner@example.com", password="pass1234")
        self.user_other = User.objects.create_user(email="other@example.com", password="pass1234")
        self.moderator = User.objects.create_user(email="mod@example.com", password="pass1234")

        # группа модераторов
        mod_group, _ = Group.objects.get_or_create(name="moderators")
        self.moderator.groups.add(mod_group)

        # клиент
        self.client = APIClient()

        # курс
        self.client.force_authenticate(user=self.user_owner)
        self.course = Course.objects.create(title="Test Course", owner=self.user_owner)

        # урок
        self.lesson = Lesson.objects.create(
            title="Test Lesson", course=self.course, owner=self.user_owner
        )

    def test_owner_can_create_lesson(self):
        """Владелец курса может создать урок"""
        self.client.force_authenticate(user=self.user_owner)
        url = reverse("lesson-list-create")
        data = {
            "title": "New Lesson",
            "course": self.course.id,
            "video_url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_201_CREATED)
        self.assertTrue(Lesson.objects.filter(title="New Lesson").exists())
        created = Lesson.objects.get(title="New Lesson")
        self.assertEqual(created.owner, self.user_owner)

    def test_other_cannot_edit_owner_lesson(self):
        """Посторонний пользователь не может редактировать чужой урок"""
        self.client.force_authenticate(user=self.user_other)
        url = reverse("lesson-detail", kwargs={"pk": self.lesson.id})
        resp = self.client.patch(url, {"title": "Hacked"}, format="json")
        self.assertEqual(resp.status_code, status.HTTP_403_FORBIDDEN)

    def test_moderator_can_edit_but_not_delete(self):
        """Модератор может редактировать, но не удалять урок"""
        self.client.force_authenticate(user=self.moderator)
        url = reverse("lesson-detail", kwargs={"pk": self.lesson.id})

        # редактирование
        resp = self.client.patch(url, {"title": "Edited by moderator"}, format="json")
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_202_ACCEPTED))
        self.lesson.refresh_from_db()
        self.assertEqual(self.lesson.title, "Edited by moderator")

        # удаление
        resp2 = self.client.delete(url)
        self.assertIn(
            resp2.status_code,
            (status.HTTP_403_FORBIDDEN, status.HTTP_405_METHOD_NOT_ALLOWED, status.HTTP_401_UNAUTHORIZED),
        )

    def test_subscription_create_and_flag(self):
        """Подписка на курс и проверка флага is_subscribed"""
        self.client.force_authenticate(user=self.user_other)
        subscribe_url = f"/api/courses/{self.course.id}/subscribe/"
        resp = self.client.post(subscribe_url)
        self.assertIn(resp.status_code, (status.HTTP_200_OK, status.HTTP_201_CREATED))
        self.assertTrue(Subscription.objects.filter(user=self.user_other, course=self.course).exists())

        # проверка is_subscribed в деталях курса
        course_detail = self.client.get(f"/api/courses/{self.course.id}/")
        self.assertEqual(course_detail.status_code, status.HTTP_200_OK)
        self.assertTrue(course_detail.data.get("is_subscribed"))

        # отписка
        resp2 = self.client.delete(f"/api/courses/{self.course.id}/unsubscribe/")
        self.assertEqual(resp2.status_code, status.HTTP_204_NO_CONTENT)
        self.assertFalse(Subscription.objects.filter(user=self.user_other, course=self.course).exists())

    def test_video_validator_rejects_non_youtube(self):
        """Проверка валидации видео: допускаются только ссылки YouTube"""
        self.client.force_authenticate(user=self.user_owner)
        url = reverse("lesson-list-create")
        data = {
            "title": "Bad link",
            "course": self.course.id,
            "video_url": "https://some-edu.com/video/123",
        }
        resp = self.client.post(url, data, format="json")
        self.assertEqual(resp.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("video_url", resp.data)