"""Serializers for the mobile/JSON API. These reuse the same validation rules
as the web forms so both clients behave identically."""

from django.contrib.auth import get_user_model, password_validation
from django.utils import timezone
from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer

from accounts.forms import QUICK_ADD_DEFAULT_PASSWORD
from darood.forms import addable_users_queryset, managers_queryset
from darood.models import DaroodEntry

User = get_user_model()


# ---------------------------------------------------------------------------
# Users
# ---------------------------------------------------------------------------
class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.CharField(read_only=True)
    role_display = serializers.CharField(source='get_role_display', read_only=True)
    is_superadmin = serializers.BooleanField(read_only=True)
    is_manager = serializers.BooleanField(read_only=True)
    can_add_darood = serializers.BooleanField(read_only=True)
    darood_total = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = (
            'id', 'username', 'first_name', 'last_name', 'full_name',
            'role', 'role_display', 'is_active', 'is_superadmin',
            'is_manager', 'can_add_darood', 'darood_total',
        )

    def get_darood_total(self, obj):
        return getattr(obj, 'darood_total', None) or 0


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name', 'password', 'password2')

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value

    def validate(self, attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({'password2': 'The two passwords do not match.'})
        password_validation.validate_password(attrs['password'])
        return attrs

    def create(self, validated_data):
        validated_data.pop('password2')
        password = validated_data.pop('password')
        user = User(**validated_data)
        user.set_password(password)
        # New accounts start inactive; a super admin activates them later.
        user.is_active = False
        user.role = User.Role.SIMPLE
        user.save()
        return user


class LoginSerializer(TokenObtainPairSerializer):
    """Standard JWT login; also returns the authenticated user object.

    Inactive accounts are rejected automatically (Django's auth backend refuses
    to authenticate users with is_active=False).
    """

    def validate(self, attrs):
        data = super().validate(attrs)
        data['user'] = UserSerializer(self.user).data
        return data


class ChangePasswordSerializer(serializers.Serializer):
    """Self-service password change: verify current, then set the new one."""

    current_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password = serializers.CharField(write_only=True, style={'input_type': 'password'})
    new_password2 = serializers.CharField(write_only=True, style={'input_type': 'password'})

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value

    def validate(self, attrs):
        if attrs['new_password'] != attrs['new_password2']:
            raise serializers.ValidationError({'new_password2': 'The two new passwords do not match.'})
        password_validation.validate_password(attrs['new_password'], self.context['request'].user)
        return attrs

    def save(self, **kwargs):
        user = self.context['request'].user
        user.set_password(self.validated_data['new_password'])
        user.save(update_fields=['password'])
        return user


class QuickAddUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'first_name', 'last_name')
        extra_kwargs = {
            'first_name': {'required': False, 'allow_blank': True},
            'last_name': {'required': False, 'allow_blank': True},
        }

    def validate_username(self, value):
        if User.objects.filter(username__iexact=value).exists():
            raise serializers.ValidationError('A user with that username already exists.')
        return value

    def create(self, validated_data):
        user = User(**validated_data)
        user.role = User.Role.SIMPLE
        user.is_active = True
        user.set_password(QUICK_ADD_DEFAULT_PASSWORD)
        user.save()
        return user


class UserUpdateSerializer(serializers.ModelSerializer):
    """Super admin: change role and/or active status of a non-admin user."""

    class Meta:
        model = User
        fields = ('role', 'is_active')
        extra_kwargs = {
            'role': {'required': False},
            'is_active': {'required': False},
        }

    def validate_role(self, value):
        if value not in (User.Role.SIMPLE, User.Role.MANAGER):
            raise serializers.ValidationError('You can only assign Simple User or Manager.')
        return value


# ---------------------------------------------------------------------------
# Darood entries
# ---------------------------------------------------------------------------
class DaroodEntrySerializer(serializers.ModelSerializer):
    user_name = serializers.CharField(source='user.full_name', read_only=True)
    manager_name = serializers.SerializerMethodField()
    recorded_by_name = serializers.SerializerMethodField()
    status_display = serializers.CharField(source='get_status_display', read_only=True)

    class Meta:
        model = DaroodEntry
        fields = (
            'id', 'user', 'user_name', 'count', 'date',
            'status', 'status_display', 'manager', 'manager_name',
            'recorded_by', 'recorded_by_name', 'reviewed_at', 'created_at',
        )

    def get_manager_name(self, obj):
        return obj.manager.full_name if obj.manager_id else None

    def get_recorded_by_name(self, obj):
        return obj.recorded_by.full_name if obj.recorded_by_id else None


class _DaroodWriteMixin:
    def validate_date(self, value):
        if value and value > timezone.localdate():
            raise serializers.ValidationError("The date can't be in the future.")
        return value

    def validate_count(self, value):
        if value < 1:
            raise serializers.ValidationError('Count must be at least 1.')
        return value


class RecordDaroodSerializer(_DaroodWriteMixin, serializers.ModelSerializer):
    """Manager / super admin records darood for a searched user (auto-approved)."""

    class Meta:
        model = DaroodEntry
        fields = ('user', 'date', 'count')

    def __init__(self, *args, request_user=None, **kwargs):
        super().__init__(*args, **kwargs)
        if request_user is not None:
            # Enforce, server-side, that the target is one the requester may pick.
            self.fields['user'].queryset = addable_users_queryset(request_user)


class SubmitDaroodSerializer(_DaroodWriteMixin, serializers.ModelSerializer):
    """A simple user submits their own darood to a manager (pending)."""

    class Meta:
        model = DaroodEntry
        fields = ('manager', 'date', 'count')

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['manager'].queryset = managers_queryset()
        self.fields['manager'].required = True
