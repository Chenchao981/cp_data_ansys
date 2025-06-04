#!/usr/bin/env python
# -*- coding: utf-8 -*-

from frontend.charts.boxplot_chart import BoxplotChart

chart = BoxplotChart('output')
chart.load_data()
param_info = chart.get_parameter_info('IGSSR1')

print(f'IGSSR1 spec: LimitL={param_info.get("limit_lower")}, LimitU={param_info.get("limit_upper")}')

lsl = min(param_info['limit_lower'], param_info['limit_upper'])
usl = max(param_info['limit_lower'], param_info['limit_upper'])
padding = (usl - lsl) * 0.1

print(f'Y轴范围: [{lsl-padding:.2e}, {usl+padding:.2e}]')
print(f'范围跨度: {(usl+padding)-(lsl-padding):.2e}') 