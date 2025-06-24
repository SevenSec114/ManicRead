# ManicRead
> AAAAAAAAAAarch~~

## Overview
Linux 版本的 ManicTime 本地端本身不支持渲染 UI，只提供了各程式的 timeline 追踪，最终会生成 `sqlite` 文件，通常位于 `~/.config/manictime/` 中，并伴随着 `Screenshots` 一并储存。

截至 2025.06.24，仅使用并读取了 `ManicTimeReports.db` 作为数据源，后续考虑使用 `electron` 整合为桌面应用。界面渲染使用网页形式，主要框架为 [NiceGUI](https://nicegui.io) ，绘图使用页面嵌入式 [HighCharts](https://www.highcharts.com)

后续考虑加入使用 ScreenShots 内容

## Features
直接上图吧

- `Daily` 具体日期追踪
![](./img/daily.png)

- `Period` 时间段追踪
![](./img/period.png)

## Usage
建议 python 版本 3.10 以上

### 依赖
```bash
pip install nicegui
```

### 运行
```bash
python main.py
```
将会启动一个网页，默认 `http://127.0.0.1:8080`


## Changelog
- 2025.06.23
    - 数据读取和页面内容基本完成
    - Period 排序
    - Period 过滤
- 2025.06.24
    - 添加对 session lock, away 的追踪
    - 添加 Daily 页面动画效果