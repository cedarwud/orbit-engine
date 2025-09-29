#!/usr/bin/env python3
"""
NTPU衛星換手場景視覺化
聚焦於NTPU上空的衛星動態池和換手事件
"""

import dash
from dash import dcc, html, Input, Output, State
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import dash_bootstrap_components as dbc

# NTPU座標
NTPU_LAT = 24.9442
NTPU_LON = 121.3711

class NTPUHandoverSimulator:
    def __init__(self):
        self.current_time = 0
        self.handover_history = []
        self.serving_satellite = None

    def generate_satellite_passes(self):
        """生成經過NTPU的衛星過境數據"""
        passes = []

        # Starlink衛星過境（90分鐘週期，每5-10分鐘有新衛星進入）
        for i in range(30):  # 30顆Starlink
            entry_time = i * 3 + np.random.uniform(-1, 1)  # 錯開進入時間
            pass_duration = np.random.uniform(8, 12)  # 8-12分鐘可見

            passes.append({
                'id': f'STARLINK-{i+1:03d}',
                'constellation': 'Starlink',
                'entry_time': entry_time % 90,
                'exit_time': (entry_time + pass_duration) % 90,
                'max_elevation': np.random.uniform(20, 85),
                'azimuth_entry': np.random.uniform(0, 360),
                'azimuth_exit': (np.random.uniform(0, 360)) % 360,
                'max_rsrp': -70 + np.random.uniform(-10, 10)
            })

        # OneWeb衛星過境（115分鐘週期）
        for i in range(10):  # 10顆OneWeb
            entry_time = i * 11 + np.random.uniform(-2, 2)
            pass_duration = np.random.uniform(10, 15)  # 10-15分鐘可見

            passes.append({
                'id': f'ONEWEB-{i+1:03d}',
                'constellation': 'OneWeb',
                'entry_time': entry_time % 115,
                'exit_time': (entry_time + pass_duration) % 115,
                'max_elevation': np.random.uniform(25, 80),
                'azimuth_entry': np.random.uniform(0, 360),
                'azimuth_exit': (np.random.uniform(0, 360)) % 360,
                'max_rsrp': -75 + np.random.uniform(-8, 8)
            })

        return passes

    def get_visible_satellites(self, time_minute):
        """獲取特定時間NTPU上空可見的衛星"""
        visible = []

        for sat in self.satellite_passes:
            # 檢查衛星是否在可見時間窗口內
            if sat['entry_time'] <= sat['exit_time']:
                is_visible = sat['entry_time'] <= time_minute <= sat['exit_time']
            else:  # 跨越0點的情況
                is_visible = time_minute >= sat['entry_time'] or time_minute <= sat['exit_time']

            if is_visible:
                # 計算當前仰角和方位角
                progress = (time_minute - sat['entry_time']) / (sat['exit_time'] - sat['entry_time'] + 0.001)
                progress = max(0, min(1, progress))

                # 仰角變化：上升-最高-下降
                if progress < 0.5:
                    elevation = sat['max_elevation'] * (progress * 2)
                else:
                    elevation = sat['max_elevation'] * (2 - progress * 2)

                # 方位角插值
                azimuth = sat['azimuth_entry'] + (sat['azimuth_exit'] - sat['azimuth_entry']) * progress

                # RSRP根據仰角計算
                rsrp = sat['max_rsrp'] - (90 - elevation) * 0.5

                # 檢查是否滿足可見門檻
                min_elevation = 5 if sat['constellation'] == 'Starlink' else 10

                if elevation >= min_elevation:
                    visible.append({
                        'id': sat['id'],
                        'constellation': sat['constellation'],
                        'elevation': elevation,
                        'azimuth': azimuth % 360,
                        'rsrp': rsrp,
                        'time_to_exit': sat['exit_time'] - time_minute if sat['exit_time'] > time_minute else 0
                    })

        return visible

    def check_handover_events(self, current_visible, time_minute):
        """檢測3GPP換手事件"""
        events = []

        if not current_visible:
            return events

        # 排序找出最佳候選
        sorted_sats = sorted(current_visible, key=lambda x: x['rsrp'], reverse=True)
        best_candidate = sorted_sats[0]

        # A4事件：鄰近衛星優於門檻（-95 dBm）
        for sat in sorted_sats[1:]:
            if sat['rsrp'] > -95:
                events.append({
                    'type': 'A4',
                    'time': time_minute,
                    'satellite': sat['id'],
                    'rsrp': sat['rsrp'],
                    'description': f"{sat['id']} 信號優於門檻 (-95 dBm)"
                })
                break

        # A5事件：服務衛星劣化且有更好的候選
        if self.serving_satellite:
            serving_sat = next((s for s in current_visible if s['id'] == self.serving_satellite), None)
            if serving_sat and serving_sat['rsrp'] < -100:
                if best_candidate['id'] != self.serving_satellite and best_candidate['rsrp'] > -90:
                    events.append({
                        'type': 'A5',
                        'time': time_minute,
                        'from_satellite': self.serving_satellite,
                        'to_satellite': best_candidate['id'],
                        'description': f"換手建議: {self.serving_satellite} → {best_candidate['id']}"
                    })
                    self.serving_satellite = best_candidate['id']

        # D2事件：基於即將離開的時間
        for sat in current_visible:
            if sat['time_to_exit'] < 2:  # 2分鐘內將離開
                events.append({
                    'type': 'D2',
                    'time': time_minute,
                    'satellite': sat['id'],
                    'time_to_exit': sat['time_to_exit'],
                    'description': f"{sat['id']} 即將離開覆蓋範圍"
                })

        # 如果沒有服務衛星，選擇最佳的
        if not self.serving_satellite and best_candidate:
            self.serving_satellite = best_candidate['id']
            events.append({
                'type': 'Initial',
                'time': time_minute,
                'satellite': best_candidate['id'],
                'description': f"選擇 {best_candidate['id']} 作為服務衛星"
            })

        return events

