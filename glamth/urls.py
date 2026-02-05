from django.urls import path, include
from .views import *
from rest_framework.routers import DefaultRouter

router = DefaultRouter()
router.register(r'users', UserViewSet)
router.register(r'request-categories', RequestCategoryViewSet, basename='request-category')
router.register(r'work-progress', WorkProgressUpdateViewSet, basename='work-progress')
router.register(r'gate-passes', GatePassViewSet, basename='gate-pass')
router.register(r'work-claims', WorkClaimViewSet, basename='work-claim')
router.register(r'reminders', ReminderThreadViewSet, basename='reminders')

urlpatterns = [
    path('', include(router.urls)),          # ✅ USERS API WORKS HERE
    path('login/', LoginAPIView.as_view(), name='login'),   # ✅ LOGIN API
    path('dashboard-counts/', DashboardCountAPIView.as_view(), name='dashboard-counts'),
    path('threads/<int:thread_id>/full-detail/', FullThreadDetailAPIView.as_view()),
    path('threads/create/', WorkThreadCreateAPIView.as_view(), name='create-thread'),
    path(
        'threads/<int:thread_id>/approve-reject/',
        WorkThreadApprovalAPIView.as_view(),
        name='thread-approve-reject'
    ),
    path('threads/send-message/', SendThreadMessageAPIView.as_view(), name='send-thread-message'),
    path('auth/me/', MeAPIView.as_view(), name='me'),
    path("threads/<int:pk>/mark-completed/", MarkWorkThreadCompletedAPIView.as_view()),
    path("save-subscription/", SaveSubscriptionAPIView.as_view(), name="save_subscription"),
    path("delete-subscription/", DeleteSubscriptionAPIView.as_view(), name="delete_subscription"),
    


]
