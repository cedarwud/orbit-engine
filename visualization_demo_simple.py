#!/usr/bin/env python3
"""
LEO衛星動態池視覺化Demo (簡化版)
使用plotly生成靜態HTML檔案，無需執行伺服器
"""

import os
import sys

# 檢查並安裝必要套件
try:
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
except ImportError:
    print("📦 安裝必要套件 plotly...")
    os.system("pip install plotly")
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots

import numpy as np
import pandas as pd
from datetime import datetime, timedelta
import webbrowser

# NTPU座標
NTPU_LAT = 24.9442  # 24°56'39"N
NTPU_LON = 121.3711  # 121°22'17"E

def create_3d_satellite_visualization():
    """創建3D衛星軌道視覺化"""

    # 創建地球網格
    u = np.linspace(0, 2 * np.pi, 50)
    v = np.linspace(0, np.pi, 50)

    earth_radius = 6371
    x = earth_radius * np.outer(np.cos(u), np.sin(v))
    y = earth_radius * np.outer(np.sin(u), np.sin(v))
    z = earth_radius * np.outer(np.ones(np.size(u)), np.cos(v))

    # 創建圖形
    fig = go.Figure()

    # 添加地球表面
    fig.add_trace(go.Surface(
        x=x, y=y, z=z,
        colorscale='Blues',
        showscale=False,
        opacity=0.5,
        name='Earth',
        hoverinfo='skip'
    ))

    # 生成Starlink衛星軌道 (550km, 15顆)
    np.random.seed(42)
    starlink_sats = []
    for i in range(15):
        # 簡化軌道參數
        inclination = 53.0 + np.random.uniform(-2, 2)
        raan = i * 24
        altitude = 550
        radius = earth_radius + altitude

        # 生成軌道點 (90分鐘週期)
        t = np.linspace(0, 2*np.pi, 90)

        # 軌道座標
        x_orbit = radius * np.cos(t) * np.cos(np.radians(inclination))
        y_orbit = radius * np.sin(t) * np.cos(np.radians(inclination))
        z_orbit = radius * np.sin(np.radians(inclination)) * np.sin(t)

        # 旋轉軌道面
        rotation = np.radians(raan)
        x_rot = x_orbit * np.cos(rotation) - y_orbit * np.sin(rotation)
        y_rot = x_orbit * np.sin(rotation) + y_orbit * np.cos(rotation)

        # 添加軌道線
        fig.add_trace(go.Scatter3d(
            x=x_rot, y=y_rot, z=z_orbit,
            mode='lines',
            line=dict(color='lightgreen', width=1),
            name=f'Starlink-{i+1}軌道',
            showlegend=False,
            hoverinfo='skip'
        ))

        # 添加當前位置衛星
        current_pos = np.random.randint(0, 90)
        fig.add_trace(go.Scatter3d(
            x=[x_rot[current_pos]],
            y=[y_rot[current_pos]],
            z=[z_orbit[current_pos]],
            mode='markers',
            marker=dict(size=6, color='green', symbol='circle'),
            name=f'Starlink-{i+1}',
            hovertext=f'Starlink-{i+1}<br>高度: 550km<br>仰角: {np.random.uniform(0,90):.1f}°',
            hoverinfo='text'
        ))

        # 計算是否可見 (簡化計算)
        sat_lat = np.degrees(np.arcsin(z_orbit[current_pos]/radius))
        sat_lon = np.degrees(np.arctan2(y_rot[current_pos], x_rot[current_pos]))
        distance = np.sqrt((sat_lat - NTPU_LAT)**2 + (sat_lon - NTPU_LON)**2)
        visible = distance < 30  # 簡化可見性判斷
        starlink_sats.append({'id': f'Starlink-{i+1}', 'visible': visible})

    # 生成OneWeb衛星軌道 (1200km, 6顆)
    oneweb_sats = []
    for i in range(6):
        inclination = 87.9  # 極軌道
        raan = i * 60
        altitude = 1200
        radius = earth_radius + altitude

        # 生成軌道點 (115分鐘週期)
        t = np.linspace(0, 2*np.pi, 115)

        x_orbit = radius * np.cos(t) * np.cos(np.radians(inclination))
        y_orbit = radius * np.sin(t) * np.cos(np.radians(inclination))
        z_orbit = radius * np.sin(np.radians(inclination)) * np.sin(t)

        rotation = np.radians(raan)
        x_rot = x_orbit * np.cos(rotation) - y_orbit * np.sin(rotation)
        y_rot = x_orbit * np.sin(rotation) + y_orbit * np.cos(rotation)

        # 添加軌道線
        fig.add_trace(go.Scatter3d(
            x=x_rot, y=y_rot, z=z_orbit,
            mode='lines',
            line=dict(color='lightblue', width=1),
            name=f'OneWeb-{i+1}軌道',
            showlegend=False,
            hoverinfo='skip'
        ))

        # 添加當前位置衛星
        current_pos = np.random.randint(0, 115)
        fig.add_trace(go.Scatter3d(
            x=[x_rot[current_pos]],
            y=[y_rot[current_pos]],
            z=[z_orbit[current_pos]],
            mode='markers',
            marker=dict(size=8, color='blue', symbol='diamond'),
            name=f'OneWeb-{i+1}',
            hovertext=f'OneWeb-{i+1}<br>高度: 1200km<br>仰角: {np.random.uniform(0,90):.1f}°',
            hoverinfo='text'
        ))

        sat_lat = np.degrees(np.arcsin(z_orbit[current_pos]/radius))
        sat_lon = np.degrees(np.arctan2(y_rot[current_pos], x_rot[current_pos]))
        distance = np.sqrt((sat_lat - NTPU_LAT)**2 + (sat_lon - NTPU_LON)**2)
        visible = distance < 40  # OneWeb覆蓋範圍更大
        oneweb_sats.append({'id': f'OneWeb-{i+1}', 'visible': visible})

    # 添加NTPU位置標記
    r = earth_radius
    x_ntpu = r * np.cos(np.radians(NTPU_LAT)) * np.cos(np.radians(NTPU_LON))
    y_ntpu = r * np.cos(np.radians(NTPU_LAT)) * np.sin(np.radians(NTPU_LON))
    z_ntpu = r * np.sin(np.radians(NTPU_LAT))

    fig.add_trace(go.Scatter3d(
        x=[x_ntpu], y=[y_ntpu], z=[z_ntpu],
        mode='markers+text',
        marker=dict(size=12, color='red', symbol='diamond'),
        text=['NTPU'],
        textposition='top center',
        name='NTPU位置',
        hovertext='國立臺北大學<br>24°56\'39"N<br>121°22\'17"E',
        hoverinfo='text'
    ))

    # 統計可見衛星
    visible_starlink = sum(1 for s in starlink_sats if s['visible'])
    visible_oneweb = sum(1 for s in oneweb_sats if s['visible'])

    # 設置佈局
    fig.update_layout(
        title=dict(
            text=f'🛰️ LEO衛星動態池3D視覺化<br>' +
                 f'<sub>Starlink可見: {visible_starlink}/15 | OneWeb可見: {visible_oneweb}/6</sub>',
            x=0.5,
            xanchor='center'
        ),
        scene=dict(
            xaxis=dict(showgrid=False, showticklabels=False, title=''),
            yaxis=dict(showgrid=False, showticklabels=False, title=''),
            zaxis=dict(showgrid=False, showticklabels=False, title=''),
            camera=dict(
                eye=dict(x=1.5, y=1.5, z=1.5)
            )
        ),
        showlegend=True,
        width=1200,
        height=800,
        template='plotly_white'
    )

    return fig, visible_starlink, visible_oneweb

