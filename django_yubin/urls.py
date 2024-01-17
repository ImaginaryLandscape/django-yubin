from django_yubin.views import MailHealthCheckView
from django.urls import re_path


urlpatterns = [
    re_path(r'^health$', MailHealthCheckView.as_view(), name='yubin_health'),
]
