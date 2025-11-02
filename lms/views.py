from datetime import timedelta

from django.shortcuts import render
from django.utils import timezone
from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.permissions import IsAuthenticated
from rest_framework.exceptions import PermissionDenied
from rest_framework.response import Response

from lms.models import Course, Lesson, Subscription
from lms.serializers import CourseSerializer, LessonSerializer
from usersapp.permissions import IsModer, NotModer
from .tasks import send_course_update_emails

class CourseViewSet(viewsets.ModelViewSet):
    queryset = Course.objects.all()
    serializer_class = CourseSerializer
    parser_classes = [MultiPartParser, FormParser, JSONParser]

    def get_permissions(self):
        if self.action in ["list", "retrieve", "update", "partial_update"]:
            return [IsAuthenticated()]
        elif self.action in ["create", "destroy"]:
            return [IsAuthenticated(), NotModer()]
        return [IsAuthenticated()]

    def perform_update(self, serializer):
        course = serializer.save()
        if not course.updated_at or timezone.now() - course.updated_at > timedelta(hours=4):
            send_course_update_emails.delay(course.id)


    @action(detail=True, methods=["post"], permission_classes=[IsAuthenticated])
    def subscribe(self, request, pk=None):
        course = self.get_object()
        sub, created = Subscription.objects.get_or_create(user=request.user, course=course)
        if created:
            return Response({"message": "Вы подписались на курс."}, status=status.HTTP_201_CREATED)
        else:
            sub.delete()
            return Response({"message": "Вы отписались от курса."}, status=status.HTTP_200_OK)

    @action(detail=True, methods=["delete"], permission_classes=[IsAuthenticated])
    def unsubscribe(self, request, pk=None):
        course = self.get_object()
        deleted, _ = Subscription.objects.filter(user=request.user, course=course).delete()
        if deleted:
            return Response(status=status.HTTP_204_NO_CONTENT)
        return Response({"detail": "Подписка не найдена."}, status=status.HTTP_404_NOT_FOUND)

    def retrieve(self, request, *args, **kwargs):
        course = self.get_object()
        serializer = self.get_serializer(course)
        data = serializer.data
        data["is_subscribed"] = Subscription.objects.filter(user=request.user, course=course).exists()
        return Response(data)


class LessonListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    parser_classes = [JSONParser, FormParser, MultiPartParser]
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class LessonRetrieveUpdateDestroyAPIView(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = LessonSerializer
    queryset = Lesson.objects.all()
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    permission_classes = [IsAuthenticated]

    def get_object(self):
        obj = super().get_object()
        user = self.request.user
        is_moderator = user.groups.filter(name="moderators").exists()
        if obj.owner != user and not is_moderator:
            raise PermissionDenied("Вы не можете редактировать чужой урок.")
        return obj

    def delete(self, request, *args, **kwargs):
        user = request.user
        if user.groups.filter(name="moderators").exists():
            raise PermissionDenied("Модератор не может удалять уроки.")
        return super().delete(request, *args, **kwargs)