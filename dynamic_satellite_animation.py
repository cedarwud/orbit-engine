#!/usr/bin/env python3
"""
🛰️ 真實動態衛星動畫展示
- 自動播放的衛星軌道動畫
- 即時移動的衛星標記
- 實時更新的衛星池狀態
- 動態換手事件觸發
"""

import numpy as np
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, State
import dash_bootstrap_components as dbc
from datetime import datetime, timedelta
import time
import math

class SatelliteAnimator:
    def __init__(self):
        self.current_time = 0
        self.max_time = 115  # 最長軌道週期
        self.animation_speed = 1  # 每秒前進多少分鐘
        self.satellites = self.generate_realistic_satellites()

    def generate_realistic_satellites(self):
        """生成更真實的衛星軌道動畫數據"""
        satellites = []

        # Starlink 星座 - 多個軌道面
        starlink_planes = 5  # 5個軌道面
        sats_per_plane = 3   # 每個軌道面3顆衛星

        for plane in range(starlink_planes):
            for sat_in_plane in range(sats_per_plane):
                sat_id = f"STARLINK-{plane*sats_per_plane + sat_in_plane + 1}"

                # 不同軌道面有不同的升交點赤經
                raan = plane * 72  # 每個軌道面間隔72度
                # 同軌道面內衛星有相位差
                phase_offset = sat_in_plane * 120  # 120度間隔

                satellite = self.create_satellite_orbit(
                    sat_id=sat_id,
                    constellation="Starlink",
                    altitude=550,      # km
                    inclination=53.0,  # 度
                    raan=raan,
                    phase_offset=phase_offset,
                    orbital_period=95  # 分鐘
                )
                satellites.append(satellite)

        # OneWeb 星座 - 極軌道
        oneweb_planes = 3
        sats_per_plane = 2

        for plane in range(oneweb_planes):
            for sat_in_plane in range(sats_per_plane):
                sat_id = f"ONEWEB-{plane*sats_per_plane + sat_in_plane + 1}"

                raan = plane * 60  # 60度間隔
                phase_offset = sat_in_plane * 180

                satellite = self.create_satellite_orbit(
                    sat_id=sat_id,
                    constellation="OneWeb",
                    altitude=1200,     # km
                    inclination=87.9,  # 極軌道
                    raan=raan,
                    phase_offset=phase_offset,
                    orbital_period=115  # 分鐘
                )
                satellites.append(satellite)

        return satellites

    def create_satellite_orbit(self, sat_id, constellation, altitude, inclination, raan, phase_offset, orbital_period):
        """創建單個衛星的完整軌道"""
        time_points = np.linspace(0, orbital_period, orbital_period * 2)  # 每30秒一個點

        positions = []
        elevations = []
        rsrp_values = []

        earth_radius = 6371  # km
        orbit_radius = earth_radius + altitude

        # NTPU 位置
        ntpu_lat, ntpu_lon = 24.9464, 121.3706
        ntpu_x = earth_radius * np.cos(np.radians(ntpu_lat)) * np.cos(np.radians(ntpu_lon))
        ntpu_y = earth_radius * np.cos(np.radians(ntpu_lat)) * np.sin(np.radians(ntpu_lon))
        ntpu_z = earth_radius * np.sin(np.radians(ntpu_lat))

        for t in time_points:
            # 軌道角度 (加上相位偏移)
            angle = (t / orbital_period) * 2 * np.pi + np.radians(phase_offset)

            # 3D軌道計算 (簡化的SGP4)
            # 軌道平面內的位置
            x_orbit = orbit_radius * np.cos(angle)
            y_orbit = orbit_radius * np.sin(angle)
            z_orbit = 0

            # 應用軌道傾角
            inc_rad = np.radians(inclination)
            x_inclined = x_orbit
            y_inclined = y_orbit * np.cos(inc_rad) - z_orbit * np.sin(inc_rad)
            z_inclined = y_orbit * np.sin(inc_rad) + z_orbit * np.cos(inc_rad)

            # 應用升交點赤經
            raan_rad = np.radians(raan)
            x_final = x_inclined * np.cos(raan_rad) - y_inclined * np.sin(raan_rad)
            y_final = x_inclined * np.sin(raan_rad) + y_inclined * np.cos(raan_rad)
            z_final = z_inclined

            positions.append([x_final, y_final, z_final])

            # 計算相對NTPU的仰角
            sat_to_ntpu = np.array([ntpu_x - x_final, ntpu_y - y_final, ntpu_z - z_final])
            distance = np.linalg.norm(sat_to_ntpu)

            # 仰角計算 (簡化)
            elevation_angle = 90 - np.degrees(np.arccos(np.dot(sat_to_ntpu, [ntpu_x, ntpu_y, ntpu_z]) /
                                                       (distance * earth_radius)))
            elevation_angle = max(0, elevation_angle)
            elevations.append(elevation_angle)

            # RSRP計算 (基於距離和仰角)
            if elevation_angle > 0:
                # 自由空間路徑損耗公式
                frequency_ghz = 12  # Ku波段
                fspl = 32.45 + 20 * np.log10(frequency_ghz) + 20 * np.log10(distance)
                rsrp = 20 - fspl + np.random.normal(0, 2)  # 加入噪聲
            else:
                rsrp = -150  # 不可見時的極低值

            rsrp_values.append(rsrp)

        return {
            'id': sat_id,
            'constellation': constellation,
            'positions': np.array(positions),
            'elevations': elevations,
            'rsrp': rsrp_values,
            'time_points': time_points,
            'orbital_period': orbital_period,
            'color': 'red' if constellation == 'Starlink' else 'blue'
        }

    def get_current_positions(self, current_time):
        """獲取當前時間點所有衛星的位置"""
        current_positions = []

        for sat in self.satellites:
            # 根據軌道週期計算當前位置索引
            time_in_orbit = current_time % sat['orbital_period']

            # 找到最接近的時間點
            time_idx = int((time_in_orbit / sat['orbital_period']) * len(sat['positions']))
            time_idx = min(time_idx, len(sat['positions']) - 1)

            pos = sat['positions'][time_idx]
            elevation = sat['elevations'][time_idx]
            rsrp = sat['rsrp'][time_idx]

            current_positions.append({
                'id': sat['id'],
                'constellation': sat['constellation'],
                'x': pos[0], 'y': pos[1], 'z': pos[2],
                'elevation': elevation,
                'rsrp': rsrp,
                'color': sat['color'],
                'visible': elevation > (5 if sat['constellation'] == 'Starlink' else 10)
            })

        return current_positions

