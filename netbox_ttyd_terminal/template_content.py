try:
    from netbox.plugins import PluginTemplateExtension
except ImportError:
    from extras.plugins import PluginTemplateExtension


class DeviceTerminalButton(PluginTemplateExtension):
    model = "dcim.device"

    def buttons(self):
        obj = self.context.get("object") or self.context.get("record")
        if not obj:
            return ""
        ip_obj = getattr(obj, "primary_ip4", None) or getattr(obj, "primary_ip6", None)
        if not ip_obj:
            return ""
        return self.render(
            "netbox_ttyd_terminal/inc/terminal_button.html",
            {
                "device": obj,
            },
        )


template_extensions = [DeviceTerminalButton]

