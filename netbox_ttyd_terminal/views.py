from urllib.parse import urlencode

from django.conf import settings
from django.contrib.auth.mixins import PermissionRequiredMixin
from django.shortcuts import get_object_or_404, render
from django.views import View

from dcim.models import Device


def get_ttyd_base_url() -> str:
    cfg = getattr(settings, "PLUGINS_CONFIG", {}).get("netbox_ttyd_terminal", {}) or {}
    return cfg.get("ttyd_base_url", "http://localhost:7681")


class DeviceShellView(PermissionRequiredMixin, View):
    permission_required = "dcim.view_device"

    def get(self, request, pk: int):
        device = get_object_or_404(Device, pk=pk)
        ip_obj = getattr(device, "primary_ip4", None) or getattr(device, "primary_ip6", None)
        ip = str(ip_obj.address.ip) if ip_obj else None
        ssh_username = request.GET.get("SSH_USERNAME") or request.GET.get("ssh_username") or ""
        ssh_password = request.GET.get("SSH_PASSWORD") or request.GET.get("ssh_password") or ""
        base_url = get_ttyd_base_url()
        ttyd_url = base_url
        if ip and ssh_username:
            query = urlencode(
                {
                    "arg": f"{ssh_username}@{ip}",
                }
            )
            ttyd_url = f"{base_url}?{query}"
        return render(
            request,
            "netbox_ttyd_terminal/device_shell.html",
            {
                "device": device,
                "device_ip": ip,
                "ssh_username": ssh_username,
                "ttyd_url": ttyd_url,
            },
        )

