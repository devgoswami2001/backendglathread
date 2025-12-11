from django.conf import settings
from django.contrib.auth import get_user_model
from django.db.models import Q, OuterRef, Subquery
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
import json
from rest_framework import status, permissions
from rest_framework.decorators import action
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.viewsets import ModelViewSet
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from rest_framework_simplejwt.tokens import RefreshToken

from pywebpush import webpush, WebPushException

from .models import WorkThread
from .serializers import *


User = get_user_model()

class LoginAPIView(APIView):
    def post(self, request):
        serializer = LoginSerializer(data=request.data)

        if serializer.is_valid():
            user = serializer.validated_data['user']

            refresh = RefreshToken.for_user(user)

            return Response({
                "message": "Login successful",
                "access": str(refresh.access_token),
                "refresh": str(refresh),
                "user": {
                    "id": user.id,
                    "full_name": user.full_name,
                    "email": user.email,
                    "phone": user.phone,
                    "employee_id": user.employee_id,
                    "department": user.department,
                    "designation": user.designation,
                    "role": user.role,
                }
            }, status=status.HTTP_200_OK)

        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class UserViewSet(ModelViewSet):
    queryset = User.objects.all().order_by("-id")
    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated, IsAdminUser]




class DashboardCountAPIView(APIView):
    def get(self, request):
        today = timezone.now().date()

        # ✅ =========================
        # ✅ BASIC STATUS COUNTS
        # ✅ =========================

        total_requests = WorkThread.objects.count()

        pending = WorkThread.objects.filter(
            status='pending',
            approval_status='pending'
        ).count()

        working = WorkThread.objects.filter(status='working').count()

        work_completed = WorkThread.objects.filter(status='completed').count()

        payment_pending = WorkThread.objects.filter(status='payment_pending').count()

        payment_done = WorkThread.objects.filter(status='payment_completed').count()

        rejected = WorkThread.objects.filter(approval_status='rejected').count()

        # ✅ =========================
        # ✅ LATEST DUE DATE SUBQUERY
        # ✅ =========================

        latest_due_date = WorkProgressUpdate.objects.filter(
            thread=OuterRef('pk')
        ).order_by('-created_at').values('expected_end_date')[:1]

        # ✅ =========================
        # ✅ OVERDUE (LATEST DUE < TODAY)
        # ✅ =========================

        overdue = WorkThread.objects.annotate(
            latest_due=Subquery(latest_due_date)
        ).filter(
            latest_due__lt=today
        ).exclude(
            status__in=['completed', 'payment_completed', 'workcompleted']
        ).count()

        # ✅ =========================
        # ✅ TODAY'S PENDENCY (DUE TODAY)
        # ✅ =========================

        todays_pendency_qs = WorkThread.objects.annotate(
            latest_due=Subquery(latest_due_date)
        ).filter(
            latest_due=today
        )

        # ✅ =========================
        # ✅ TODAY'S WORK (CREATED TODAY - ANY STATUS)
        # ✅ =========================

        todays_work_qs = WorkThread.objects.filter(
            created_at__date=today
        )

        # ✅ =========================
        # ✅ COUNTS
        # ✅ =========================

        todays_pendency_count = todays_pendency_qs.count()
        todays_work_count = todays_work_qs.count()

        # ✅ =========================
        # ✅ SERIALIZED THREAD DATA
        # ✅ =========================

        todays_pendency_data = TodayThreadListSerializer(
            todays_pendency_qs, many=True
        ).data

        todays_work_data = TodayThreadListSerializer(
            todays_work_qs, many=True
        ).data

        # ✅ =========================
        # ✅ FINAL DASHBOARD RESPONSE
        # ✅ =========================

        data = {
            "total_requests": total_requests,
            "pending": pending,
            "working": working,
            "work_completed": work_completed,
            "payment_pending": payment_pending,
            "payment_done": payment_done,
            "rejected": rejected,
            "overdue": overdue,

            "todays_pendency": {
                "count": todays_pendency_count,
                "threads": todays_pendency_data
            },

            "todays_work": {
                "count": todays_work_count,
                "threads": todays_work_data
            }
        }

        return Response(data)   





class FullThreadDetailAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request, thread_id):
        try:
            thread = WorkThread.objects.select_related(
                'created_by',
                'approved_by',
                'request_category'
            ).prefetch_related(
                'assigned_to',
                'progress_updates',
                'messages',
                'gate_passes',   # ✅ NEW
                'claims'         # ✅ NEW
            ).get(id=thread_id)

        except WorkThread.DoesNotExist:
            return Response(
                {"error": "Thread not found"},
                status=status.HTTP_404_NOT_FOUND
            )

        serializer = WorkThreadFullDetailSerializer(thread)

        return Response({
            "success": True,
            "thread": serializer.data
        }, status=status.HTTP_200_OK)


class WorkThreadCreateAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser]

    def post(self, request):
        serializer = WorkThreadCreateSerializer(
            data=request.data,
            context={'request': request}
        )

        if serializer.is_valid():
            thread = serializer.save()
            return Response(
                {
                    "success": True,
                    "message": "Thread created successfully",
                    "thread_id": thread.id,
                    "thread_number": thread.thread_number
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )




class RequestCategoryViewSet(ModelViewSet):
    queryset = RequestCategory.objects.all().order_by('-created_at')
    serializer_class = RequestCategorySerializer
    permission_classes = [IsAuthenticated]




class WorkThreadApprovalAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def patch(self, request, thread_id):
        thread = get_object_or_404(WorkThread, id=thread_id)

        serializer = WorkThreadApprovalSerializer(
            thread,
            data=request.data,
            partial=True,
            context={'request': request}
        )

        if serializer.is_valid():
            serializer.save()
            return Response(
                {
                    "success": True,
                    "message": f"Thread {serializer.data.get('approval_status')} successfully"
                },
                status=status.HTTP_200_OK
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )



class WorkProgressUpdateViewSet(ModelViewSet):
    queryset = WorkProgressUpdate.objects.select_related(
        'thread', 'updated_by'
    ).order_by('-created_at')

    serializer_class = WorkProgressUpdateSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(updated_by=self.request.user)



class SendThreadMessageAPIView(APIView):
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser,JSONParser]

    def post(self, request):
        serializer = ThreadMessageCreateSerializer(data=request.data)

        if serializer.is_valid():
            message = serializer.save(sender=request.user)

            return Response(
                {
                    "success": True,
                    "message": "Message sent successfully",
                    "data": {
                        "id": message.id,
                        "thread": message.thread.id,
                        "sender": message.sender.id,
                        "receiver": message.receiver.id if message.receiver else None,
                        "message_type": message.message_type,
                        "text_message": message.text_message,
                        "media_file": message.media_file.url if message.media_file else None,
                        "created_at": message.created_at
                    }
                },
                status=status.HTTP_201_CREATED
            )

        return Response(
            {
                "success": False,
                "errors": serializer.errors
            },
            status=status.HTTP_400_BAD_REQUEST
        )
    


class MeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = LoggedInUserSerializer(request.user)

        return Response(
            {
                "success": True,
                "user": serializer.data
            },
            status=status.HTTP_200_OK
        )


class GatePassViewSet(ModelViewSet):
    queryset = GatePass.objects.all().order_by('-created_at')
    serializer_class = GatePassSerializer
    permission_classes = [IsAuthenticated]

    # --------------------------------------------------
    # ✅ CREATE = AUTO OUT
    # --------------------------------------------------
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        gate_pass = serializer.save(
            status='out',          # ✅ Direct OUT
            pass_mode='out',
            out_time=timezone.now()
        )

        return Response(
            {
                "success": True,
                "message": "Gate Pass created and marked as OUT",
                "data": GatePassSerializer(gate_pass).data
            },
            status=status.HTTP_201_CREATED
        )

    # --------------------------------------------------
    # ✅ MARK IN (only return)
    # --------------------------------------------------
    @action(detail=True, methods=['patch'], url_path='mark-in')
    def mark_in(self, request, pk=None):
        gate_pass = get_object_or_404(GatePass, pk=pk)

        if gate_pass.status != 'out':
            return Response(
                {"error": "Gate pass must be in OUT state first"},
                status=status.HTTP_400_BAD_REQUEST
            )

        gate_pass.mark_in()

        return Response(
            {"success": True, "message": "Marked as IN"},
            status=status.HTTP_200_OK
        )


class WorkClaimViewSet(ModelViewSet):
    queryset = WorkClaim.objects.all().order_by('-created_at')
    serializer_class = WorkClaimSerializer
    permission_classes = [IsAuthenticated]
    parser_classes = [MultiPartParser, FormParser, JSONParser]





class MarkWorkThreadCompletedAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def patch(self, request, pk):
        thread = get_object_or_404(WorkThread, pk=pk)

        serializer = WorkThreadCompleteSerializer(thread, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            "success": True,
            "message": "Work thread marked as completed successfully.",
            "data": serializer.data
        }, status=status.HTTP_200_OK)







from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, permissions
from django.utils import timezone
from .serializers import PushSubscriptionSerializer
from .models import PushSubscription

class SaveSubscriptionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]  # require login

    def post(self, request):
        data = request.data
        endpoint = data.get("endpoint")
        if not endpoint:
            return Response({"detail":"endpoint required"}, status=status.HTTP_400_BAD_REQUEST)

        obj, created = PushSubscription.objects.update_or_create(
            endpoint=endpoint,
            defaults=dict(
                user=request.user,
                p256dh=data["keys"]["p256dh"],
                auth=data["keys"]["auth"],
                last_seen=timezone.now(),
            )
        )
        return Response(PushSubscriptionSerializer(obj).data, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

class DeleteSubscriptionAPIView(APIView):
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request):
        endpoint = request.data.get("endpoint")
        if not endpoint:
            return Response({"detail":"endpoint required"}, status=status.HTTP_400_BAD_REQUEST)
        PushSubscription.objects.filter(user=request.user, endpoint=endpoint).delete()
        return Response({"success": True})