# 創建動畫器
animator = SatelliteAnimator()

# 建立Dash應用
app = dash.Dash(__name__, external_stylesheets=[dbc.themes.BOOTSTRAP])

app.layout = dbc.Container([
    # 標題和控制
    dbc.Row([
        dbc.Col([
            html.H1("🛰️ 即時衛星動態追蹤", className="text-center mb-4"),
            dbc.Card([
                dbc.CardBody([
                    dbc.Row([
                        dbc.Col([
                            html.Label("播放控制:"),
                            dbc.ButtonGroup([
                                dbc.Button("▶️ 播放", id="play-btn", color="success", size="sm"),
                                dbc.Button("⏸️ 暫停", id="pause-btn", color="warning", size="sm"),
                                dbc.Button("🔄 重置", id="reset-btn", color="info", size="sm"),
                            ])
                        ], width=4),
                        dbc.Col([
                            html.Label("播放速度:"),
                            dcc.Slider(
                                id="speed-slider",
                                min=0.5, max=5, step=0.5, value=2,
                                marks={i: f"{i}x" for i in [0.5, 1, 2, 3, 5]},
                                tooltip={"placement": "bottom", "always_visible": True}
                            )
                        ], width=4),
                        dbc.Col([
                            html.Label("當前時間:"),
                            html.H4(id="current-time-display", children="0 分鐘", className="text-primary")
                        ], width=4)
                    ])
                ])
            ], className="mb-4")
        ])
    ]),

    # 主要視覺化區域
    dbc.Row([
        dbc.Col([
            dcc.Graph(
                id="live-3d-plot",
                style={'height': '600px'},
                config={'displayModeBar': False}
            )
        ], width=8),
        dbc.Col([
            # 即時衛星池狀態
            dbc.Card([
                dbc.CardHeader("🎯 即時衛星池狀態"),
                dbc.CardBody([
                    html.Div(id="live-pool-status")
                ])
            ], className="mb-3"),

            # 換手事件監控
            dbc.Card([
                dbc.CardHeader("📡 換手事件"),
                dbc.CardBody([
                    html.Div(id="handover-alerts")
                ])
            ])
        ], width=4)
    ]),

    # 信號品質監控
    dbc.Row([
        dbc.Col([
            dcc.Graph(id="live-signal-plot", style={'height': '300px'})
        ], width=6),
        dbc.Col([
            dcc.Graph(id="live-elevation-plot", style={'height': '300px'})
        ], width=6)
    ], className="mt-4"),

    # 自動更新間隔
    dcc.Interval(
        id='animation-interval',
        interval=500,  # 500ms 更新一次
        n_intervals=0,
        disabled=False
    ),

    # 儲存動畫狀態
    dcc.Store(id='animation-state', data={'playing': True, 'current_time': 0, 'speed': 2})
])

