#!/usr/bin/env python3
"""
簡化的衛星動畫演示 - 修復 updating 問題
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
    html.H1("🛰️ 簡化衛星動畫演示", className="text-center mb-4"),

    # 控制面板
    html.Div([
        html.Button("▶️ 播放", id="play-btn", className="btn btn-success me-2"),
        html.Button("⏸️ 暫停", id="pause-btn", className="btn btn-warning me-2"),
        html.Button("🔄 重置", id="reset-btn", className="btn btn-secondary"),
    ], className="text-center mb-3"),

    # 時間顯示
    html.Div(id="time-display", className="text-center mb-3"),

    # 3D 圖表
    dcc.Graph(id="satellite-plot", style={'height': '600px'}),

    # 自動更新組件
    dcc.Interval(
        id='interval-component',
        interval=1000,  # 1秒更新一次
        n_intervals=0,
        disabled=False
    ),

    # 存儲動畫狀態
    dcc.Store(id='animation-state', data={
        'is_playing': False,
        'current_time': 0,
        'start_time': time.time()
    })
])

# 生成簡單的衛星軌道數據
def generate_simple_orbit(n_satellites=8):
    satellites = []
    for i in range(n_satellites):
        # 創建簡單的圓形軌道
        theta = np.linspace(0, 2*np.pi, 100)
        radius = 1.2 + 0.2 * np.sin(i)  # 不同高度

        # 軌道參數
        phase_offset = i * (2*np.pi / n_satellites)

        satellites.append({
            'name': f'SAT-{i+1:02d}',
            'theta': theta,
            'radius': radius,
            'phase_offset': phase_offset,
            'color': f'hsl({i*45}, 70%, 50%)'
        })

    return satellites

satellites = generate_simple_orbit()

# 控制狀態回調
@app.callback(
    Output('animation-state', 'data'),
    [Input('play-btn', 'n_clicks'),
     Input('pause-btn', 'n_clicks'),
     Input('reset-btn', 'n_clicks')],
    prevent_initial_call=True
)
def control_animation(play_clicks, pause_clicks, reset_clicks):
    ctx = dash.callback_context
    if not ctx.triggered:
        return dash.no_update

    button_id = ctx.triggered[0]['prop_id'].split('.')[0]
    current_time = time.time()

    if button_id == 'play-btn':
        return {
            'is_playing': True,
            'current_time': 0,
            'start_time': current_time
        }
    elif button_id == 'pause-btn':
        return {
            'is_playing': False,
            'current_time': 0,
            'start_time': current_time
        }
    elif button_id == 'reset-btn':
        return {
            'is_playing': False,
            'current_time': 0,
            'start_time': current_time
        }

    return dash.no_update

# 主要動畫回調
@app.callback(
    [Output('satellite-plot', 'figure'),
     Output('time-display', 'children')],
    [Input('interval-component', 'n_intervals'),
     Input('animation-state', 'data')]
)
def update_animation(n_intervals, state):
    try:
        # 計算當前時間
        if state['is_playing']:
            elapsed_time = time.time() - state['start_time']
            current_time = state['current_time'] + elapsed_time
        else:
            current_time = state['current_time']

        # 創建地球
        u = np.linspace(0, 2 * np.pi, 50)
        v = np.linspace(0, np.pi, 50)
        x_earth = np.outer(np.cos(u), np.sin(v))
        y_earth = np.outer(np.sin(u), np.sin(v))
        z_earth = np.outer(np.ones(np.size(u)), np.cos(v))

        # 創建圖形
        fig = go.Figure()

        # 添加地球
        fig.add_trace(go.Surface(
            x=x_earth, y=y_earth, z=z_earth,
            colorscale=[[0, 'lightblue'], [1, 'lightgreen']],
            showscale=False,
            name='地球'
        ))

        # 添加衛星
        for sat in satellites:
            # 計算當前位置
            time_factor = current_time * 0.1  # 控制速度
            current_angle = time_factor + sat['phase_offset']

            # 衛星位置
            x = sat['radius'] * np.cos(current_angle)
            y = sat['radius'] * np.sin(current_angle)
            z = 0.3 * np.sin(current_angle * 2)  # 添加一些z軸變化

            # 添加衛星標記
            fig.add_trace(go.Scatter3d(
                x=[x], y=[y], z=[z],
                mode='markers',
                marker=dict(size=8, color=sat['color']),
                name=sat['name'],
                text=sat['name']
            ))

            # 添加軌道軌跡
            orbit_x = sat['radius'] * np.cos(sat['theta'])
            orbit_y = sat['radius'] * np.sin(sat['theta'])
            orbit_z = 0.3 * np.sin(sat['theta'] * 2)

            fig.add_trace(go.Scatter3d(
                x=orbit_x, y=orbit_y, z=orbit_z,
                mode='lines',
                line=dict(color=sat['color'], width=2),
                showlegend=False,
                opacity=0.3
            ))

        # 設置布局
        fig.update_layout(
            title="🛰️ 實時衛星軌道動畫",
            scene=dict(
                xaxis_title="X",
                yaxis_title="Y",
                zaxis_title="Z",
                camera=dict(
                    eye=dict(x=2, y=2, z=1)
                ),
                aspectmode='cube'
            ),
            showlegend=True,
            height=600
        )

        # 時間顯示
        time_text = f"⏰ 動畫時間: {current_time:.1f}s | 狀態: {'▶️ 播放中' if state['is_playing'] else '⏸️ 已暫停'}"

        return fig, time_text

    except Exception as e:
        # 錯誤處理
        error_fig = go.Figure()
        error_fig.add_annotation(
            text=f"動畫錯誤: {str(e)}",
            xref="paper", yref="paper",
            x=0.5, y=0.5, showarrow=False
        )
        return error_fig, f"錯誤: {str(e)}"

if __name__ == '__main__':
    print("🚀 啟動簡化衛星動畫...")
    print("📱 訪問: http://localhost:8091")
    print("🔧 這個版本專門修復 updating 問題")

    app.run(debug=True, host='0.0.0.0', port=8091)