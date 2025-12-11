from django.db import models
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager, PermissionsMixin
import random
from django.utils import timezone
# ✅ Custom User Manager

# ✅ Custom User Manager (FIXED)
class CustomUserManager(BaseUserManager):

    def create_user(self, email, employee_id, password=None, **extra_fields):
        if not email:
            raise ValueError("Email is required")
        if not employee_id:
            raise ValueError("Employee ID is required")

        email = self.normalize_email(email)
        user = self.model(email=email, employee_id=employee_id, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, employee_id, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True')

        return self.create_user(email, employee_id, password, **extra_fields)


# ✅ ✅ ✅ MAIN USER MODEL (ADMIN SAFE)
class User(AbstractBaseUser, PermissionsMixin):

    ROLE_CHOICES = (
        (1, 'CFO'),
        (2, 'Registrar'),
        (3, 'Administrator'),
        (4, 'HOD'),
        (5, 'Supervisor'),
        (6, 'Employee'),
    )

    full_name = models.CharField(max_length=100)
    email = models.EmailField(unique=True)

    # ✅ ✅ FIXED: phone now allows NULL to avoid crash
    phone = models.CharField(max_length=15, unique=True, null=True, blank=True)

    employee_id = models.CharField(max_length=20, unique=True)

    # ✅ ✅ FIXED: optional for superuser
    department = models.CharField(max_length=100, null=True, blank=True)
    designation = models.CharField(max_length=100, null=True, blank=True)

    role = models.PositiveSmallIntegerField(choices=ROLE_CHOICES, default=4)

    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)

    date_joined = models.DateTimeField(auto_now_add=True)

    objects = CustomUserManager()

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['employee_id', 'full_name']

    def __str__(self):
        return f"{self.full_name} - {self.employee_id}"




class RequestCategory(models.Model):
    name = models.CharField(max_length=100, unique=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name



class WorkThread(models.Model):

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('working', 'Working'),
        ('workcompleted', 'Work Completed'),
        ('payment_pending', 'Payment Pending'),
        ('payment_completed', 'Payment Completed'),
        ('completed', 'Completed'),
        ('delayed', 'Delayed'),
    )

    APPROVAL_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
    )

    VEHICLE_TYPE_CHOICES = (
        ('bus', 'Bus'),
        ('car', 'Car'),
        ('golf_cart', 'Golf Cart'),
        ('e_rickshaw', 'E-Rickshaw'),
        ('ambulance', 'Ambulance'),
        ('other', 'Other Vehicle'),
    )

    # ✅ ✅ UNIQUE GTX + 6 DIGIT THREAD NUMBER
    thread_number = models.CharField(
        max_length=10,   # "GTX" + 6 digits = 9, keep buffer
        unique=True,
        editable=False,
        null=True,
        blank=True,
    )

    request_category = models.ForeignKey(
        RequestCategory,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='threads'
    )

    title = models.CharField(max_length=255)
    description = models.TextField()

    vehicle_number = models.CharField(max_length=20, blank=True, null=True)
    vehicle_type = models.CharField(
        max_length=20,
        choices=VEHICLE_TYPE_CHOICES,
        blank=True,
        null=True
    )

    document_1_name = models.CharField(max_length=100, blank=True, null=True)
    document_1_file = models.FileField(upload_to='documents/', blank=True, null=True)

    document_2_name = models.CharField(max_length=100, blank=True, null=True)
    document_2_file = models.FileField(upload_to='documents/', blank=True, null=True)

    document_3_name = models.CharField(max_length=100, blank=True, null=True)
    document_3_file = models.FileField(upload_to='documents/', blank=True, null=True)

    document_4_name = models.CharField(max_length=100, blank=True, null=True)
    document_4_file = models.FileField(upload_to='documents/', blank=True, null=True)

    created_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='created_threads'
    )

    assigned_to = models.ManyToManyField(
        User,
        related_name='assigned_threads',
        blank=True
    )

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    approval_status = models.CharField(
        max_length=20,
        choices=APPROVAL_STATUS_CHOICES,
        default='pending'
    )

    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_threads'
    )

    approval_remark = models.TextField(blank=True, null=True)
    approval_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # ✅ ✅ AUTO-GENERATE GTX + 6 DIGIT UNIQUE NUMBER
    def save(self, *args, **kwargs):
        if not self.thread_number:
            while True:
                number = f"TH{random.randint(100000, 999999)}"
                if not WorkThread.objects.filter(thread_number=number).exists():
                    self.thread_number = number
                    break
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.thread_number} | {self.title} | {self.get_status_display()}"

# =====================================================
# ✅ WORK PROGRESS / DATE / DELAY HISTORY
# =====================================================