# 初始化模擬器
simulator = NTPUHandoverSimulator()
simulator.satellite_passes = simulator.generate_satellite_passes()

# 創建Dash應用
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    dbc.Row([
        dbc.Col([
            html.H1("🎯 NTPU衛星換手場景模擬", className="text-center mb-4"),
            html.P("聚焦於NTPU上空的衛星動態池與3GPP換手事件", className="text-center text-muted")
        ])
    ]),

    # 控制面板
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardBody([
                    html.H5("⏱️ 時間控制"),
                    dcc.Slider(
                        id='time-slider',
                        min=0, max=120, step=1, value=0,
                        marks={i: f'{i}分' for i in range(0, 121, 20)},
                        tooltip={"placement": "bottom", "always_visible": True}
                    ),
                    html.Div(id='current-time', className='mt-2 text-center')
                ])
            ])
        ])
    ], className="mb-4"),

    # 主要視覺化
    dbc.Row([
        dbc.Col([
            # NTPU天空視圖
            dcc.Graph(id='sky-view', style={'height': '500px'})
        ], width=6),
        dbc.Col([
            # 衛星池狀態圖
            dcc.Graph(id='pool-timeline', style={'height': '500px'})
        ], width=6)
    ]),

    # 狀態顯示
    dbc.Row([
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📊 當前衛星池狀態"),
                dbc.CardBody(id='pool-status')
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("📡 服務衛星"),
                dbc.CardBody(id='serving-status')
            ])
        ], width=4),
        dbc.Col([
            dbc.Card([
                dbc.CardHeader("🚨 換手事件"),
                dbc.CardBody(id='handover-events')
            ])
        ], width=4)
    ], className="mt-4"),

    # RSRP比較圖
    dbc.Row([
        dbc.Col([
            dcc.Graph(id='rsrp-comparison', style={'height': '300px'})
        ])
    ], className="mt-4"),

    # 自動更新
    dcc.Interval(
        id='auto-update',
        interval=2000,  # 每2秒更新
        n_intervals=0,
        disabled=False
    )
])

