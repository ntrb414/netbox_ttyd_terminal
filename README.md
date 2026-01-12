# netbox_ttyd_terminal

一个面向 NetBox 的教学型插件示例，通过集成开源 Web 终端工具 **TTYD**，在设备详情页提供交互式 Web SSH 终端入口。

该项目适合用来学习：

- NetBox 插件的基本结构与文件组织方式
- 如何使用 `PluginTemplateExtension` 在设备详情页注入按钮
- 如何通过插件路由与视图，将 NetBox 的设备信息（如管理 IP）传递给外部 Web 终端服务

---

## 功能概览

- 在 **设备详情页** 增加一个按钮：`Terminal`
- 点击按钮后，弹出对话框，要求用户输入：
  - `SSH_USERNAME`
  - `SSH_PASSWORD`（当前示例只做表单传递，实际密码处理由 TTYD/SSH 端负责）
- 点击 `Commit` 后跳转到新页面：
  - 页面中通过 `<iframe>` 嵌入 TTYD 提供的 Web 终端界面
  - 终端窗口支持：
    - 上下滚动查看历史输出
    - 浏览器原生复制粘贴
    - 交互式命令输入与执行（由 TTYD + SSH 提供）

> 注意：本插件只负责 **拼装 URL 与页面集成**，真正的 SSH 连接与命令交互由外部运行的 TTYD 服务完成。

---

## 项目结构

项目的目录结构尽量保持简单清晰，方便对照学习：

```text
netbox_ttyd_terminal/
├─ README.md                     # 本说明文件
├─ setup.py                      # Python 包 & NetBox 插件安装入口
├─ MANIFEST.in                   # 打包时包含模板文件
└─ netbox_ttyd_terminal/
   ├─ __init__.py                # 插件配置：PluginConfig 派生类
   ├─ template_content.py        # 设备详情页上的 Terminal 按钮注入逻辑
   ├─ urls.py                    # 插件内部 URL 路由定义
   ├─ views.py                   # 处理表单并拼装 TTYD 地址的视图
   └─ templates/
      └─ netbox_ttyd_terminal/
         ├─ device_shell.html    # 终端页面：通过 iframe 嵌入 TTYD
         └─ inc/
            └─ terminal_button.html  # “Terminal” 按钮与弹窗表单
```

下面对几个关键文件做简要说明。

### 1. 插件配置：`__init__.py`

```python
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
```

- `name`：插件的 Python 包名，也是 `PLUGINS` 中使用的名字。
- `base_url`：插件在 NetBox 中的基础 URL 前缀，例如：
  - `/plugins/ttyd-terminal/...`
- `default_settings`：允许在 NetBox `configuration.py` 中覆盖的配置项，这里主要是 TTYD 的基础访问地址。

### 2. 设备详情页按钮：`template_content.py`

```python
from netbox.plugins import PluginTemplateExtension


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
```

主要作用：

- 限定只对 `dcim.device` 模型生效。
- 尝试获取设备的管理 IP（`primary_ip4` 或 `primary_ip6`），若没有则隐藏按钮。
- 渲染 `inc/terminal_button.html` 模板，将当前 `device` 传入模板上下文。

### 3. 路由与视图：`urls.py` 与 `views.py`

`urls.py` 定义了一个用于显示终端页面的路由：

```python
from django.urls import path
from .views import DeviceShellView

app_name = "netbox_ttyd_terminal"

urlpatterns = [
    path("device/<int:pk>/shell/", DeviceShellView.as_view(), name="device_shell"),
]
```

`views.py` 则完成以下逻辑：

- 检查用户是否有 `dcim.view_device` 权限。
- 根据 `pk` 获取 NetBox 中的 `Device` 对象。
- 提取其管理 IP（primary_ip4/primary_ip6）。
- 从 `GET` 参数中读取 `SSH_USERNAME` / `SSH_PASSWORD`（本示例不在服务端存储密码）。
- 从插件配置中获取 `ttyd_base_url`，并构造真实的 TTYD 访问地址：

```python
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
```

在默认情况下，如果 TTYD 以 `ttyd ssh` 启动，则访问：

```text
http://TTyD_HOST:7681/?arg=admin@10.0.0.1
```

会在服务器端执行：

```bash
ssh admin@10.0.0.1
```

从而在浏览器中呈现一个真实的 SSH 终端。

### 4. 前端模板：按钮与终端页面

#### 4.1 按钮与弹窗表单：`inc/terminal_button.html`

该模板使用 Bootstrap Modal，在设备详情页注入一个 `Terminal` 按钮：

- 点击按钮后弹出表单。
- 表单字段包括 `SSH_USERNAME` 与 `SSH_PASSWORD`。
- 提交后跳转到 `device_shell` 视图。

#### 4.2 终端页面：`device_shell.html`

终端页面继承自 NetBox 的基础布局，在主体区域嵌入一个 iframe：

```html
<iframe src="{{ ttyd_url }}" style="width: 100%; height: 80vh; border: 0;"></iframe>
```

TTYD 内部使用 xterm.js 渲染终端，因此具备完整的滚动和复制功能。

---

## 在 NetBox 中安装与启用

### 1. 安装插件

在 NetBox 的虚拟环境中，从本仓库根目录执行：

```bash
pip install -e .
```

### 2. 在 NetBox 配置中启用

编辑 NetBox 的 `configuration.py`，增加：

```python
PLUGINS = [
    # ... 其他插件
    "netbox_ttyd_terminal",
]

PLUGINS_CONFIG = {
    "netbox_ttyd_terminal": {
        "ttyd_base_url": "http://localhost:7681",
    },
}
```

之后重启 NetBox 服务。

---

## TTYD 部署示例

在运行 NetBox 的服务器上安装并启动 TTYD，例如：

```bash
ttyd -p 7681 ssh
```

说明：

- 这里的 `ssh` 表示 TTYD 会执行系统自带的 `ssh` 客户端。
- 当浏览器访问：

  ```text
  http://localhost:7681/?arg=admin@10.0.0.1
  ```

  TTYD 实际执行：

  ```bash
  ssh admin@10.0.0.1
  ```

- 密码输入仍在终端内部由用户交互完成。

生产环境中通常会：

- 用 Nginx/Traefik 等为 TTYD 提供 HTTPS 反向代理。
- 配置访问控制，只允许来自 NetBox 或特定管理网段的流量。

---

## 学习建议与扩展方向

你可以在此基础上进一步练习和扩展：

- 将密码处理逻辑下沉到 TTYD 侧脚本或堡垒机，实现半自动登录。
- 根据 NetBox 的 `Platform` 字段，为不同厂商设备预填合适的用户名。
- 在视图中增加审计日志，将“谁在何时打开了哪台设备的终端”记录到数据库。
- 将插件拆解成教学步骤（Tag、分支），用于课堂演示 NetBox 插件的演进过程。

本项目的目标是作为一个“尽量简单但足够完整”的示例，让你可以快速理解 NetBox 插件与外部 Web 终端之间的集成方式。

