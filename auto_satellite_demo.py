#!/usr/bin/env python3
"""
自動播放的衛星動畫演示 - 無需手動點擊播放
"""

import dash
from dash import dcc, html, Input, Output, callback
import plotly.graph_objects as go
import numpy as np
import time

# 創建 Dash 應用
app = dash.Dash(__name__)

# 應用布局
app.layout = html.Div([
    html.H1("🛰️ 自動播放衛星動畫", className="text-center mb-4"),

    # 狀態顯示
    html.Div([
        html.H3("▶️ 動畫正在播放中...", id="status-display", className="text-center text-success"),
        html.Div(id="time-display", className="text-center mb-3")
    ]),

    # 3D 圖表
    dcc.Graph(id="satellite-plot", style={'height': '600px'}),

    # 自動更新組件 - 每500ms更新一次，更流暢
    dcc.Interval(
        id='interval-component',
        interval=500,  # 0.5秒更新一次
        n_intervals=0,
        disabled=False
    ),

    # 控制面板
    html.Div([
        html.Button("⏸️ 暫停", id="pause-btn", className="btn btn-warning me-2"),
        html.Button("▶️ 播放", id="play-btn", className="btn btn-success me-2"),
        html.Button("🔄 重置", id="reset-btn", className="btn btn-secondary me-2"),
        html.Label("速度:", className="me-2"),
        dcc.Slider(id="speed-slider", min=0.1, max=3.0, step=0.1, value=1.0,
                  marks={0.5: '0.5x', 1.0: '1.0x', 2.0: '2.0x', 3.0: '3.0x'})
    ], className="text-center mt-3"),

    # 存儲動畫狀態
    dcc.Store(id='animation-state', data={
        'is_playing': True,  # 預設為播放狀態
        'start_time': time.time(),
        'speed': 1.0
    })
])

# 生成衛星軌道數據
def generate_satellite_data():
    satellites = []

    # Starlink 衛星 (較低軌道)
    for i in range(6):
        satellites.append({
            'name': f'STARLINK-{i+1}',
            'constellation': 'starlink',
            'radius': 1.3 + 0.1 * np.random.random(),
            'inclination': 53 + 5 * np.random.random(),
            'phase': i * 60,  # 度
            'color': 'red',
            'speed': 1.0 + 0.2 * np.random.random()
        })

    # OneWeb 衛星 (較高軌道)
    for i in range(4):
        satellites.append({
            'name': f'ONEWEB-{i+1}',
            'constellation': 'oneweb',
            'radius': 1.6 + 0.1 * np.random.random(),
            'inclination': 87 + 3 * np.random.random(),
            'phase': i * 90,  # 度
            'color': 'blue',
            'speed': 0.8 + 0.1 * np.random.random()
        })

    return satellites

satellites = generate_satellite_data()

# 控制按鈕回調
@app.callback(
    [Output('animation-state', 'data'),
     Output('status-display', 'children')],
    [Input('play-btn', 'n_clicks'),
     Input('pause-btn', 'n_clicks'),
     Input('reset-btn', 'n_clicks'),
     Input('speed-slider', 'value')],
    prevent_initial_call=True
)
def control_animation(play_clicks, pause_clicks, reset_clicks, speed):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update, dash.no_update

    trigger_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_time = time.time()

    if trigger_id == 'play-btn':
        return {
            'is_playing': True,
            'start_time': current_time,
            'speed': speed
        }, "▶️ 動畫正在播放中..."
    elif trigger_id == 'pause-btn':
        return {
            'is_playing': False,
            'start_time': current_time,
            'speed': speed
        }, "⏸️ 動畫已暫停"
    elif trigger_id == 'reset-btn':
        return {
            'is_playing': True,
            'start_time': current_time,
            'speed': speed
        }, "🔄 動畫已重置並播放"
    elif trigger_id == 'speed-slider':
        return {
            'is_playing': True,
            'start_time': current_time,
            'speed': speed
        }, f"⚡ 播放速度: {speed}x"

    return dash.no_update, dash.no_update