@app.callback(
    [Output('sky-view', 'figure'),
     Output('pool-timeline', 'figure'),
     Output('pool-status', 'children'),
     Output('serving-status', 'children'),
     Output('handover-events', 'children'),
     Output('rsrp-comparison', 'figure'),
     Output('current-time', 'children')],
    [Input('time-slider', 'value'),
     Input('auto-update', 'n_intervals')]
)
def update_visualization(manual_time, n_intervals):
    # 使用手動時間或自動增加
    current_time = manual_time if manual_time > 0 else (n_intervals * 0.5) % 120

    # 獲取當前可見衛星
    visible_sats = simulator.get_visible_satellites(current_time)

    # 檢測換手事件
    handover_events = simulator.check_handover_events(visible_sats, current_time)
    if handover_events:
        simulator.handover_history.extend(handover_events)

    # 1. NTPU天空視圖（極座標）
    fig_sky = go.Figure()

    # 添加仰角圓圈
    for elev in [0, 30, 60, 90]:
        r = 90 - elev
        theta = np.linspace(0, 360, 100)
        fig_sky.add_trace(go.Scatterpolar(
            r=[r]*100, theta=theta,
            mode='lines',
            line=dict(color='lightgray', width=1),
            showlegend=False,
            hoverinfo='skip'
        ))

    # 添加可見衛星
    for sat in visible_sats:
        color = 'red' if sat['constellation'] == 'Starlink' else 'blue'
        size = 15 if sat['id'] == simulator.serving_satellite else 10
        symbol = 'star' if sat['id'] == simulator.serving_satellite else 'circle'

        fig_sky.add_trace(go.Scatterpolar(
            r=[90 - sat['elevation']],
            theta=[sat['azimuth']],
            mode='markers+text',
            marker=dict(size=size, color=color, symbol=symbol),
            text=sat['id'].split('-')[1],
            textposition='top center',
            name=sat['id'],
            hovertext=f"{sat['id']}<br>仰角: {sat['elevation']:.1f}°<br>方位: {sat['azimuth']:.1f}°<br>RSRP: {sat['rsrp']:.1f} dBm"
        ))

    fig_sky.update_layout(
        title="🌌 NTPU天空視圖（北方朝上）",
        polar=dict(
            radialaxis=dict(
                visible=True,
                range=[0, 90],
                tickmode='array',
                tickvals=[0, 30, 60, 90],
                ticktext=['90°', '60°', '30°', '0°']
            )
        ),
        showlegend=False
    )

    # 2. 衛星池時間線
    fig_timeline = go.Figure()

    # 計算未來30分鐘的衛星池狀態
    future_times = np.arange(current_time, current_time + 30, 1)
    starlink_counts = []
    oneweb_counts = []

    for t in future_times:
        future_visible = simulator.get_visible_satellites(t % 120)
        starlink_counts.append(sum(1 for s in future_visible if s['constellation'] == 'Starlink'))
        oneweb_counts.append(sum(1 for s in future_visible if s['constellation'] == 'OneWeb'))

    fig_timeline.add_trace(go.Scatter(
        x=future_times,
        y=starlink_counts,
        mode='lines+markers',
        name='Starlink',
        line=dict(color='red', width=2)
    ))

    fig_timeline.add_trace(go.Scatter(
        x=future_times,
        y=oneweb_counts,
        mode='lines+markers',
        name='OneWeb',
        line=dict(color='blue', width=2)
    ))

    # 添加目標範圍
    fig_timeline.add_hrect(y0=10, y1=15, fillcolor="red", opacity=0.1)
    fig_timeline.add_hrect(y0=3, y1=6, fillcolor="blue", opacity=0.1)

    # 標記當前時間
    fig_timeline.add_vline(x=current_time, line_dash="dash", line_color="green")

    fig_timeline.update_layout(
        title="📈 衛星池狀態預測（未來30分鐘）",
        xaxis_title="時間（分鐘）",
        yaxis_title="可見衛星數量",
        showlegend=True
    )

    # 3. 衛星池狀態
    starlink_visible = [s for s in visible_sats if s['constellation'] == 'Starlink']
    oneweb_visible = [s for s in visible_sats if s['constellation'] == 'OneWeb']

    pool_status = html.Div([
        dbc.Badge(f"Starlink: {len(starlink_visible)}/15",
                 color="success" if 10 <= len(starlink_visible) <= 15 else "warning",
                 className="me-2"),
        dbc.Badge(f"OneWeb: {len(oneweb_visible)}/6",
                 color="success" if 3 <= len(oneweb_visible) <= 6 else "warning"),
        html.Hr(),
        html.Small(f"總計: {len(visible_sats)} 顆可見")
    ])

    # 4. 服務衛星狀態
    if simulator.serving_satellite:
        serving = next((s for s in visible_sats if s['id'] == simulator.serving_satellite), None)
        if serving:
            serving_status = html.Div([
                html.H5(simulator.serving_satellite),
                html.P(f"RSRP: {serving['rsrp']:.1f} dBm"),
                html.P(f"仰角: {serving['elevation']:.1f}°"),
                html.P(f"剩餘時間: {serving['time_to_exit']:.1f} 分鐘")
            ])
        else:
            serving_status = html.Div("服務衛星已離開")
    else:
        serving_status = html.Div("未選擇服務衛星")

    # 5. 換手事件
    recent_events = simulator.handover_history[-5:] if simulator.handover_history else []
    handover_display = html.Div([
        html.Div([
            dbc.Alert(
                [html.Strong(e['type']), html.Br(), e['description']],
                color="warning" if e['type'] == 'A4' else "danger" if e['type'] == 'A5' else "info",
                className="mb-2"
            )
        ]) for e in reversed(recent_events)
    ])

    # 6. RSRP比較圖
    fig_rsrp = go.Figure()

    if visible_sats:
        sorted_sats = sorted(visible_sats, key=lambda x: x['rsrp'], reverse=True)[:5]

        colors = ['gold' if s['id'] == simulator.serving_satellite else 'gray' for s in sorted_sats]

        fig_rsrp.add_trace(go.Bar(
            x=[s['id'] for s in sorted_sats],
            y=[s['rsrp'] for s in sorted_sats],
            marker_color=colors
        ))

        # 添加門檻線
        fig_rsrp.add_hline(y=-95, line_dash="dash", line_color="orange", annotation_text="A4門檻")
        fig_rsrp.add_hline(y=-100, line_dash="dash", line_color="red", annotation_text="A5門檻")

    fig_rsrp.update_layout(
        title="📶 RSRP信號強度比較",
        xaxis_title="衛星ID",
        yaxis_title="RSRP (dBm)",
        yaxis_range=[-120, -60]
    )

    # 時間顯示
    time_display = f"模擬時間: {int(current_time)} 分鐘"

    return (fig_sky, fig_timeline, pool_status, serving_status,
            handover_display, fig_rsrp, time_display)

if __name__ == '__main__':
    print("🚀 啟動NTPU衛星換手場景模擬...")
    print("🌐 訪問: http://120.126.151.103:8050")
    print("\n📊 模擬特色:")
    print("  • NTPU天空視圖 - 顯示衛星實際位置")
    print("  • 動態衛星池 - 即時追蹤可見衛星數")
    print("  • 3GPP換手事件 - A4/A5/D2事件檢測")
    print("  • RSRP比較 - 候選衛星信號強度")
    print("  • 服務衛星追蹤 - 當前連接狀態")

    app.run(host='0.0.0.0', port=8050, debug=False)