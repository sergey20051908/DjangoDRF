from django.shortcuts import get_object_or_404
from rest_framework.filters import SearchFilter, OrderingFilter
from drf_spectacular.utils import extend_schema
from rest_framework import generics, permissions, status

# Create your views here.
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from lms.models import Course, Lesson
from .models import User, Payment
from .serializers import UserSerializer, PaymentSerializer, UserRegisterSerializer
from .service import create_stripe_product, create_stripe_price, create_checkout_session


@extend_schema(tags=["Users"])
class UserViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = User.objects.all()
    serializer_class = UserSerializer

@extend_schema(tags=["Users"])
class RegisterUserView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

@extend_schema(tags=["Payments"])
class PaymentListView(generics.ListAPIView):
    queryset = Payment.objects.all()
    serializer_class = PaymentSerializer
    filter_backends = [SearchFilter, OrderingFilter]
    filterset_fields = ["course", "lesson", "method"]
    ordering_fields = ["date"]
    search_fields = ["method"]

@extend_schema(tags=["Payments-stripe"])
class CreateStripePaymentView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Ожидает JSON: { "course": <id> } или { "lesson": <id> }
        Опционально: "currency": "usd", "success_url", "cancel_url"
        """
        user = request.user
        course_id = request.data.get("course")
        lesson_id = request.data.get("lesson")
        currency = request.data.get("currency", "usd")
        success_url = request.data.get("success_url", "http://localhost:8000/success")
        cancel_url = request.data.get("cancel_url", "http://localhost:8000/cancel")

        if not (course_id or lesson_id):
            return Response({"detail":"Нужно указать course или lesson"}, status=status.HTTP_400_BAD_REQUEST)

        if course_id:
            course = get_object_or_404(Course, pk=course_id)
            title = course.title
            description = course.description or ""
            amount_decimal = request.data.get("amount") or getattr(course, "price", None)
        else:
            lesson = get_object_or_404(Lesson, pk=lesson_id)
            title = lesson.title
            description = lesson.description or ""
            amount_decimal = request.data.get("amount") or getattr(lesson, "price", None)

        if not amount_decimal:
            return Response({"detail":"Не указана сумма (amount) и в объекте нет поля price"}, status=status.HTTP_400_BAD_REQUEST)

        # unit_amount в центах
        try:
            unit_amount_cents = int(float(amount_decimal) * 100)
        except Exception:
            return Response({"detail":"Некорректная сумма"}, status=status.HTTP_400_BAD_REQUEST)

        # 1) создаём продукт в Stripe
        product = create_stripe_product(name=title, description=description, metadata={"internal": "course_or_lesson"})

        # 2) создаём цену
        price = create_stripe_price(product_id=product["id"], unit_amount=unit_amount_cents, currency=currency)

        # 3) создаём чекаут сессию
        session = create_checkout_session(price_id=price["id"], success_url=success_url, cancel_url=cancel_url, customer_email=user.email)

        # 4) сохраняем запись Payment
        payment = Payment.objects.create(
            user=user,
            course=course if course_id else None,
            lesson=lesson if lesson_id else None,
            amount=amount_decimal,
            method="stripe",
            stripe_product_id=product["id"],
            stripe_price_id=price["id"],
            stripe_session_id=session["id"],
            checkout_url=session.get("url"),
            status="pending",
        )

        return Response({
            "checkout_url": session.get("url"),
            "session_id": session.get("id"),
            "payment_id": payment.id,
        }, status=status.HTTP_201_CREATED)
