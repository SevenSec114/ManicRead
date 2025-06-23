from nicegui import ui
from datetime import datetime, date, timedelta
import hashlib, json
from data_fetch import DataBase
from nicegui_toolkit import inject_layout_tool
# inject_layout_tool()

class UIRenderer():
    def __init__(self, db):
        self.db = db
        self.daily_total_statistics_container = None
        self.period_total_statistics_container = None
        self.inited = False # 只是用来看另一个tab是否加载
        pass

    def hash_color(self, name):
        h = hashlib.md5(name.encode()).hexdigest()
        r = int(h[0:2], 16)
        g = int(h[2:4], 16)
        b = int(h[4:6], 16)
        return f'#{r:02x}{g:02x}{b:02x}'
    
    def daily_render(self, date_str=str(date.today())):
        segments, usage = self.db.load_data(date_str)

        # 合并相邻同名且时间连续的 segments
        merged_segments = []
        for seg in segments:
            if merged_segments and seg[0] == merged_segments[-1][0] and seg[1] == merged_segments[-1][2]:
                # 合并：更新end_ms
                merged_segments[-1] = (merged_segments[-1][0], merged_segments[-1][1], seg[2])
            else:
                merged_segments.append(seg)
        segments = merged_segments

        if self.daily_total_statistics_container:
            with self.daily_total_statistics_container:
                self.daily_total_statistics_container.clear()
                with ui.card().style('align-self: stretch;'):
                    ui.label("Usage Summary").classes('text-h6').style('align-self: center;')
                    for app, total_hours in sorted(usage.items(), key=lambda x: x[1], reverse=True):
                        hours = int(total_hours)
                        minutes = int((total_hours - hours) * 60)
                        seconds = int(((total_hours - hours) * 60 - minutes) * 60)
                        ui.label(f"{app}: {hours:02d}:{minutes:02d}:{seconds:02d}").classes('ml-4').style('align-self: end;')

        if not segments:
            date_str = ''

        data = [
            {
                'x': start_ms,
                'x2': end_ms,
                'y': 0,
                'name': title,
                'color': self.hash_color(title)
            }
            for title, start_ms, end_ms in segments
        ]
        chart_data = json.dumps(data, ensure_ascii=False)
        categories = json.dumps([""], ensure_ascii=False)

        ui.run_javascript(f"""
            let chart = null;
            function initChart(data, date_str) {{
                chart = Highcharts.chart('daily-gantt-graph', {{
                    time: {{
                        timezoneOffset: -8 * 60
                    }},
                    chart: {{ type: 'xrange', zoomType: 'x', height: 200 }},
                    title: {{ text: date_str + ' timeline' }},
                    xAxis: {{
                        type: 'datetime',
                        title: {{ text: '时间' }},
                        labels: {{ format: '{{value:%H:%M}}' }}
                    }},
                    yAxis: {{
                        categories: {categories},
                        reversed: true,
                        tickInterval: 1,
                        title: null,
                        labels: {{ enabled: false }},
                        gridLineWidth: 0
                    }},
                    tooltip: {{
                        formatter: function() {{
                            return '<b>' + this.point.name + '</b><br>' +
                            Highcharts.dateFormat('%H:%M:%S', this.point.x) +
                            ' → ' + Highcharts.dateFormat('%H:%M:%S', this.point.x2);
                        }}
                    }},
                    series: [{{
                        name: 'activities',
                        data: {chart_data}
                    }}],
                    navigator: {{
                        enabled: true
                    }},
                    scrollbar: {{
                        enabled: true
                    }},
                    rangeSelector: {{
                        enabled: true
                    }}
                }});

                Highcharts.setOptions({{
                    time: {{
                        timezoneOffset: -8 * 60
                    }}
                }});
            }}

            if (chart) {{
                chart.series[0].setData({chart_data});
            }} else {{
                initChart({chart_data}, '{date_str}');
            }}
        """)

    def period_render(self, start_date_str=None, end_date_str=None):
        if not start_date_str or not end_date_str and not self.inited:
            today = date.today()
            first_day_of_month = today.replace(day=1)
            last_day_of_month = (first_day_of_month.replace(month=first_day_of_month.month % 12 + 1, day=1) - timedelta(days=1))

            start_date_str = first_day_of_month.strftime("%Y-%m-%d")
            end_date_str = last_day_of_month.strftime("%Y-%m-%d")

        self.inited = True

        usage = self.db.load_data_range(start_date_str, end_date_str)

        # Prepare data for Highcharts
        categories_list = list(usage.keys())
        categories = json.dumps(categories_list, ensure_ascii=False)
        series_data = [
            {
                "y": round(usage[app], 2),
                "color": self.hash_color(app),
                "name": app
            }
            for app in categories_list
        ]
        chart_data = json.dumps(series_data, ensure_ascii=False)

        # Inject JavaScript to render the bar chart
        ui.run_javascript(f"""
            window.periodChart = Highcharts.chart('period-gantt-graph', {{
                chart: {{
                    type: 'column'
                }},
                title: {{
                    text: '{start_date_str} to {end_date_str} Usage Statistics'
                }},
                xAxis: {{
                    categories: {categories},
                    labels: {{
                        rotation: -45,
                        style: {{
                            fontSize: '12px'
                        }}
                    }}
                }},
                yAxis: {{
                    title: {{
                        text: 'Hours'
                    }}
                }},
                tooltip: {{
                    formatter: function() {{
                        return '<span style="color:' + this.point.color + '">\u25CF</span> ' +
                               '<b>' + this.point.name + '</b><br/>' +
                               this.y.toFixed(2) + ' hours';
                    }}
                }},
                plotOptions: {{
                    column: {{
                        dataLabels: {{
                            enabled: true,
                            format: '{'{point.y:.1f}'}'
                        }}
                    }}
                }},
                series: [{{
                    name: 'Total Usage',
                    data: {chart_data},
                    colorByPoint: false
                }}]
            }});
        """)

    def daily_chart_update(self, e):
        date_str = e.value
        self.daily_render(date_str)

    def period_chart_update(self, e):
        if type(e.value) is dict:
            start_date_str = e.value['from']
            end_date_str = e.value['to']
        elif type(e.value) is str:
            start_date_str = e.value
            end_date_str = e.value
        else:
            start_date_str = None
            end_date_str = None
        self.period_render(start_date_str, end_date_str)

    def create_interface(self):
        with ui.header(elevated=True).style('background-color: #3874c8; padding-top: 2px; padding-bottom: 2px;').classes('items-center justify-between'):
            ui.label('ManicRead').style('font-size: 24px; font-weight: bold;')
            with ui.tabs(on_change=self.period_render) as tabs:
                ui.tab('Per Day', icon='schedule').props('no-caps style="font-size: 10px;"')
                ui.tab('Total', icon='equalizer').props('no-caps style="font-size: 10px;"')

        # 页面创建
        with ui.tab_panels(tabs, value='Per Day').style('align-self: stretch;'):
            with ui.tab_panel('Per Day'):
                with ui.column().style('align-self: stretch;'):
                    with ui.button(icon='calendar_month').props('round flat color="white').tooltip('Select a date'):
                        with ui.menu():
                            formatted_dates = {datetime.strptime(date_str, "%Y-%m-%d").strftime("%Y/%m/%d") for date_str in self.db.get_available_dates()}
                            ui.date(value=date.today(), on_change=self.daily_chart_update).style('align-self: center;').props(f'''options="{formatted_dates}"''')

                    ui.card().style('align-self: stretch;').props('id=daily-gantt-graph') # 图像显示容器
                    self.daily_total_statistics_container = ui.element().style('align-self: stretch;')  # 当日时长总统计容器

                    # 初次进入渲染当天数据
                    ui.timer(0.1, self.daily_render, once=True)

            with ui.tab_panel('Total'):
                with ui.column().style('align-self: stretch;'):
                    with ui.button(icon='calendar_month').props('round flat color="white').tooltip('Select a date'):
                        with ui.menu():
                            ui.date({'from': str(datetime.now().replace(day=1).date()), 'to': str(datetime.now().date())}, on_change=self.period_chart_update).style('align-self: center;').props('range')
                    
                    ui.card().style('align-self: stretch;').props('id=period-gantt-graph') # 阶段时长总统计容器