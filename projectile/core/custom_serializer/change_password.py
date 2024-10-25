from django.contrib.auth import password_validation
from django.utils.translation import gettext_lazy as _
from rest_framework import serializers


class PasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(max_length=128)
    new_password = serializers.CharField(max_length=128)
    re_new_password = serializers.CharField(max_length=128)

    def validate_current_password(self, value):
        invalid_password_conditions = (
            self.context['request'].user,
            not self.context['request'].user.check_password(value),
        )

        if all(invalid_password_conditions):
            err_msg = _('YOUR_CURRENT_PASSWORD_IS_INCORRECT')
            raise serializers.ValidationError(err_msg)
        return value

    def validate(self, attrs):
        new_password = attrs.get('new_password')
        re_new_password = attrs.get('re_new_password')
        if new_password and re_new_password:
            if new_password != re_new_password:
                raise serializers.ValidationError({
                    'detail': _('NEW_PASSWORD_AND_RE_NEW_PASSWORD_FIELDS_ARE_MISMATCHED')
                })
        password_validation.validate_password(re_new_password, self.context['request'].user)
        return attrs

    def save(self, commit=True):
        password = self.validated_data["new_password"]
        self.context['request'].user.set_password(password)
        if commit:
            self.context['request'].user.save()
        from django.contrib.auth import update_session_auth_hash
        update_session_auth_hash(self.context['request'], self.context['request'].user)