class WorkProgressUpdate(models.Model):

    PROGRESS_TYPE_CHOICES = (
        ('initial', 'Initial Estimate'),
        ('delay', 'Delay Update'),
        ('completed', 'Completion Update'),
    )

    thread = models.ForeignKey(
        WorkThread,
        on_delete=models.CASCADE,
        related_name='progress_updates'
    )

    updated_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='progress_updates'
    )

    progress_type = models.CharField(
        max_length=20,
        choices=PROGRESS_TYPE_CHOICES
    )

    expected_end_date = models.DateField()

    delay_reason = models.TextField(
        blank=True,
        null=True,
        help_text="Required only if progress_type is delay"
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.thread.title} | {self.progress_type} | {self.expected_end_date}"


# =====================================================
# ✅ THREAD CHAT (WHATSAPP STYLE)
# =====================================================

class ThreadMessage(models.Model):

    MESSAGE_TYPE_CHOICES = (
        ('text', 'Text'),
        ('image', 'Image'),
        ('video', 'Video'),
        ('audio', 'Audio'),
        ('document', 'Document'),
        ('system', 'System'),
    )

    thread = models.ForeignKey(
        WorkThread,
        on_delete=models.CASCADE,
        related_name='messages'
    )

    sender = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='sent_messages'
    )

    receiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='received_private_messages'
    )

    message_type = models.CharField(
        max_length=20,
        choices=MESSAGE_TYPE_CHOICES,
        default='text'
    )

    text_message = models.TextField(blank=True, null=True)

    media_file = models.FileField(
        upload_to='thread_messages/',
        blank=True,
        null=True
    )

    seen_by = models.ManyToManyField(
        User,
        blank=True,
        related_name='seen_messages'
    )

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        if self.receiver:
            return f"Private: {self.sender.full_name} → {self.receiver.full_name}"
        return f"Group: {self.sender.full_name} in {self.thread.title}"
    
# =====================================================
# ✅ GATE PASS MANAGEMENT (OUT → IN SYSTEM)
# =====================================================

class GatePass(models.Model):

    PASS_MODE_CHOICES = (
        ('out', 'OUT Pass'),
        ('in', 'IN Entry'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('out', 'OUT'),
        ('in', 'IN'),
        ('expired', 'Expired'),
    )

    thread = models.ForeignKey(
        WorkThread,
        on_delete=models.CASCADE,
        related_name='gate_passes'
    )

    issued_to = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='gate_passes'
    )

    vehicle_number = models.CharField(
        max_length=20,
        blank=True,
        null=True
    )

    pass_mode = models.CharField(
        max_length=10,
        choices=PASS_MODE_CHOICES,
        default='out'
    )

    purpose = models.TextField()

    valid_from = models.DateTimeField()
    valid_to = models.DateTimeField()

    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending'
    )

    # ✅ APPROVAL SYSTEM
    approved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_gate_passes'
    )

    approved_at = models.DateTimeField(blank=True, null=True)

    rejection_reason = models.TextField(blank=True, null=True)

    # ✅ OUT & IN TRACKING
    out_time = models.DateTimeField(blank=True, null=True)
    in_time = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def mark_out(self):
        """Call this when OUT pass is used"""
        self.status = 'out'
        self.pass_mode = 'out'
        self.out_time = timezone.now()
        self.save()

    def mark_in(self):
        """Call this when person/vehicle returns"""
        self.status = 'in'
        self.pass_mode = 'in'
        self.in_time = timezone.now()
        self.save()

    def __str__(self):
        return f"GatePass | {self.thread.thread_number} | {self.status}"



class WorkClaim(models.Model):

    PAYMENT_STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('paid', 'Paid'),
    )

    thread = models.ForeignKey(
        WorkThread,
        on_delete=models.CASCADE,
        related_name='claims'
    )

    # ✅ CLAIM AMOUNT (OPTIONAL)
    claim_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        blank=True,
        null=True
    )

    # ✅ BILL / INVOICE UPLOAD
    bill_document = models.FileField(
        upload_to='claim_bills/',
        blank=True,
        null=True
    )

    # ✅ WORK DONE STATUS
    work_done = models.BooleanField(default=False)

    # ✅ PAYMENT APPROVAL ID
    approval_id = models.CharField(
        max_length=100,
        blank=True,
        null=True
    )

    # ✅ PAYMENT / APPROVAL PROOF IMAGE
    approval_image = models.ImageField(
        upload_to='claim_approvals/',
        blank=True,
        null=True
    )

    payment_status = models.CharField(
        max_length=20,
        choices=PAYMENT_STATUS_CHOICES,
        default='pending'
    )

    approved_at = models.DateTimeField(blank=True, null=True)
    paid_at = models.DateTimeField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return (
            f"Claim | {self.thread.thread_number} | "
            f"₹{self.claim_amount if self.claim_amount else 'N/A'} | "
            f"{self.payment_status}"
        )




class PushSubscription(models.Model):
    """
    Stores the browser push subscription for a user.
    Keep one active subscription per browser client (endpoint unique).
    """
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="push_subscriptions")
    endpoint = models.URLField(max_length=1000, unique=True)
    p256dh = models.CharField(max_length=255)
    auth = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    last_seen = models.DateTimeField(default=timezone.now)

    class Meta:
        indexes = [
            models.Index(fields=["user"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"PushSubscription({self.user}, {self.endpoint[:40]}...)"


