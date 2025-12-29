from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin

from .models import *

# =====================================================
# ✅ CUSTOM USER ADMIN
# =====================================================

class UserAdmin(BaseUserAdmin):
    model = User

    list_display = (
        "email",
        "full_name",
        "employee_id",
        "role",
        "is_staff",
        "is_superuser",
        "is_active",
    )

    list_filter = ("role", "is_staff", "is_superuser", "is_active")
    search_fields = ("email", "full_name", "employee_id")
    ordering = ("email",)

    fieldsets = (
        ("Login Credentials", {
            "fields": ("email", "password")
        }),
        ("Personal Info", {
            "fields": ("full_name", "phone", "employee_id", "department", "designation")
        }),
        ("Permissions", {
            "fields": (
                "role",
                "is_staff",
                "is_superuser",
                "is_active",
                "groups",
                "user_permissions"
            )
        }),
        ("Important Dates", {
            "fields": ("last_login", "date_joined")
        }),
    )

    add_fieldsets = (
        (None, {
            "classes": ("wide",),
            "fields": (
                "email",
                "employee_id",
                "full_name",
                "phone",
                "department",
                "designation",
                "role",
                "password1",
                "password2",
                "is_staff",
                "is_superuser",
                "is_active",
            ),
        }),
    )

    readonly_fields = ("date_joined", "last_login")


admin.site.register(User, UserAdmin)


# =====================================================
# ✅ REQUEST CATEGORY ADMIN
# =====================================================

@admin.register(RequestCategory)
class RequestCategoryAdmin(admin.ModelAdmin):
    list_display = ("id", "name", "created_at")
    search_fields = ("name",)
    ordering = ("-created_at",)


# =====================================================
# ✅ INLINE WORK PROGRESS
# =====================================================

class WorkProgressInline(admin.TabularInline):
    model = WorkProgressUpdate
    extra = 0


# =====================================================
# ✅ INLINE THREAD MESSAGES
# =====================================================

class ThreadMessageInline(admin.TabularInline):
    model = ThreadMessage
    extra = 0
    readonly_fields = (
        "sender",
        "receiver",
        "message_type",
        "text_message",
        "created_at"
    )


# =====================================================
# ✅ WORK THREAD ADMIN
# =====================================================

@admin.register(WorkThread)
class WorkThreadAdmin(admin.ModelAdmin):
    list_display = (
        "thread_number",
        "title",
        "status",
        "approval_status",
        "created_by",
        "created_at",
    )

    list_filter = (
        "status",
        "approval_status",
        "vehicle_type",
        "created_at",
    )

    search_fields = (
        "thread_number",
        "title",
        "vehicle_number",
        "created_by__email",
    )

    readonly_fields = ("thread_number", "created_at", "updated_at")

    inlines = [WorkProgressInline, ThreadMessageInline]

    ordering = ("-created_at",)


# =====================================================
# ✅ WORK PROGRESS ADMIN
# =====================================================

@admin.register(WorkProgressUpdate)
class WorkProgressUpdateAdmin(admin.ModelAdmin):
    list_display = (
        "thread",
        "progress_type",
        "expected_end_date",
        "updated_by",
        "created_at",
    )

    list_filter = ("progress_type",)
    search_fields = ("thread__title",)
    ordering = ("-created_at",)


# =====================================================
# ✅ THREAD MESSAGE ADMIN
# =====================================================

@admin.register(ThreadMessage)
class ThreadMessageAdmin(admin.ModelAdmin):
    list_display = (
        "thread",
        "sender",
        "receiver",
        "message_type",
        "created_at",
    )

    list_filter = ("message_type", "created_at")
    search_fields = ("thread__title", "sender__email", "receiver__email")
    ordering = ("-created_at",)


# =====================================================
# ✅ GATE PASS ADMIN ✅✅✅
# =====================================================

@admin.register(GatePass)
class GatePassAdmin(admin.ModelAdmin):
    list_display = (
        "thread",
        "issued_to",
        "vehicle_number",
        "pass_mode",
        "status",
        "valid_from",
        "valid_to",
        "approved_by",
    )

    list_filter = (
        "status",
        "pass_mode",
        "valid_from",
    )

    search_fields = (
        "thread__thread_number",
        "issued_to__email",
        "vehicle_number",
    )

    readonly_fields = (
        "out_time",
        "in_time",
        "created_at",
        "approved_at",
    )

    ordering = ("-created_at",)


# =====================================================
# ✅ WORK CLAIM ADMIN ✅✅✅
# =====================================================

@admin.register(WorkClaim)
class WorkClaimAdmin(admin.ModelAdmin):
    list_display = (
        "thread",
        "claim_amount",
        "payment_status",
        "work_done",
        "approved_at",
        "paid_at",
        "created_at",
    )

    list_filter = (
        "payment_status",
        "work_done",
        "created_at",
    )

    search_fields = (
        "thread__thread_number",
        "approval_id",
    )

    readonly_fields = (
        "approved_at",
        "paid_at",
        "created_at",
    )

    ordering = ("-created_at",)




@admin.register(PushSubscription)
class PushSubscriptionAdmin(admin.ModelAdmin):
    list_display = ("user", "endpoint_short", "created_at", "last_seen")
    list_filter = ("created_at", "last_seen")
    search_fields = ("user__username", "endpoint", "p256dh", "auth")
    ordering = ("-created_at",)

    def endpoint_short(self, obj):
        return obj.endpoint[:50] + "..." if len(obj.endpoint) > 50 else obj.endpoint
    endpoint_short.short_description = "Endpoint"





@admin.register(ReminderThread)
class ReminderThreadAdmin(admin.ModelAdmin):
    list_display = ('id', 'work_thread', 'reminder_at', 'created_by', 'created_at')
    list_filter = ('reminder_at', 'created_by')
    search_fields = ('work_thread__thread_number', 'message', 'created_by__username')
    ordering = ('-reminder_at',)
                



