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
        
        # 检查自定义字段 management_IP 是否有值
        mgmt_ip = obj.custom_field_data.get("management_IP")
        if not mgmt_ip:
            return ""
            
        return self.render(
            "netbox_ttyd_terminal/inc/terminal_button.html",
            {
                "device": obj,
            },
        )


template_extensions = [DeviceTerminalButton]

