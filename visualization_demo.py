#!/usr/bin/env python3
"""
衛星可視化展示範例
使用 plotly + dash 建立互動式衛星軌道和換手事件視覺化

基於推薦套件：plotly, dash, numpy, pandas
模擬衛星池規劃和3GPP換手事件的前端展示效果
"""

import numpy as np
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from plotly.subplots import make_subplots
import dash
from dash import dcc, html, Input, Output, dash_table
from datetime import datetime, timedelta
import math

# 模擬數據生成
def generate_satellite_orbits():
    """生成模擬的衛星軌道數據"""
    satellites = []

    # Starlink 模擬數據 (550km軌道)
    for i in range(15):
        time_points = np.linspace(0, 95, 95)  # 95分鐘軌道週期

        # 模擬軌道參數
        inclination = 53.0 + np.random.normal(0, 2)  # 軌道傾角
        raan = i * 24 + np.random.normal(0, 5)      # 升交點赤經

        # 計算軌道位置 (簡化模型)
        radius = 6371 + 550  # 地球半徑 + 高度

        x = []
        y = []
        z = []
        lat = []
        lon = []
        elevation = []
        rsrp = []

        for t in time_points:
            # 簡化的軌道計算
            angle = t * 2 * np.pi / 95  # 軌道角度

            # 3D 座標
            x_pos = radius * np.cos(angle) * np.cos(np.radians(inclination))
            y_pos = radius * np.sin(angle) * np.cos(np.radians(inclination))
            z_pos = radius * np.sin(np.radians(inclination)) * np.sin(angle)

            x.append(x_pos)
            y.append(y_pos)
            z.append(z_pos)

            # 轉換為地理座標 (簡化)
            lat_pos = np.degrees(np.arcsin(z_pos / radius))
            lon_pos = np.degrees(np.arctan2(y_pos, x_pos))

            lat.append(lat_pos)
            lon.append(lon_pos)

            # 計算相對NTPU的仰角 (簡化)
            ntpu_lat, ntpu_lon = 24.9464, 121.3706
            distance = np.sqrt((lat_pos - ntpu_lat)**2 + (lon_pos - ntpu_lon)**2)
            elev = max(0, 90 - distance * 10)  # 簡化仰角計算
            elevation.append(elev)

            # 模擬RSRP (基於仰角)
            rsrp_val = -70 - (90 - elev) * 0.5 + np.random.normal(0, 3)
            rsrp.append(rsrp_val)

        satellites.append({
            'id': f'STARLINK-{i+1}',
            'constellation': 'Starlink',
            'x': x, 'y': y, 'z': z,
            'lat': lat, 'lon': lon,
            'elevation': elevation,
            'rsrp': rsrp,
            'time': time_points
        })

    # OneWeb 模擬數據 (1200km軌道，較少衛星)
    for i in range(6):
        time_points = np.linspace(0, 115, 115)  # 115分鐘軌道週期

        inclination = 87.9 + np.random.normal(0, 1)  # 極軌道
        raan = i * 60 + np.random.normal(0, 5)

        radius = 6371 + 1200  # 更高軌道

        x, y, z, lat, lon, elevation, rsrp = [], [], [], [], [], [], []

        for t in time_points:
            angle = t * 2 * np.pi / 115

            x_pos = radius * np.cos(angle) * np.cos(np.radians(inclination))
            y_pos = radius * np.sin(angle) * np.cos(np.radians(inclination))
            z_pos = radius * np.sin(np.radians(inclination)) * np.sin(angle)

            x.append(x_pos)
            y.append(y_pos)
            z.append(z_pos)

            lat_pos = np.degrees(np.arcsin(z_pos / radius))
            lon_pos = np.degrees(np.arctan2(y_pos, x_pos))

            lat.append(lat_pos)
            lon.append(lon_pos)

            # OneWeb 使用10度仰角門檻
            ntpu_lat, ntpu_lon = 24.9464, 121.3706
            distance = np.sqrt((lat_pos - ntpu_lat)**2 + (lon_pos - ntpu_lon)**2)
            elev = max(0, 90 - distance * 8)  # 不同的仰角計算
            elevation.append(elev)

            rsrp_val = -75 - (90 - elev) * 0.3 + np.random.normal(0, 2)
            rsrp.append(rsrp_val)

        satellites.append({
            'id': f'ONEWEB-{i+1}',
            'constellation': 'OneWeb',
            'x': x, 'y': y, 'z': z,
            'lat': lat, 'lon': lon,
            'elevation': elevation,
            'rsrp': rsrp,
            'time': time_points
        })

    return satellites

