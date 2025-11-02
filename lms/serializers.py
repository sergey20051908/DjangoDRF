from rest_framework import serializers

from lms.models import Lesson, Course, Subscription
from lms.validators import validate_video_url


class LessonSerializer(serializers.ModelSerializer):
    video_url = serializers.URLField(required=False, allow_blank=True, validators=[validate_video_url])

    class Meta:
        model = Lesson
        fields = ('id', 'course', 'title', 'description', 'preview', 'video_url')
        read_only_fields = ('id',)

class CourseSerializer(serializers.ModelSerializer):
    lessons = LessonSerializer(many=True, read_only=True)
    lessons_count = serializers.SerializerMethodField()
    is_subscribed = serializers.SerializerMethodField()

    def get_lessons_count(self, obj):
        return obj.lessons.count()

    def get_is_subscribed(self, obj):
        request = self.context.get("request", None)
        if request is None or request.user.is_anonymous:
            return False
        return Subscription.objects.filter(user=request.user, course=obj).exists()


    class Meta:
        model = Course
        fields = ('id', 'title', 'preview', 'description', 'lessons', 'lessons_count', 'is_subscribed')
        read_only_fields = ('id',)

