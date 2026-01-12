from netbox.plugins import PluginConfig


class TtydTerminalConfig(PluginConfig):
    name = "netbox_ttyd_terminal"
    verbose_name = "TTYD 终端"
    description = "在设备详情页提供基于 TTYD 的 Web SSH 终端"
    version = "0.1.0"
    base_url = "ttyd-terminal"
    default_settings = {
        "ttyd_base_url": "http://localhost:7681",
    }


config = TtydTerminalConfig