def create_time_series_dashboard():
    """創建時序分析儀表板"""

    # 生成60分鐘的時間序列數據
    times = pd.date_range(start='2025-01-29 12:00', periods=60, freq='1min')

    # 創建4個子圖
    fig = make_subplots(
        rows=2, cols=2,
        subplot_titles=(
            '衛星池動態狀態',
            'RSRP信號品質',
            '3GPP換手事件',
            '衛星仰角分布'
        ),
        specs=[
            [{"secondary_y": False}, {"secondary_y": False}],
            [{"type": "scatter"}, {"type": "bar"}]
        ]
    )

    # 1. 衛星池狀態 (左上)
    starlink_pool = 12 + 2 * np.sin(np.linspace(0, 4*np.pi, 60)) + np.random.normal(0, 0.5, 60)
    starlink_pool = np.clip(starlink_pool, 10, 15)

    oneweb_pool = 4.5 + 1.5 * np.sin(np.linspace(0, 3*np.pi, 60)) + np.random.normal(0, 0.3, 60)
    oneweb_pool = np.clip(oneweb_pool, 3, 6)

    fig.add_trace(
        go.Scatter(x=times, y=starlink_pool, name='Starlink池',
                  mode='lines+markers', line=dict(color='green', width=2)),
        row=1, col=1
    )

    fig.add_trace(
        go.Scatter(x=times, y=oneweb_pool, name='OneWeb池',
                  mode='lines+markers', line=dict(color='blue', width=2)),
        row=1, col=1
    )

    # 添加目標範圍
    fig.add_hrect(y0=10, y1=15, line_width=0, fillcolor="green",
                  opacity=0.1, row=1, col=1)
    fig.add_hrect(y0=3, y1=6, line_width=0, fillcolor="blue",
                  opacity=0.1, row=1, col=1)

    # 2. RSRP信號品質 (右上)
    rsrp_serving = -75 - 10 * np.sin(np.linspace(0, 4*np.pi, 60)) + np.random.normal(0, 2, 60)
    rsrp_candidate = -85 - 8 * np.sin(np.linspace(0, 4*np.pi, 60) + np.pi/3) + np.random.normal(0, 2, 60)

    fig.add_trace(
        go.Scatter(x=times, y=rsrp_serving, name='服務衛星',
                  mode='lines', line=dict(color='darkgreen', width=2)),
        row=1, col=2
    )

    fig.add_trace(
        go.Scatter(x=times, y=rsrp_candidate, name='候選衛星',
                  mode='lines', line=dict(color='orange', width=2, dash='dash')),
        row=1, col=2
    )

    # A4門檻線
    fig.add_hline(y=-100, line_color="red", line_dash="dot",
                  row=1, col=2)

    # 3. 3GPP換手事件 (左下)
    event_times = np.random.choice(60, 8, replace=False)
    event_types = np.random.choice(['A4', 'A5', 'D2'], 8)
    event_colors = {'A4': 'yellow', 'A5': 'orange', 'D2': 'red'}

    for i, (t, e) in enumerate(zip(event_times, event_types)):
        fig.add_trace(
            go.Scatter(x=[times[t]], y=[e],
                      mode='markers',
                      marker=dict(size=12, color=event_colors[e], symbol='diamond'),
                      name=f'{e}事件',
                      showlegend=(i<3)),
            row=2, col=1
        )

    # 4. 衛星仰角分布 (右下)
    elevation_ranges = ['0-30°', '30-60°', '60-90°']
    starlink_dist = [3, 8, 4]
    oneweb_dist = [1, 3, 2]

    fig.add_trace(
        go.Bar(name='Starlink', x=elevation_ranges, y=starlink_dist,
               marker_color='green'),
        row=2, col=2
    )

    fig.add_trace(
        go.Bar(name='OneWeb', x=elevation_ranges, y=oneweb_dist,
               marker_color='blue'),
        row=2, col=2
    )

    # 更新佈局
    fig.update_xaxes(title_text="時間", row=1, col=1)
    fig.update_xaxes(title_text="時間", row=1, col=2)
    fig.update_xaxes(title_text="時間", row=2, col=1)
    fig.update_xaxes(title_text="仰角範圍", row=2, col=2)

    fig.update_yaxes(title_text="衛星數量", row=1, col=1)
    fig.update_yaxes(title_text="RSRP (dBm)", row=1, col=2)
    fig.update_yaxes(title_text="事件類型", row=2, col=1)
    fig.update_yaxes(title_text="衛星數量", row=2, col=2)

    fig.update_layout(
        title_text="📊 LEO衛星換手場景時序分析儀表板",
        height=800,
        showlegend=True,
        template='plotly_white'
    )

    return fig

