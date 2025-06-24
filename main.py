from nicegui import ui
from data_fetch import DataBase
from ui_show import UIRenderer
import os

db_path = os.path.expanduser("~/.config/manictime/ManicTimeReports.db")
db = DataBase(db_path)
renderer = UIRenderer(db)

# 加载 Highcharts 模块
ui.add_css("""
    @keyframes fade-out {
        from {
           opacity: 0;
        }
        to {
           opacity: 1;
        }
    }
""")

ui.add_head_html("""
    <script src="https://code.highcharts.com/highcharts.js"></script>
    <script src="https://code.highcharts.com/highcharts-more.js"></script>
    <script src="https://code.highcharts.com/modules/xrange.js"></script>
    <script src="https://code.highcharts.com/modules/exporting.js"></script>
    <script src="https://code.highcharts.com/modules/accessibility.js"></script>
""")

renderer.create_interface()

ui.run(title='ManicRead')