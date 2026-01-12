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
        
        # 尝试获取自定义字段，兼容 management_IP 和 managment_IP (预防拼写错误)
        mgmt_ip = obj.custom_field_data.get("management_IP") or obj.custom_field_data.get("managment_IP")
        
        # 如果还是没有，可以尝试列出所有 key 方便调试 (可选)
        if not mgmt_ip:
            # print(f"DEBUG: Available CF keys: {list(obj.custom_field_data.keys())}")
            return ""
            
        return self.render(
            "netbox_ttyd_terminal/inc/terminal_button.html",
            {
                "device": obj,
            },
        )


template_extensions = [DeviceTerminalButton]

