from rest_framework import serializers

from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.utils.translation import ugettext as _

from misago.conf import settings
from misago.users.validators import validate_email, validate_username


UserModel = get_user_model()


class ForumOptionsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = [
            'is_hiding_presence', 'limits_private_thread_invites_to',
            'subscribe_to_started_threads', 'subscribe_to_replied_threads'
        ]
        extra_kwargs = {
            'limits_private_thread_invites_to': {
                'required': True
            },
            'subscribe_to_started_threads': {
                'required': True
            },
            'subscribe_to_replied_threads': {
                'required': True
            },
        }


class EditSignatureSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserModel
        fields = ['signature']

    def validate(self, data):
        if len(data.get('signature', '')) > settings.signature_length_max:
            raise serializers.ValidationError(_("Signature is too long."))

        return data


class ChangeUsernameSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=200, required=True, allow_blank=False)

    def validate_username(self, username):
        if username == self.context['user'].username:
            raise serializers.ValidationError(_("New username is same as current one."))
        validate_username(username)
        return username

    def change_username(self, changed_by):
        self.context['user'].set_username(self.validated_data['username'], changed_by=changed_by)
        self.context['user'].save(update_fields=['username', 'slug'])


class ChangePasswordSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=200, trim_whitespace=False)
    new_password = serializers.CharField(max_length=200, trim_whitespace=False)

    def validate_password(self, value):
        if not self.context['user'].check_password(value):
            raise serializers.ValidationError(_("Entered password is invalid."))
        return value

    def validate_new_password(self, value):
        validate_password(value, user=self.context['user'])
        return value


class ChangeEmailSerializer(serializers.Serializer):
    password = serializers.CharField(max_length=200, trim_whitespace=False)
    new_email = serializers.CharField(max_length=200)

    def validate_password(self, value):
        if not self.context['user'].check_password(value):
            raise serializers.ValidationError(_("Entered password is invalid."))
        return value

    def validate_new_email(self, value):
        if not value:
            raise serializers.ValidationError(_("You have to enter new e-mail address."))

        if value.lower() == self.context['user'].email.lower():
            raise serializers.ValidationError(_("New e-mail is same as current one."))

        validate_email(value)

        return value
