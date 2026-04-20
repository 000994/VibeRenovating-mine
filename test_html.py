from config import APIProvider

status_cells = []
for provider in APIProvider:
    configured = False
    badge = '<span class="badge badge-green">已配置</span>' if configured else '<span class="badge badge-gray">未配置</span>'
    cell = f'<div class="status-cell"><div class="status-label">{provider.value.upper()}</div><div class="status-value" style="margin-top:6px;">{badge}</div></div>'
    status_cells.append(cell)

html = f'<div class="status-grid">{ "".join(status_cells) }</div>'
print(html)
