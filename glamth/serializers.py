from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import User
from .models import *
from django.utils import timezone

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        email = data.get('email')
        password = data.get('password')

        user = authenticate(email=email, password=password)

        if not user:
            raise serializers.ValidationError("Invalid email or password")

        if not user.is_active:
            raise serializers.ValidationError("User account is disabled")

        data['user'] = user
        return data



class UserSerializer(serializers.ModelSerializer):
    password = serializers.CharField(
        write_only=True,
        required=False,
        min_length=8
    )

    class Meta:
        model = User
        fields = [
            "id",
            "full_name",
            "email",
            "phone",
            "employee_id",
            "department",
            "designation",
            "role",
            "password",
            "is_active",
            "is_staff",
            "date_joined",
        ]
        read_only_fields = ["id", "date_joined"]

    # ✅ CREATE USER (POST)
    def create(self, validated_data):
        password = validated_data.pop("password", None)
        user = User(**validated_data)

        if password:
            user.set_password(password)
        else:
            user.set_unusable_password()

        user.save()
        return user

    # ✅ UPDATE USER (PUT/PATCH)
    def update(self, instance, validated_data):
        password = validated_data.pop("password", None)

        for attr, value in validated_data.items():
            setattr(instance, attr, value)

        if password:
            instance.set_password(password)

        instance.save()
        return instance
    


class DashboardCountSerializer(serializers.Serializer):
    total_requests = serializers.IntegerField()
    pending = serializers.IntegerField()
    working = serializers.IntegerField()
    work_completed = serializers.IntegerField()
    payment_pending = serializers.IntegerField()
    payment_done = serializers.IntegerField()
    rejected = serializers.IntegerField()
    overdue = serializers.IntegerField()
    todays_pendency = serializers.IntegerField()
    todays_work = serializers.IntegerField()


class TodayThreadListSerializer(serializers.ModelSerializer):
    thread_number = serializers.IntegerField(source='id')
    created_by_name = serializers.CharField(source='created_by.full_name')
    due_date = serializers.SerializerMethodField()

    class Meta:
        model = WorkThread
        fields = [
            'thread_number',
            'title',
            'created_by_name',
            'status',
            'due_date',
            'description',
        ]

    def get_due_date(self, obj):
        last_update = obj.progress_updates.order_by('-created_at').first()
        return last_update.expected_end_date if last_update else None
    


class ThreadMessageSerializer(serializers.ModelSerializer):
    sender_name = serializers.CharField(source='sender.full_name', read_only=True)
    receiver_name = serializers.CharField(source='receiver.full_name', read_only=True)

    class Meta:
        model = ThreadMessage
        fields = [
            'id',
            'sender',
            'sender_name',
            'receiver',
            'receiver_name',
            'message_type',
            'text_message',
            'media_file',
            'created_at',
        ]


class WorkProgressUpdateSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)

    class Meta:
        model = WorkProgressUpdate
        fields = [
            'id',
            'progress_type',
            'expected_end_date',
            'delay_reason',
            'updated_by',
            'updated_by_name',
            'created_at',
        ]



# class WorkThreadFullDetailSerializer(serializers.ModelSerializer):
#     created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

#     assigned_to_details = serializers.SerializerMethodField()
#     progress_updates = WorkProgressUpdateSerializer(many=True, read_only=True)
#     messages = ThreadMessageSerializer(many=True, read_only=True)

#     request_category_name = serializers.CharField(
#         source='request_category.name',
#         read_only=True
#     )

#     approved_by_name = serializers.CharField(
#         source='approved_by.full_name',
#         read_only=True
#     )

#     class Meta:
#         model = WorkThread
#         fields = [
#             'id',
#             'thread_number',
#             'title',
#             'description',

#             'request_category',
#             'request_category_name',

#             'vehicle_number',
#             'vehicle_type',

#             'document_1_name',
#             'document_1_file',
#             'document_2_name',
#             'document_2_file',
#             'document_3_name',
#             'document_3_file',
#             'document_4_name',
#             'document_4_file',

#             'created_by',
#             'created_by_name',

#             'assigned_to_details',

#             'status',
#             'approval_status',

#             'approved_by',
#             'approved_by_name',

#             'approval_remark',
#             'approval_at',

