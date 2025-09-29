#!/usr/bin/env python3
"""
LEO衛星視覺化Web伺服器
可透過IP直接訪問的Dash應用
"""

import dash
from dash import dcc, html
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# NTPU座標
NTPU_LAT = 24.9442
NTPU_LON = 121.3711

app = dash.Dash(__name__)

def create_3d_visualization():
    """創建3D衛星視覺化"""
    fig = go.Figure()

    # 地球
    u = np.linspace(0, 2 * np.pi, 30)
    v = np.linspace(0, np.pi, 30)
    r = 6371
    x = r * np.outer(np.cos(u), np.sin(v))
    y = r * np.outer(np.sin(u), np.sin(v))
    z = r * np.outer(np.ones(np.size(u)), np.cos(v))

    fig.add_trace(go.Surface(
        x=x, y=y, z=z,
        colorscale='Blues',
        showscale=False,
        opacity=0.5
    ))

    # 模擬Starlink衛星
    np.random.seed(42)
    for i in range(10):
        altitude = 550 + r
        t = np.linspace(0, 2*np.pi, 90)
        inclination = 53 + np.random.uniform(-2, 2)

        x_orbit = altitude * np.cos(t) * np.cos(np.radians(inclination))
        y_orbit = altitude * np.sin(t) * np.cos(np.radians(inclination))
        z_orbit = altitude * np.sin(np.radians(inclination)) * np.sin(t)

        # 旋轉軌道
        rotation = np.radians(i * 36)
        x_rot = x_orbit * np.cos(rotation) - y_orbit * np.sin(rotation)
        y_rot = x_orbit * np.sin(rotation) + y_orbit * np.cos(rotation)

        fig.add_trace(go.Scatter3d(
            x=x_rot, y=y_rot, z=z_orbit,
            mode='lines',
            line=dict(color='green', width=1),
            showlegend=False
        ))

        # 衛星當前位置
        pos = np.random.randint(0, 90)
        fig.add_trace(go.Scatter3d(
            x=[x_rot[pos]], y=[y_rot[pos]], z=[z_orbit[pos]],
            mode='markers',
            marker=dict(size=5, color='green'),
            name=f'Starlink-{i+1}'
        ))

    # NTPU位置
    x_ntpu = r * np.cos(np.radians(NTPU_LAT)) * np.cos(np.radians(NTPU_LON))
    y_ntpu = r * np.cos(np.radians(NTPU_LAT)) * np.sin(np.radians(NTPU_LON))
    z_ntpu = r * np.sin(np.radians(NTPU_LAT))

    fig.add_trace(go.Scatter3d(
        x=[x_ntpu], y=[y_ntpu], z=[z_ntpu],
        mode='markers+text',
        marker=dict(size=10, color='red', symbol='diamond'),
        text=['NTPU'],
        name='NTPU'
    ))

    fig.update_layout(
        title='🛰️ LEO衛星3D即時視覺化',
        scene=dict(
            xaxis=dict(showgrid=False, showticklabels=False),
            yaxis=dict(showgrid=False, showticklabels=False),
            zaxis=dict(showgrid=False, showticklabels=False)
        ),
        height=600
    )

    return fig

def create_dashboard():
    """創建儀表板"""
    times = pd.date_range(start='2025-01-29 12:00', periods=60, freq='1min')

    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=('衛星池狀態', 'RSRP信號', '換手事件', '仰角分布')
    )

    # 衛星池
    starlink = 12 + 2*np.sin(np.linspace(0, 4*np.pi, 60)) + np.random.normal(0, 0.5, 60)
    oneweb = 4 + 1.5*np.sin(np.linspace(0, 3*np.pi, 60)) + np.random.normal(0, 0.3, 60)

    fig.add_trace(go.Scatter(x=times, y=starlink, name='Starlink',
                            line=dict(color='green')), row=1, col=1)
    fig.add_trace(go.Scatter(x=times, y=oneweb, name='OneWeb',
                            line=dict(color='blue')), row=1, col=1)

    # RSRP
    rsrp = -80 + 10*np.sin(np.linspace(0, 4*np.pi, 60)) + np.random.normal(0, 3, 60)
    fig.add_trace(go.Scatter(x=times, y=rsrp, name='RSRP',
                            line=dict(color='purple')), row=1, col=2)

    # 換手事件
    events = np.random.choice(['A4', 'A5', 'D2'], 10)
    event_times = np.random.choice(60, 10, replace=False)
    for i, (t, e) in enumerate(zip(event_times, events)):
        color = {'A4': 'yellow', 'A5': 'orange', 'D2': 'red'}[e]
        fig.add_trace(go.Scatter(x=[times[t]], y=[e],
                                mode='markers',
                                marker=dict(size=10, color=color),
                                showlegend=False), row=2, col=1)

    # 仰角分布
    fig.add_trace(go.Bar(x=['0-30°', '30-60°', '60-90°'],
                        y=[3, 8, 4], name='分布',
                        marker_color='teal'), row=2, col=2)

    fig.update_layout(height=600, showlegend=True)
    return fig

# 應用佈局
app.layout = html.Div([
    html.H1('🛰️ LEO衛星動態池視覺化系統',
            style={'text-align': 'center', 'color': '#2c3e50'}),

    html.Div([
        html.Div([
            html.H3('3D衛星軌道'),
            dcc.Graph(figure=create_3d_visualization())
        ], style={'width': '48%', 'display': 'inline-block'}),

        html.Div([
            html.H3('監控儀表板'),
            dcc.Graph(figure=create_dashboard())
        ], style={'width': '48%', 'float': 'right', 'display': 'inline-block'})
    ]),

    html.Div([
        html.H3('系統狀態', style={'text-align': 'center'}),
        html.Div([
            html.Div('🟢 Starlink池: 12/15顆',
                    style={'width': '33%', 'display': 'inline-block', 'text-align': 'center'}),
            html.Div('🔵 OneWeb池: 4/6顆',
                    style={'width': '33%', 'display': 'inline-block', 'text-align': 'center'}),
            html.Div('⚡ 換手事件: 10次/小時',
                    style={'width': '33%', 'display': 'inline-block', 'text-align': 'center'})
        ], style={'background-color': '#f0f0f0', 'padding': '20px', 'margin': '20px'})
    ])
])

if __name__ == '__main__':
    print("🚀 啟動衛星視覺化伺服器...")
    print("📡 伺服器運行在: http://120.126.151.103:8050")
    print("💡 提示: 確保防火牆允許8050埠")
    print("\n按 Ctrl+C 停止伺服器")

    # 在所有網路介面上運行，允許外部訪問
    app.run(host='0.0.0.0', port=8050, debug=False)