# 主要動畫回調
@app.callback(
    [Output('satellite-plot', 'figure'),
     Output('time-display', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('animation-state', 'data')]
)
def update_animation(n_intervals, state):
    try:
        # 計算動畫時間
        if state.get('is_playing', True):
            elapsed = time.time() - state.get('start_time', time.time())
            animation_time = elapsed * state.get('speed', 1.0)
        else:
            animation_time = 0

        # 創建地球
        u = np.linspace(0, 2 * np.pi, 30)
        v = np.linspace(0, np.pi, 30)
        x_earth = np.outer(np.cos(u), np.sin(v))
        y_earth = np.outer(np.sin(u), np.sin(v))
        z_earth = np.outer(np.ones(np.size(u)), np.cos(v))

        # 創建圖形
        fig = go.Figure()

        # 添加地球
        fig.add_trace(go.Surface(
            x=x_earth, y=y_earth, z=z_earth,
            colorscale=[[0, 'lightblue'], [0.5, 'lightgreen'], [1, 'darkgreen']],
            showscale=False,
            name='地球',
            opacity=0.8
        ))

        # 添加衛星
        starlink_count = 0
        oneweb_count = 0

        for sat in satellites:
            # 計算當前位置
            time_factor = animation_time * 0.1 * sat['speed']

            # 軌道角度
            orbit_angle = time_factor + np.radians(sat['phase'])
            inclination_rad = np.radians(sat['inclination'])

            # 3D 位置計算
            x = sat['radius'] * np.cos(orbit_angle) * np.cos(inclination_rad)
            y = sat['radius'] * np.sin(orbit_angle) * np.cos(inclination_rad)
            z = sat['radius'] * np.sin(inclination_rad) * np.sin(orbit_angle * 0.5)

            # 添加衛星標記
            fig.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[z],
                mode='markers',
                marker=dict(
                    size=10,
                    color=sat['color'],
                    symbol='diamond' if sat['constellation'] == 'starlink' else 'circle'
                ),
                name=sat['name'],
                text=f"{sat['name']}<br>高度: {sat['radius']:.2f}<br>傾角: {sat['inclination']:.1f}°",
                hoverinfo='text'
            ))

            # 統計可見衛星
            elevation = np.degrees(np.arcsin(z / sat['radius']))
            if elevation > 5:  # 仰角大於5度視為可見
                if sat['constellation'] == 'starlink':
                    starlink_count += 1
                else:
                    oneweb_count += 1

            # 添加軌道軌跡
            theta_orbit = np.linspace(0, 2*np.pi, 100)
            x_orbit = sat['radius'] * np.cos(theta_orbit) * np.cos(inclination_rad)
            y_orbit = sat['radius'] * np.sin(theta_orbit) * np.cos(inclination_rad)
            z_orbit = sat['radius'] * np.sin(inclination_rad) * np.sin(theta_orbit * 0.5)

            fig.add_trace(go.Scatter3d(
                x=x_orbit, y=y_orbit, z=z_orbit,
                mode='lines',
                line=dict(color=sat['color'], width=1),
                showlegend=False,
                opacity=0.3
            ))

        # 設置布局
        fig.update_layout(
            title=dict(
                text=f"🛰️ LEO 衛星動態池規劃<br>🔴 Starlink: {starlink_count} | 🔵 OneWeb: {oneweb_count}",
                x=0.5,
                font=dict(size=16)
            ),
            scene=dict(
                xaxis_title="X (地球半徑)",
                yaxis_title="Y (地球半徑)",
                zaxis_title="Z (地球半徑)",
                camera=dict(
                    eye=dict(x=2.5, y=2.5, z=1.5)
                ),
                aspectmode='cube'
            ),
            showlegend=True,
            height=600,
            legend=dict(
                orientation="h",
                yanchor="bottom",
                y=1.02,
                xanchor="right",
                x=1
            )
        )

        # 時間顯示
        minutes = int(animation_time / 60)
        seconds = int(animation_time % 60)
        time_text = f"⏰ 軌道時間: {minutes:02d}:{seconds:02d} | 速度: {state.get('speed', 1.0)}x"

        return fig, time_text

    except Exception as e:
        # 錯誤處理
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"動畫錯誤: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False,
            font=dict(size=16, color="red")
        )
        error_fig.update_layout(height=600)

        return error_fig, f"❌ 錯誤: {str(e)}"

if __name__ == '__main__':
    print("🚀 啟動自動播放衛星動畫...")
    print("📱 訪問: http://localhost:8050")
    print("✨ 動畫將自動開始播放，無需手動點擊")
    print("🎮 可以使用控制面板調整播放狀態和速度")

    app.run(debug=True, host='0.0.0.0', port=8050)