#             'created_at',
#             'updated_at',

#             # ✅ FULL HISTORY
#             'progress_updates',
#             'messages',
#         ]

#     def get_assigned_to_details(self, obj):
#         return [
#             {
#                 "id": user.id,
#                 "name": user.full_name,
#                 "email": user.email
#             }
#             for user in obj.assigned_to.all()
#         ]



class WorkThreadCreateSerializer(serializers.ModelSerializer):

    assigned_to = serializers.PrimaryKeyRelatedField(
        queryset=User.objects.all(),
        many=True,
        required=False,
        write_only=True
    )

    request_category = serializers.PrimaryKeyRelatedField(
        queryset=RequestCategory.objects.all(),
        required=False,
        allow_null=True
    )

    class Meta:
        model = WorkThread
        fields = [
            'id',
            'request_category',
            'title',
            'description',

            'vehicle_number',
            'vehicle_type',

            'document_1_name',
            'document_1_file',
            'document_2_name',
            'document_2_file',
            'document_3_name',
            'document_3_file',
            'document_4_name',
            'document_4_file',

            'assigned_to',
        ]

    def create(self, validated_data):
        assigned_users = validated_data.pop('assigned_to', [])
        request = self.context['request']

        thread = WorkThread.objects.create(
            created_by=request.user,
            **validated_data
        )

        if assigned_users:
            thread.assigned_to.set(assigned_users)

        return thread


class RequestCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = RequestCategory
        fields = [
            'id',
            'name',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']




class WorkThreadApprovalSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkThread
        fields = [
            'approval_status'
        ]

    def validate_approval_status(self, value):
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError(
                "Approval status must be either 'approved' or 'rejected'."
            )
        return value

    def update(self, instance, validated_data):
        request = self.context['request']

        instance.approval_status = validated_data.get(
            'approval_status', instance.approval_status
        )

        instance.approved_by = request.user
        instance.approval_at = timezone.now()

        # ✅ Auto main status update
        if instance.approval_status == 'approved':
            instance.status = 'working'
        elif instance.approval_status == 'rejected':
            instance.status = 'completed'

        instance.save()
        return instance



class WorkProgressUpdateSerializer(serializers.ModelSerializer):
    updated_by_name = serializers.CharField(source='updated_by.full_name', read_only=True)
    thread_title = serializers.CharField(source='thread.title', read_only=True)

    class Meta:
        model = WorkProgressUpdate
        fields = [
            'id',
            'thread',
            'thread_title',

            'updated_by',
            'updated_by_name',

            'progress_type',
            'expected_end_date',
            'delay_reason',

            'created_at',
        ]
        read_only_fields = ['id', 'updated_by', 'created_at']

    def validate(self, data):
        # ✅ delay_reason mandatory only when progress_type = delay
        if data.get('progress_type') == 'delay' and not data.get('delay_reason'):
            raise serializers.ValidationError({
                "delay_reason": "This field is required when progress type is 'delay'."
            })
        return data




class ThreadMessageCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = ThreadMessage
        fields = [
            'id',
            'thread',
            'receiver',
            'message_type',
            'text_message',
            'media_file',
            'created_at',
        ]
        read_only_fields = ['id', 'created_at']

    def validate(self, data):
        msg_type = data.get('message_type')

        if msg_type == 'text' and not data.get('text_message'):
            raise serializers.ValidationError({
                "text_message": "Text message is required for text type."
            })

        if msg_type in ['image', 'video', 'audio', 'document'] and not data.get('media_file'):
            raise serializers.ValidationError({
                "media_file": "Media file is required for this message type."
            })

        return data


class LoggedInUserSerializer(serializers.ModelSerializer):
    role_display = serializers.CharField(source='get_role_display', read_only=True)

    class Meta:
        model = User
        fields = [
            'id',
            'full_name',
            'email',
            'phone',
            'employee_id',
            'department',
            'designation',
            'role',
            'role_display',
            'is_active',
            'is_staff',
            'date_joined',
        ]



class GatePassSerializer(serializers.ModelSerializer):

    class Meta:
        model = GatePass
        fields = [
            'id',
            'thread',
            'issued_to',
            'vehicle_number',
            'purpose',
            'valid_from',
            'valid_to',
            'status',
            'pass_mode',
            'out_time',
            'in_time',
            'created_at',
        ]
        read_only_fields = [
            'status',
            'pass_mode',
            'out_time',
            'in_time',
            'created_at',
        ]


# ✅ APPROVE / REJECT SERIALIZER
class GatePassApprovalSerializer(serializers.ModelSerializer):

    class Meta:
        model = GatePass
        fields = ['status', 'rejection_reason']

    def validate_status(self, value):
        if value not in ['approved', 'rejected']:
            raise serializers.ValidationError("Status must be approved or rejected.")
        return value

    def update(self, instance, validated_data):
        request = self.context['request']

        instance.status = validated_data['status']
        instance.rejection_reason = validated_data.get('rejection_reason', None)
        instance.approved_by = request.user
        instance.approved_at = timezone.now()
        instance.save()
        return instance


class WorkClaimSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkClaim
        fields = [
            'id',
            'thread',
            'claim_amount',
            'bill_document',
            'work_done',
            'approval_id',
            'approval_image',
            'payment_status',
            'approved_at',
            'paid_at',
            'created_at',
        ]
        read_only_fields = [
            'approved_at',
            'paid_at',
            'created_at',
        ]


class GatePassDetailSerializer(serializers.ModelSerializer):
    issued_to_name = serializers.CharField(source='issued_to.full_name', read_only=True)
    approved_by_name = serializers.CharField(source='approved_by.full_name', read_only=True)

    class Meta:
        model = GatePass
        fields = [
            'id',
            'issued_to',
            'issued_to_name',
            'vehicle_number',
            'pass_mode',
            'purpose',
            'valid_from',
            'valid_to',
            'status',
            'approved_by',
            'approved_by_name',
            'approved_at',
            'rejection_reason',
            'out_time',
            'in_time',
            'created_at',
        ]
class WorkClaimDetailSerializer(serializers.ModelSerializer):

    class Meta:
        model = WorkClaim
        fields = [
            'id',
            'claim_amount',
            'bill_document',
            'work_done',
            'approval_id',
            'approval_image',
            'payment_status',
            'approved_at',
            'paid_at',
            'created_at',
        ]



class WorkThreadFullDetailSerializer(serializers.ModelSerializer):

    created_by_name = serializers.CharField(source='created_by.full_name', read_only=True)

    assigned_to_details = serializers.SerializerMethodField()
    progress_updates = WorkProgressUpdateSerializer(many=True, read_only=True)
    messages = ThreadMessageSerializer(many=True, read_only=True)

    # ✅ NEW
    gate_passes = GatePassDetailSerializer(many=True, read_only=True)
    claims = WorkClaimDetailSerializer(many=True, read_only=True)

    request_category_name = serializers.CharField(
        source='request_category.name',
        read_only=True
    )

    approved_by_name = serializers.CharField(
        source='approved_by.full_name',
        read_only=True
    )

    class Meta:
        model = WorkThread
        fields = [
            'id',
            'thread_number',
            'title',
            'description',

            'request_category',
            'request_category_name',

            'vehicle_number',
            'vehicle_type',

            'document_1_name',
            'document_1_file',
            'document_2_name',
            'document_2_file',
            'document_3_name',
            'document_3_file',
            'document_4_name',
            'document_4_file',

            'created_by',
            'created_by_name',

            'assigned_to_details',

            'status',
            'approval_status',

            'approved_by',
            'approved_by_name',

            'approval_remark',
            'approval_at',

            'created_at',
            'updated_at',

            # ✅ FULL HISTORY
            'progress_updates',
            'messages',

            # ✅ NEW ADDITIONS
            'gate_passes',
            'claims',
        ]

    def get_assigned_to_details(self, obj):
        return [
            {
                "id": user.id,
                "name": user.full_name,
                "email": user.email
            }
            for user in obj.assigned_to.all()
        ]




class WorkThreadCompleteSerializer(serializers.ModelSerializer):
    class Meta:
        model = WorkThread
        fields = ["id", "thread_number", "status"]
        read_only_fields = ["id", "thread_number"]

    def update(self, instance, validated_data):
        instance.status = "completed"
        instance.save()
        return instance





class PushSubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = PushSubscription
        fields = ("id","endpoint","p256dh","auth")