def main():
    """執行視覺化demo"""
    print("="*60)
    print("🛰️  LEO衛星動態池視覺化Demo")
    print("="*60)

    print("\n📊 生成3D衛星軌道視覺化...")
    fig_3d, starlink_visible, oneweb_visible = create_3d_satellite_visualization()

    print(f"\n✅ 衛星池狀態:")
    print(f"   Starlink: {starlink_visible}/15 顆可見 (目標: 10-15)")
    status_starlink = "✅ 滿足" if 10 <= starlink_visible <= 15 else "⚠️ 不足"
    print(f"   狀態: {status_starlink}")

    print(f"\n   OneWeb: {oneweb_visible}/6 顆可見 (目標: 3-6)")
    status_oneweb = "✅ 滿足" if 3 <= oneweb_visible <= 6 else "⚠️ 不足"
    print(f"   狀態: {status_oneweb}")

    # 儲存3D視覺化
    output_3d = "satellite_3d_demo.html"
    fig_3d.write_html(output_3d)
    print(f"\n💾 已儲存3D視覺化: {output_3d}")

    print("\n📈 生成時序分析儀表板...")
    fig_dashboard = create_time_series_dashboard()

    # 儲存儀表板
    output_dashboard = "satellite_dashboard_demo.html"
    fig_dashboard.write_html(output_dashboard)
    print(f"💾 已儲存儀表板: {output_dashboard}")

    print("\n🎯 視覺化特色:")
    print("   • 3D地球與衛星軌道")
    print("   • 動態衛星池狀態監控")
    print("   • RSRP信號品質追蹤")
    print("   • 3GPP換手事件標記")
    print("   • 衛星仰角分布統計")

    print("\n✨ Demo完成！")
    print(f"   請開啟瀏覽器查看:")
    print(f"   • {output_3d}")
    print(f"   • {output_dashboard}")

    # 嘗試自動開啟瀏覽器
    try:
        file_path = os.path.abspath(output_3d)
        webbrowser.open(f'file://{file_path}')
        print("\n🌐 已自動開啟瀏覽器顯示3D視覺化")
    except:
        print("\n💡 提示: 請手動開啟HTML檔案查看")

if __name__ == "__main__":
    main()