def generate_handover_events():
    """生成3GPP換手事件數據"""
    events = []
    current_time = datetime.now()

    event_types = ['A4', 'A5', 'D2']
    constellations = ['Starlink', 'OneWeb']

    for i in range(50):
        event = {
            'timestamp': current_time + timedelta(minutes=i*2),
            'event_type': np.random.choice(event_types),
            'serving_satellite': f'{np.random.choice(constellations)}-{np.random.randint(1,10)}',
            'target_satellite': f'{np.random.choice(constellations)}-{np.random.randint(1,10)}',
            'rsrp_serving': np.random.normal(-85, 10),
            'rsrp_target': np.random.normal(-80, 8),
            'distance_km': np.random.uniform(800, 2000),
            'decision': np.random.choice(['Accept', 'Reject', 'Pending'])
        }
        events.append(event)

    return pd.DataFrame(events)

# 生成模擬數據
satellites_data = generate_satellite_orbits()
handover_events = generate_handover_events()

# 建立 Dash 應用
app = dash.Dash(__name__)

app.layout = html.Div([
    html.H1("🛰️ LEO衛星時空錯置動態池規劃視覺化",
            style={'textAlign': 'center', 'color': '#2c3e50'}),

    # 控制面板
    html.Div([
        html.Div([
            html.Label("選擇星座:"),
            dcc.Dropdown(
                id='constellation-dropdown',
                options=[
                    {'label': '全部', 'value': 'all'},
                    {'label': 'Starlink', 'value': 'Starlink'},
                    {'label': 'OneWeb', 'value': 'OneWeb'}
                ],
                value='all'
            )
        ], style={'width': '30%', 'display': 'inline-block'}),

        html.Div([
            html.Label("時間點 (分鐘):"),
            dcc.Slider(
                id='time-slider',
                min=0, max=115, step=1, value=0,
                marks={i: str(i) for i in range(0, 116, 20)},
                tooltip={"placement": "bottom", "always_visible": True}
            )
        ], style={'width': '65%', 'float': 'right', 'display': 'inline-block'})
    ], style={'margin': '20px'}),

    # 主要圖表區域
    html.Div([
        # 3D 軌道視覺化
        html.Div([
            dcc.Graph(id='3d-orbit-plot')
        ], style={'width': '50%', 'display': 'inline-block'}),

        # 地面投影圖
        html.Div([
            dcc.Graph(id='ground-track-plot')
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),

    # 衛星池狀態
    html.Div([
        html.H3("🎯 當前衛星池狀態"),
        html.Div(id='satellite-pool-status'),
    ], style={'margin': '20px', 'padding': '20px', 'backgroundColor': '#f8f9fa'}),

    # 信號品質圖表
    html.Div([
        html.Div([
            dcc.Graph(id='rsrp-timeline')
        ], style={'width': '50%', 'display': 'inline-block'}),

        html.Div([
            dcc.Graph(id='elevation-plot')
        ], style={'width': '50%', 'display': 'inline-block'})
    ]),

    # 3GPP換手事件表
    html.Div([
        html.H3("📡 3GPP 換手事件監控"),
        dash_table.DataTable(
            id='handover-events-table',
            data=handover_events.head(10).to_dict('records'),
            columns=[
                {'name': '時間', 'id': 'timestamp'},
                {'name': '事件類型', 'id': 'event_type'},
                {'name': '服務衛星', 'id': 'serving_satellite'},
                {'name': '目標衛星', 'id': 'target_satellite'},
                {'name': 'RSRP服務', 'id': 'rsrp_serving'},
                {'name': 'RSRP目標', 'id': 'rsrp_target'},
                {'name': '決策', 'id': 'decision'}
            ],
            style_cell={'textAlign': 'center'},
            style_data_conditional=[
                {
                    'if': {'filter_query': '{decision} = Accept'},
                    'backgroundColor': '#d4edda',
                    'color': 'black',
                },
                {
                    'if': {'filter_query': '{decision} = Reject'},
                    'backgroundColor': '#f8d7da',
                    'color': 'black',
                }
            ]
        )
    ], style={'margin': '20px'})
])

# 回調函數
@app.callback(
    [Output('3d-orbit-plot', 'figure'),
     Output('ground-track-plot', 'figure'),
     Output('satellite-pool-status', 'children'),
     Output('rsrp-timeline', 'figure'),
     Output('elevation-plot', 'figure')],
    [Input('constellation-dropdown', 'value'),
     Input('time-slider', 'value')]
)
def update_plots(selected_constellation, time_point):
    # 篩選數據
    filtered_sats = satellites_data
    if selected_constellation != 'all':
        filtered_sats = [s for s in satellites_data if s['constellation'] == selected_constellation]

    # 3D軌道圖
    fig_3d = go.Figure()

    # 添加地球
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)
    earth_x = 6371 * np.outer(np.cos(u), np.sin(v))
    earth_y = 6371 * np.outer(np.sin(u), np.sin(v))
    earth_z = 6371 * np.outer(np.ones(np.size(u)), np.cos(v))

    fig_3d.add_trace(go.Surface(
        x=earth_x, y=earth_y, z=earth_z,
        colorscale='Blues', opacity=0.6, showscale=False
    ))

    # 添加衛星軌道
    colors = {'Starlink': 'red', 'OneWeb': 'blue'}
    for sat in filtered_sats:
        color = colors[sat['constellation']]
        fig_3d.add_trace(go.Scatter3d(
            x=sat['x'], y=sat['y'], z=sat['z'],
            mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=3),
            name=sat['id']
        ))

        # 當前位置標記
        if time_point < len(sat['x']):
            fig_3d.add_trace(go.Scatter3d(
                x=[sat['x'][time_point]], y=[sat['y'][time_point]], z=[sat['z'][time_point]],
                mode='markers',
                marker=dict(size=8, color=color, symbol='diamond'),
                name=f"{sat['id']} 當前位置"
            ))

    fig_3d.update_layout(
        title="🌍 3D 衛星軌道視覺化",
        scene=dict(
            xaxis_title='X (km)', yaxis_title='Y (km)', zaxis_title='Z (km)',
            aspectmode='cube'
        ),
        showlegend=False
    )

    # 地面軌跡圖
    fig_ground = go.Figure()

    for sat in filtered_sats:
        color = colors[sat['constellation']]
        fig_ground.add_trace(go.Scattergeo(
            lon=sat['lon'], lat=sat['lat'],
            mode='lines+markers',
            line=dict(color=color, width=2),
            marker=dict(size=3),
            name=sat['id']
        ))

        # 當前位置
        if time_point < len(sat['lat']):
            fig_ground.add_trace(go.Scattergeo(
                lon=[sat['lon'][time_point]], lat=[sat['lat'][time_point]],
                mode='markers',
                marker=dict(size=10, color=color, symbol='diamond'),
                name=f"{sat['id']} 當前"
            ))

    # NTPU位置
    fig_ground.add_trace(go.Scattergeo(
        lon=[121.3706], lat=[24.9464],
        mode='markers',
        marker=dict(size=15, color='green', symbol='star'),
        name='NTPU'
    ))

    fig_ground.update_layout(
        title="🗺️ 衛星地面軌跡",
        geo=dict(showland=True, landcolor='lightgray')
    )

    # 衛星池狀態統計
    visible_starlink = sum(1 for s in filtered_sats
                          if s['constellation'] == 'Starlink' and
                          time_point < len(s['elevation']) and
                          s['elevation'][time_point] > 5)

    visible_oneweb = sum(1 for s in filtered_sats
                        if s['constellation'] == 'OneWeb' and
                        time_point < len(s['elevation']) and
                        s['elevation'][time_point] > 10)

    pool_status = html.Div([
        html.Div([
            html.H4(f"Starlink: {visible_starlink}/15", style={'color': 'red'}),
            html.P("目標: 10-15顆可見 (5°門檻)")
        ], style={'width': '45%', 'display': 'inline-block', 'textAlign': 'center'}),

        html.Div([
            html.H4(f"OneWeb: {visible_oneweb}/6", style={'color': 'blue'}),
            html.P("目標: 3-6顆可見 (10°門檻)")
        ], style={'width': '45%', 'display': 'inline-block', 'textAlign': 'center'})
    ])

    # RSRP時間線圖
    fig_rsrp = go.Figure()
    for sat in filtered_sats[:5]:  # 只顯示前5個衛星避免過於擁擠
        fig_rsrp.add_trace(go.Scatter(
            x=sat['time'], y=sat['rsrp'],
            mode='lines',
            name=sat['id'],
            line=dict(color=colors[sat['constellation']])
        ))

    fig_rsrp.update_layout(
        title="📶 RSRP信號強度時序圖",
        xaxis_title="時間 (分鐘)",
        yaxis_title="RSRP (dBm)"
    )

    # 仰角圖
    fig_elev = go.Figure()
    for sat in filtered_sats[:5]:
        fig_elev.add_trace(go.Scatter(
            x=sat['time'], y=sat['elevation'],
            mode='lines',
            name=sat['id'],
            line=dict(color=colors[sat['constellation']])
        ))

    # 添加門檻線
    fig_elev.add_hline(y=5, line_dash="dash", line_color="red",
                       annotation_text="Starlink門檻(5°)")
    fig_elev.add_hline(y=10, line_dash="dash", line_color="blue",
                       annotation_text="OneWeb門檻(10°)")

    fig_elev.update_layout(
        title="📐 衛星仰角變化",
        xaxis_title="時間 (分鐘)",
        yaxis_title="仰角 (度)"
    )

    return fig_3d, fig_ground, pool_status, fig_rsrp, fig_elev

if __name__ == '__main__':
    print("🚀 啟動衛星可視化展示...")
    print("📱 請開啟瀏覽器訪問: http://127.0.0.1:8050")
    print("\n✨ 展示功能:")
    print("  - 3D衛星軌道視覺化")
    print("  - 地面軌跡投影")
    print("  - 動態衛星池狀態")
    print("  - RSRP/仰角時序圖")
    print("  - 3GPP換手事件監控")

    app.run(debug=True, host='0.0.0.0', port=8050)