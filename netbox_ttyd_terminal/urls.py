from django.urls import path

from .views import DeviceShellView

app_name = "netbox_ttyd_terminal"

urlpatterns = [
    path("device/<int:pk>/shell/", DeviceShellView.as_view(), name="device_shell"),
]

