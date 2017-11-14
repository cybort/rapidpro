from __future__ import unicode_literals, absolute_import

import telegram

from django import forms
from django.core.exceptions import ValidationError
from django.utils.translation import ugettext_lazy as _
from smartmin.views import SmartFormView
from ...models import Channel
from ...views import ClaimViewMixin


class ClaimView(ClaimViewMixin, SmartFormView):
    class Form(ClaimViewMixin.Form):
        auth_token = forms.CharField(
            label=_("Authentication Token"), help_text=_("The Authentication token for your Telegram Bot")
        )

        def clean_auth_token(self):
            org = self.request.user.get_org()
            value = self.cleaned_data['auth_token']

            # does a bot already exist on this account with that auth token
            for channel in Channel.objects.filter(org=org, is_active=True, channel_type=self.channel_type.code):
                if channel.config_json()['auth_token'] == value:
                    raise ValidationError(_("A telegram channel for this bot already exists on your account."))

            try:
                bot = telegram.Bot(token=value)
                bot.get_me()
            except telegram.TelegramError:
                raise ValidationError(_("Your authentication token is invalid, please check and try again"))

            return value

    form_class = Form

    def form_valid(self, form):
        org = self.request.user.get_org()
        auth_token = self.form.cleaned_data['auth_token']

        bot = telegram.Bot(auth_token)
        me = bot.get_me()

        self.object = Channel.create(
            org,
            self.request.user,
            None,
            self.channel_type,
            name=me.first_name,
            address=me.username,
            config={
                'auth_token': auth_token
            }
        )

        return super(ClaimView, self).form_valid(form)