# 回調函數：動畫控制
@app.callback(
    Output('animation-state', 'data'),
    [Input('play-btn', 'n_clicks'),
     Input('pause-btn', 'n_clicks'),
     Input('reset-btn', 'n_clicks'),
     Input('speed-slider', 'value'),
     Input('animation-interval', 'n_intervals')],
    State('animation-state', 'data')
)
def update_animation_state(play_clicks, pause_clicks, reset_clicks, speed, n_intervals, current_state):
    ctx = dash.callback_context

    if not ctx.triggered:
        return current_state

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]

    if trigger_id == 'play-btn':
        current_state['playing'] = True
    elif trigger_id == 'pause-btn':
        current_state['playing'] = False
    elif trigger_id == 'reset-btn':
        current_state['current_time'] = 0
        current_state['playing'] = True
    elif trigger_id == 'speed-slider':
        current_state['speed'] = speed
    elif trigger_id == 'animation-interval' and current_state['playing']:
        # 根據速度更新時間
        current_state['current_time'] += current_state['speed'] * 0.5  # 0.5分鐘/次
        if current_state['current_time'] >= animator.max_time:
            current_state['current_time'] = 0  # 循環播放

    return current_state

# 主要視覺化更新
@app.callback(
    [Output('live-3d-plot', 'figure'),
     Output('current-time-display', 'children'),
     Output('live-pool-status', 'children'),
     Output('handover-alerts', 'children'),
     Output('live-signal-plot', 'figure'),
     Output('live-elevation-plot', 'figure')],
    [Input('animation-interval', 'n_intervals'),
     Input('animation-state', 'data')]
)
def update_live_visualization(n_intervals, animation_state):
    try:
        # 使用 n_intervals 來驅動動畫時間
        current_time = n_intervals * 0.5  # 每次間隔 0.5 分鐘

        # 獲取當前所有衛星位置
        current_positions = animator.get_current_positions(current_time)

        # 3D 動態圖
        fig_3d = go.Figure()

        # 添加地球
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 30)
        earth_radius = 6371
        earth_x = earth_radius * np.outer(np.cos(u), np.sin(v))
        earth_y = earth_radius * np.outer(np.sin(u), np.sin(v))
        earth_z = earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))

        fig_3d.add_trace(go.Surface(
            x=earth_x, y=earth_y, z=earth_z,
            colorscale='Earth', opacity=0.8, showscale=False,
            name="地球"
        ))

        # 添加NTPU位置
        ntpu_x = 6371 * np.cos(np.radians(24.9464)) * np.cos(np.radians(121.3706))
        ntpu_y = 6371 * np.cos(np.radians(24.9464)) * np.sin(np.radians(121.3706))
        ntpu_z = 6371 * np.sin(np.radians(24.9464))

        fig_3d.add_trace(go.Scatter3d(
            x=[ntpu_x], y=[ntpu_y], z=[ntpu_z],
            mode='markers',
            marker=dict(size=12, color='gold', symbol='diamond'),
            name="NTPU"
        ))

        # 添加移動的衛星
        starlink_positions = [pos for pos in current_positions if pos['constellation'] == 'Starlink']
        oneweb_positions = [pos for pos in current_positions if pos['constellation'] == 'OneWeb']

        if starlink_positions:
            fig_3d.add_trace(go.Scatter3d(
                x=[pos['x'] for pos in starlink_positions],
                y=[pos['y'] for pos in starlink_positions],
                z=[pos['z'] for pos in starlink_positions],
                mode='markers',
                marker=dict(
                    size=[10 if pos['visible'] else 5 for pos in starlink_positions],
                    color=['red' if pos['visible'] else 'pink' for pos in starlink_positions],
                    symbol='circle'
                ),
                text=[f"{pos['id']}<br>仰角: {pos['elevation']:.1f}°<br>RSRP: {pos['rsrp']:.1f}dBm"
                      for pos in starlink_positions],
                name="Starlink"
            ))

        if oneweb_positions:
            fig_3d.add_trace(go.Scatter3d(
                x=[pos['x'] for pos in oneweb_positions],
                y=[pos['y'] for pos in oneweb_positions],
                z=[pos['z'] for pos in oneweb_positions],
                mode='markers',
                marker=dict(
                    size=[10 if pos['visible'] else 5 for pos in oneweb_positions],
                    color=['blue' if pos['visible'] else 'lightblue' for pos in oneweb_positions],
                    symbol='square'
                ),
                text=[f"{pos['id']}<br>仰角: {pos['elevation']:.1f}°<br>RSRP: {pos['rsrp']:.1f}dBm"
                      for pos in oneweb_positions],
                name="OneWeb"
            ))

        fig_3d.update_layout(
            title=f"🌍 即時衛星追蹤 - {current_time:.1f} 分鐘",
            scene=dict(
                xaxis_title='X (km)', yaxis_title='Y (km)', zaxis_title='Z (km)',
                aspectmode='cube',
                camera=dict(
                    eye=dict(x=1.5, y=1.5, z=1.5)
                )
            ),
            showlegend=True,
            margin=dict(l=0, r=0, t=50, b=0)
        )

        # 時間顯示
        time_display = f"{int(current_time)} 分 {int((current_time % 1) * 60)} 秒"

        # 衛星池狀態
        visible_starlink = sum(1 for pos in starlink_positions if pos['visible'])
        visible_oneweb = sum(1 for pos in oneweb_positions if pos['visible'])

        pool_status = html.Div([
            dbc.Alert([
                html.H5(f"🔴 Starlink: {visible_starlink}/15", className="mb-1"),
                html.Small("目標: 10-15顆 (5°門檻)")
            ], color="danger" if visible_starlink < 10 or visible_starlink > 15 else "success"),

            dbc.Alert([
                html.H5(f"🔵 OneWeb: {visible_oneweb}/6", className="mb-1"),
                html.Small("目標: 3-6顆 (10°門檻)")
            ], color="danger" if visible_oneweb < 3 or visible_oneweb > 6 else "success")
        ])

        # 換手事件模擬
        handover_events = []
        if int(current_time) % 10 == 0 and (current_time % 1) < 0.1:  # 每10分鐘觸發
            handover_events.append(
                dbc.Alert([
                    html.Strong("🚨 A4事件"),
                    html.Br(),
                    f"STARLINK-{np.random.randint(1,10)} 信號超過門檻",
                    html.Br(),
                    html.Small(f"時間: {time_display}")
                ], color="warning", dismissable=True)
            )

        handover_alerts = html.Div(handover_events)

        # 信號品質圖 (最近的10分鐘歷史)
        time_history = np.linspace(max(0, current_time-10), current_time, 20)
        fig_signal = go.Figure()

        for i, sat in enumerate(animator.satellites[:5]):  # 只顯示前5個衛星
            rsrp_history = []
            for t in time_history:
                time_in_orbit = t % sat['orbital_period']
                time_idx = int((time_in_orbit / sat['orbital_period']) * len(sat['rsrp']))
                time_idx = min(time_idx, len(sat['rsrp']) - 1)
                rsrp_history.append(sat['rsrp'][time_idx])

            fig_signal.add_trace(go.Scatter(
                x=time_history, y=rsrp_history,
                mode='lines+markers',
                name=sat['id'],
                line=dict(color=sat['color'])
            ))

        fig_signal.add_hline(y=-100, line_dash="dash", line_color="red",
                            annotation_text="換手門檻")
        fig_signal.update_layout(
            title="📶 即時RSRP變化",
            xaxis_title="時間 (分鐘)",
            yaxis_title="RSRP (dBm)",
            margin=dict(l=50, r=20, t=50, b=40)
        )

        # 仰角圖
        fig_elevation = go.Figure()

        for i, sat in enumerate(animator.satellites[:5]):
            elevation_history = []
            for t in time_history:
                time_in_orbit = t % sat['orbital_period']
                time_idx = int((time_in_orbit / sat['orbital_period']) * len(sat['elevations']))
                time_idx = min(time_idx, len(sat['elevations']) - 1)
                elevation_history.append(sat['elevations'][time_idx])

            fig_elevation.add_trace(go.Scatter(
                x=time_history, y=elevation_history,
                mode='lines+markers',
                name=sat['id'],
                line=dict(color=sat['color'])
            ))

        fig_elevation.add_hline(y=5, line_dash="dash", line_color="red",
                               annotation_text="Starlink門檻")
        fig_elevation.add_hline(y=10, line_dash="dash", line_color="blue",
                               annotation_text="OneWeb門檻")
        fig_elevation.update_layout(
            title="📐 即時仰角變化",
            xaxis_title="時間 (分鐘)",
            yaxis_title="仰角 (度)",
            margin=dict(l=50, r=20, t=50, b=40)
        )

        return fig_3d, time_display, pool_status, handover_alerts, fig_signal, fig_elevation

    except Exception as e:
        # 錯誤處理 - 返回空圖表和錯誤信息
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"動畫錯誤: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )

        error_msg = f"❌ 錯誤: {str(e)}"
        empty_div = html.Div("暫無數據")

        return error_fig, error_msg, empty_div, empty_div, error_fig, error_fig

if __name__ == '__main__':
    print("🚀 啟動動態衛星動畫展示...")
    print("📱 瀏覽器訪問: http://localhost:8050")
    print("   或者外部訪問: http://your-server-ip:8050")
    print("\n🎬 動畫特色:")
    print("  ✨ 真實移動的衛星標記")
    print("  🌍 3D地球背景")
    print("  ⏯️ 播放/暫停/速度控制")
    print("  📊 即時信號品質監控")
    print("  🚨 動態換手事件提醒")
    print("  🎯 即時衛星池狀態")

    app.run(debug=False, host='0.0.0.0', port=8050)