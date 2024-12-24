# -*- coding: utf-8 -*-
from textual.app import App,ComposeResult
from textual.widgets import Static,Header,Footer,DataTable,Input,Log,Button,Label,Checkbox,ContentSwitcher
from textual.containers import Horizontal,VerticalScroll
from textual.widgets.data_table import Column 
from textual.widgets.data_table import RowDoesNotExist
from itertools import cycle
from rich.text import Text
from textual import events
from textual.cache import LRUCache
from textual._two_way_dict import TwoWayDict
import sqlite3
import sys
import subprocess
from textual.reactive import reactive
import difflib
import re
from textual import work
from textual._two_way_dict import TwoWayDict
from textual._styles_cache import StylesCache
from typing_extensions import Self
import time
import os
import random
import json
import string
from geoip2.database import Reader
import locale

class DataTables(DataTable):

        def clear(self, columns: bool = False) -> Self:
            """Clear the table.
            Args:
                columns: Also clear the columns.
            Returns:
                The `DataTable` instance.
            """
            self.davin_coordinate = self.cursor_coordinate
            self._clear_caches()
            self._y_offsets.clear()
            self._data.clear()
            self.rows.clear()
            self._row_locations = TwoWayDict({})
            if columns:
                self.columns.clear()
                self._column_locations = TwoWayDict({})
            self._require_update_dimensions = True
            #self.cursor_coordinate = Coordinate(0, 0)
            #self.hover_coordinate = Coordinate(0, 0)
            self._label_column = Column(self._label_column_key, Text(), auto_width=True)
            self._labelled_row_exists = False
            self._clear_caches()
            self.refresh()
            #self.scroll_x = 0
            #self.scroll_y = 0
            #self.scroll_target_x = 0
            #self.scroll_target_y = 0
            return self

class GridLayout(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 4 3;
        grid-columns: 20% 45% 25% 10% ;
        grid-rows: 45% 45% 10% ;
    }

    Header {
        height: 6%;
        text-style: bold;
        text-align: center;
    }

    .box {
        height: 100%;
        border: solid round  #00BFFF 30%;
        padding: 1 2;
    }

    #warning_checkbox {
        color: red;
    }

    .box:focus, #input_command:focus , #Introduction:focus {
        height: 100%;
        border: solid round green 100%;
        padding: 1 2;
    }

    .box:hover,  #input_command:hover , #Introduction:hover {
        height: 100%;
        border: solid round darkcyan 100%;
        padding: 1 2;
    }
    
    #box_warning {
        layer: horizontal;
        height: 18;
        width: 100%;
        opacity: 70%;
        margin-top: 8;
        margin-bottom: 8;
        border: solid round red 100%;
    }

    .yes_or_no_button {
        width: 1fr;
        margin-left: 3;
        margin-right: 3;
    }
    
    #network {
        width: 100%;
        align: center middle;
    }

    #listen {
        row-span: 1;
    }

    #outside {
        row-span: 1;
    }

    #details_switcher {
        column-span: 2;
        row-span: 2;
    }

    #details_switcher:focus {
        column-span: 2;
        row-span: 2;
        border: solid round green 100%;
    }
    
    #export_ip {
        row-span: 1;
        border: solid #f36c21;
        text-align: center;
        width: 100%;
    }

    #ban_ip {
        row-span: 1;
        border: solid #f36c21;
        text-align: center;
        width: 100%;
    }

    #input_command {
        height: 100%;
        border: solid round  #f36c21 100%;
        padding: 1 2;
    }

    #Introduction {
        height: 100%;
        border: solid round  #00BFFF 30%;
    }

    """

    #文本语言
    IntroductionText = """
 === Welcome To TMD-TOP ===

 author: Davin
 gitee: https://gitee.com/Davin168/tmd-top
 github: https://github.com/CDWEN0526/tmd-top
 email: 949178863@qq.com
 version: v2.2.0
 Geoip update time: 2024-12-20
 Update command: pip install tmd-top --upgrade
 Copy text: Press the tab key to switch windows, hold down the shift key, and you can choose to copy with the mouse;
    """
    warning_text = """
 Note that operation!!!
 Operation to block IP[{}]

 Blocking ip will call the system command iptables, 
 please make sure Confirm that iptables is installed, 
 otherwise the blocking feature will be ineffective!
 
 To unblock the ip, you need to manually delete 
 the iptables rule. Please operate carefully!
"""
    current_pid_text = "Current PID: None"
    search_string_text = "Enter search terms to support fuzzy search."
    export_button_text = "Export IP To ./ip.txt"
    ip_kill_button_text = 'IP Kill'
    box_warning_title_text = "Warning"
    network_title_text = "Network Card"
    total_text = "Total"
    listen_title_text = "Listening Service"
    outside_title_text = "Run Program"
    details_switcher_title_text = "Detailed"
    Introduction_title_text = "Log"
    input_command_title_text = "Search"
    button_text = "Button"
    netcard_table_text = "NetCard"
    up_table_text = "UP"
    down_table_text = "DOWN"
    service_table_text = "Service"
    addr_table_text = "Addr"
    port_table_text = "Port"
    uv_table_text = "UV"
    pv_table_text = "PV"
    mem_table_text = "MEM"
    client_ip_table_text = "ClientIp"
    client_port_table_text = "Port"
    areas_table_text = "Areas"
    name_table_text = "Name"
    current_pid_text = " current pid"
    current_pid_port_text = " current pid_port"
    pid_command_text = "PID Command"
    query_text = "Query"
    selected_ip_text = "Selected IP"
    block_ip_error_text = "Error: Operate IP block, do not choose other IP"
    checked_text = "Checked"
    unchecked_text = "Unchecked"
    export_ip_log_text = "Export IP list and wait patiently"
    export_ip_end_text = "Export IP end"
    export_path_text = "Export Path"
    block_ip_not_selected_text = "Warning: IP is not selected and cannot be blocked"
    block_ip_again_text = "Please select an IP and try again!!"
    dangerour_operations_text = "Performing dangerous operations"
    check_to_prevent_misoperation_text = "Please check to prevent misoperation"
    block_ip_success_text = "Blocking successfully"
    block_ip_text = "Block IP"
    block_fail_text = "Block Failed"
    error_text = "Error"
    cancle_window_text = "Cancel the operation and close the warning window"
    error_iptables_text = "Error executing iptables command"
    unknown_error_text = "an unknown error occurred"
    language = "en"
    no_more_reminders_text = "No more reminders"
    yes_text = "Yes"
    no_text = "No"


    ENABLE_COMMAND_PALETTE = False
    current_locale = locale.getlocale()
    language_code = current_locale[0] if current_locale[0] else None
    if 'CN' in language_code or 'cn' in language_code:
        BINDINGS = [
            ("q","quit","(退出)"),
            ('v','input_command','(搜索)'),
            ('t','slow_sleep_time','(慢刷新)'),
            ('y','sleep_time','(快刷新)'),
            ('c','sort_connect','(连接数排序)'),
            ('i','sort_ip','(IP数排序)'),
            ('u','sort_up','(上传排序)'),
            ('d','sort_down','(下载排序)'),   
            ('z','sort_cpu','(CPU排序)'), 
            ('x','sort_men','(内存排序)'),
            ]
    else:
        BINDINGS = [
            ("q","quit","(Exit)"),
            ('v','input_command','(Search)'),
            ('t','slow_sleep_time','(RefreshSlow)'),
            ('y','sleep_time','(RestoreRefresh)'),
            ('c','sort_connect','(ConnSort)'),
            ('i','sort_ip','(IpSort)'),
            ('u','sort_up','(UpSort)'),
            ('d','sort_down','(DownSort)'),   
            ('z','sort_cpu','(CpuSort)'), 
            ('x','sort_men','(MemSort)'),
            ]

    order_by = """
    ORDER BY 
            upload DESC,
            download DESC
    """
    #默认order_by
    pid_order_by = """
    ORDER BY 
            upload DESC,
            download DESC
    """
    listen = reactive([])
    network = reactive([])
    detailed = reactive([])
    outside = reactive([])
    #pid_number = reactive(None)
    pid_number = None
    pid_port = None
    davin = None
    sleep_time = 1
    listen_value = None
    outside_value = None
    details_value = None
    ip = None
    warning_checkbox_status = False
    log_value = None
    search_string = None
    listen_or_outsude = None
    AUTO_FOCUS = '#network'
    debug = False 

    def __init__(self,*args,**kwargs):
        super().__init__(*args, **kwargs)

        # 获取当前系统的区域设置
        current_locale = locale.getlocale()
        language_code = current_locale[0] if current_locale[0] else None
        if 'CN' in language_code or 'cn' in language_code:
            self.IntroductionText = """
 === Welcome To TMD-TOP ===

 author: Davin
 gitee: https://gitee.com/Davin168/tmd-top
 github: https://github.com/CDWEN0526/tmd-top
 email: 949178863@qq.com
 version: v2.2.0
 geoip更新时间: 2024-12-20
 更新: pip install tmd-top --upgrade
 复制: 按tab键切换窗口,按住shift键不放,鼠标可选复制;
        
"""
            self.warning_text = """
 注意操作！！！
 操作封禁IP[{}]

 封禁ip将会调用系统命令iptables，请确
 认已安装iptables，否则封禁功能将无效！
 
 解封ip需要手动删除iptables规则，请谨
 慎操作！ 
            """
            self.current_pid_text = "当前PID: None"
            self.search_string_text = "请输入搜索关键词,支持模糊搜索"
            self.export_button_text = "导出IP到./ip.txt"
            self.ip_kill_button_text = 'IP封禁'
            self.box_warning_title_text = "警 告"
            self.network_title_text = "网卡"
            self.total_text = "总共"
            self.listen_title_text = "监听服务"
            self.outside_title_text = "运行程序"
            self.details_switcher_title_text = "详情"
            self.Introduction_title_text = "日志"
            self.input_command_title_text = "搜索"
            self.button_text = "按钮"
            self.netcard_table_text = "网卡"
            self.up_table_text = "上传"
            self.down_table_text = "下载"
            self.service_table_text = "服务"
            self.addr_table_text = "IP"
            self.port_table_text = "端口"
            self.uv_table_text = "IP数"
            self.pv_table_text = "连接数"
            self.mem_table_text = "内存"
            self.client_ip_table_text = "客户端IP"
            self.client_port_table_text = "PORT"
            self.areas_table_text = "地区"
            self.name_table_text = "名称"
            self.current_pid_text = " 当前PID"
            self.current_pid_port_text = " 当前PID端口"
            self.pid_command_text = "PID命令"
            self.query_text = "查询"
            self.selected_ip_text = "已选IP"
            self.block_ip_error_text = "错误：操作当前选中IP，不能选择其他IP。"
            self.checked_text = "已选"
            self.unchecked_text = "未选"
            self.export_ip_log_text = "导出IP列表，请耐心等待"
            self.export_ip_end_text = "导出完成"
            self.export_path_text = "导出路径"
            self.block_ip_not_selected_text = "错误：未选择IP，请选择IP后再进行操作。"
            self.block_ip_again_text = "请选择IP然后再试"
            self.dangerour_operations_text = "进行危险操作"
            self.check_to_prevent_misoperation_text = "请检查以防误操作"
            self.block_ip_success_text = "IP封禁成功"
            self.block_ip_text = "封禁IP"
            self.block_fail_text = "封禁失败"
            self.error_text = "错误"
            self.cancle_window_text = "取消操作并关闭警告窗口" 
            self.error_iptables_text = "执行iptables命令时出错"
            self.unknown_error_text = "出现未知错误"
            self.language = 'zh-CN'
            self.no_more_reminders_text = "不再提醒"
            self.yes_text = "确定"
            self.no_text = "取消"

    def compose(self) -> ComposeResult:
        try:
            yield Header(show_clock=True)
            yield DataTables(id="network", classes="box",name="network")
            yield DataTables(classes="box", id="listen",name="listen")
            with ContentSwitcher(initial='details',classes="box",id="details_switcher",name="details_switcher"):
                yield DataTables(id="details",name="details")
                with VerticalScroll(id="box_warning"):
                    yield Label(id='warning_text')
                    yield Checkbox(self.no_more_reminders_text,id="warning_checkbox")
                    yield Horizontal(
                        Button(f"[{self.yes_text}]",classes="yes_or_no_button",id="yes_button",variant="error"),
                        Button(f"[{self.no_text}]",classes="yes_or_no_button",id="no_button",variant="primary")
                    )
            yield Log(id="Introduction",classes="box",highlight=True)
            yield DataTables(classes="box",id="outside",name="outside")
            yield Static(self.current_pid_text,classes="box",id="instruction_display")
            yield Input(placeholder=self.search_string_text,id="input_command")
            yield Button(self.export_button_text,classes='box',id='export_ip')
            yield Button(self.ip_kill_button_text,classes='box',id='ban_ip')
            yield Footer()
        except Exception:
            pass

    def on_mount(self) -> None:
        self.title = "TMD-TOP"
        self.query_one('#box_warning').border_title = self.box_warning_title_text
        self.query_one('#network').border_title = self.network_title_text
        self.query_one('#network').border_subtitle = self.total_text + " 0" 
        self.query_one('#network').loading = True
        self.query_one('#listen').border_title = self.listen_title_text
        self.query_one('#listen').border_subtitle = self.total_text + " 0"
        self.query_one('#listen').loading = True
        self.query_one('#outside').border_title = self.outside_title_text
        self.query_one('#outside').border_subtitle = self.total_text + " 0"
        self.query_one('#outside').loading = True
        self.query_one('#details_switcher').border_title = self.details_switcher_title_text
        self.query_one('#details_switcher').border_subtitle = self.total_text + " 0"
        self.query_one('#details_switcher').loading = True
        self.query_one('#details_switcher').can_focus = True
        self.query_one('#Introduction').border_title = self.Introduction_title_text
        self.query_one('#instruction_display').border_title = 'PID'
        self.query_one('#input_command').border_title = self.input_command_title_text
        self.query_one('#export_ip').border_title = self.button_text
        self.query_one('#ban_ip').border_title = self.button_text
        log = self.query_one(Log)
        log.write_line(self.IntroductionText)
        network_table = self.query_one('#network')
        network_table.cursor_type = next(cycle(["row"]))
        network_table.add_column(self.netcard_table_text,key='name')
        network_table.add_column(self.up_table_text,key='up')
        network_table.add_column(self.down_table_text,key='down')
        network_table.add_row(*self.network)

        listen_table = self.query_one('#listen')
        listen_table.cursor_type = next(cycle(["row"])) 
        listen_table.add_column("PID",key='1')
        listen_table.add_column(self.service_table_text,key='2')
        listen_table.add_column(self.addr_table_text,key='3')
        listen_table.add_column(self.port_table_text,key='4')
        listen_table.add_column(self.uv_table_text,key='5')
        listen_table.add_column(self.pv_table_text,key='6')
        listen_table.add_column(self.up_table_text,key='7')
        listen_table.add_column(self.down_table_text,key='8')
        listen_table.add_column("CPU",key='9')
        listen_table.add_column(self.mem_table_text,key='10')
        
        details_table = self.query_one('#details')
        details_table.cursor_type = next(cycle(["row"])) 
        details_table.add_column(self.client_ip_table_text,key='1')
        details_table.add_column(self.client_port_table_text,key='2')
        details_table.add_column(self.up_table_text,key='3')
        details_table.add_column(self.down_table_text,key='4')
        details_table.add_column(self.areas_table_text,key='5')

        outside_table = self.query_one('#outside')
        outside_table.cursor_type = next(cycle(["row"])) 
        outside_table.add_column("PID",key='1')
        outside_table.add_column(self.name_table_text,key='2')
        outside_table.add_column(self.uv_table_text,key='3')
        outside_table.add_column(self.pv_table_text,key='4')
        outside_table.add_column(self.up_table_text,key='5')
        outside_table.add_column(self.down_table_text,key='6')
        outside_table.add_column("CPU",key='7')
        outside_table.add_column(self.areas_table_text,key='8')

        log.write_line(f"{self.current_pid_text}: {self.pid_number}")
        log.write_line(f"{self.current_pid_port_text}: {self.pid_port}")
        self.update_tables()

    #监视network变量的改变，改变则触发事件
    def watch_network(self) -> None:
        network_dom = self.query_one("#network")
        screen_dom = self.query_one("#_default")
        try:
            screen_dom.recompose()
            screen_dom.refresh()
            screen_dom._styles_cache.clear()
            network_dom.rows = {}
            network_dom.clear()
            network_dom.recompose()
            network_dom.rows = {}
            network_dom.add_rows(self.network)
            row_number = self.query_one('#network').row_count
            network_dom.border_subtitle = f"{self.total_text} " + str(row_number)
        except Exception:
            pass
        
    #监视listen变量的改变，改变则触发事件
    def watch_listen(self) -> None:
        listen_dom = self.query_one('#listen')
        row_number = listen_dom.row_count
        try:
            listen_dom._cache = {}
            listen_dom.clear()
            for i in self.listen:
                data = list(i)[1:]
                try:
                    listen_dom.get_row_index(row_key=str(i[0]))
                    for l in data:
                        listen_dom.update_cell(row_key=str(i[0]),column_key=str(int(data.index(l)) + 1),value=str(l))
                except RowDoesNotExist:
                    listen_dom.add_row(*data,key=str(i[0]))

            row_number = listen_dom.row_count
            listen_dom.border_subtitle = f"{self.total_text} " + str(row_number)
            for s in range(int(len(self.listen) +1 ),row_number):
                try:
                    listen_dom.remove_row(str(s))
                except RowDoesNotExist:
                    pass
        except Exception as e:
            pass
            
    #监视outside变量的改变，改变则触发事件
    def watch_outside(self) -> None:
        outside_dom = self.query_one('#outside')
        row_number = outside_dom.row_count
        try:
            outside_dom._cache = {}
            outside_dom.clear()
            for i in self.outside:
                data = list(i)[1:]
                try:
                    outside_dom.get_row_index(row_key=str(i[0]))
                    for l in data:
                            outside_dom.update_cell(row_key=str(i[0]),column_key=str(int(data.index(l)) + 1),value=str(l))
                except RowDoesNotExist:
                    outside_dom.add_row(*data,key=str(i[0]))

            row_number = outside_dom.row_count
            outside_dom.border_subtitle = f"{self.total_text} " + str(row_number)
            for s in range(len(self.outside),row_number):
                try:
                    outside_dom.remove_row(str(s))
                except RowDoesNotExist:
                    pass
        except Exception:
            pass

    #监视detailed变量的改变，改变则触发事件
    def watch_detailed(self) -> None:
        details_dom = self.query_one('#details')
        details_switcher_dom = self.query_one('#details_switcher')
        row_number = details_dom.row_count
        try:
            details_switcher_dom.refresh()
            details_dom.refresh(layout=True)
            details_dom._styles_cache.clear()
            details_dom.clear()
            for i in self.detailed:
                data = list(i)[1:]
                try:
                    details_dom.get_row_index(row_key=str(i[0]))
                    for l in data:
                        details_dom.update_cell(row_key=str(i[0]),column_key=str(int(data.index(l)) + 1),value=str(l))
                except Exception:
                    details_dom.add_row(*data,key=str(i[0]))

            row_number = details_dom.row_count
            details_switcher_dom.border_subtitle = f"{self.total_text} " + str(row_number)
            for s in range(len(self.detailed),row_number):
                try:
                    details_dom.remove_row(str(s))
                except Exception:
                    pass
        except Exception:
            pass
        
    def generate_random_value(self):
        # 获取当前时间的时间戳
        timestamp = str(int(time.time() * 1000))  # 将时间戳转换为毫秒级
        # 生成一个随机字符串
        random_str = ''.join(random.choices(string.ascii_letters + string.digits, k=8))
        # 组合时间戳和随机字符串
        unique_value = f"{timestamp}_{random_str}"
        return unique_value
    
    #点击表格触发事件
    def on_data_table_row_selected(self,event):
        log = self.query_one(Log)
        value =  event.control.get_row(event.row_key)
        # if self.log_value != value[0]:
        if event.control.name == 'listen':
            self.listen_value = value
            self.pid_number = value[0]
            self.pid_port = value[3]
            cmd = self.selectPidCommand(value[0])
            log.write_line(f'\n {self.query_text}: \n')
            log.write_line(f'  {self.pid_command_text}: ' + str(cmd))
            log.write_line('  PID: ' + str(self.pid_number))
            log.write_line(f'  {self.port_table_text}: ' + str(self.pid_port))
            instruction_display = self.query_one("#instruction_display")
            instruction_display.update(f'{self.current_pid_text}: ' + value[0])
            self.log_value = value[0]
            self.listen_or_outsude = True
        if event.control.name == 'outside':
            self.outside_value = value
            self.pid_number = value[0]
            cmd = self.selectPidCommand(value[0])
            log.write_line(f'\n {self.query_text}: \n')
            log.write_line(f'  {self.pid_command_text}: ' + str(cmd))
            log.write_line('  PID: ' + str(self.pid_number))
            instruction_display = self.query_one("#instruction_display")
            instruction_display.update(f'{self.current_pid_text}: ' + value[0])
            self.listen_value = None
            self.log_value = value[0]
            self.pid_port = None
            self.listen_or_outsude = False
        if event.control.name == "details":
            self.details_value = value
            if self.query_one('#details_switcher').current == 'details':
                log.write_line(f'\n {self.selected_ip_text}: \n  ' + str(value[0]))
                self.log_value = value[0]
                self.ip = str(value[0])
            elif self.query_one('#details_switcher').current == 'box_warning':
                log.write_line(f'\n {self.block_ip_error_text}...')
                #使用api请求显示详细的ip信息
                #self.identify_address(value[1])


    #输入框查询pid回车触发事件
    def on_key(self,event: events.Key):
        self.davin = event.key
        if event.key == 'enter':
            pass

    def on_checkbox_changed(self, event: Checkbox.Changed) -> None:
        log = self.query_one(Log)
        if event.control.id == 'warning_checkbox' and event.value == True:
            log.write_line('\n ' + str(event.control.label + f": {self.checked_text}"))
            self.warning_checkbox_status = True
        elif event.control.id == 'warning_checkbox' and event.value == False:
            log.write_line('\n ' + str(event.control.label) + f": {self.unchecked_text}")
            self.warning_checkbox_status = False

    #按钮消息接收(导出ip按钮)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(Log)
        warning_box_dom = self.query_one('#box_warning')
        details_switcher_dom = self.query_one('#details_switcher')
        #导出ip列表按钮
        if event.button.id == 'export_ip':
            log.write_line(f'\n {self.export_ip_log_text}...')
            export_file_path = os.getcwd() + '/' + 'ip.txt'
            with open(export_file_path, 'w') as f:
                for i in self.detailed:
                    keys = ['ip','port','up','down','location']
                    f.write(json.dumps(dict(zip(keys,i)),ensure_ascii=False) + '\n')
            log.write_line(f' {self.export_ip_end_text}')
            log.write_line(f' {self.export_path_text}: ' + export_file_path)

        #封禁ip按钮
        elif event.button.id == 'ban_ip':
            warning_text_dom = self.query_one('#warning_text')
            if self.ip == None:
                log.write_line(f'\n {self.block_ip_not_selected_text}')
                log.write_line(f' {self.block_ip_again_text}!!')
            else:
                if self.warning_checkbox_status == False:
                    warning_text_dom.update(self.warning_text.format(self.ip))
                    log.write_line(f'\n {self.box_warning_title_text}: [' + self.ip + f']{self.dangerour_operations_text}...')
                    log.write_line(f' {self.check_to_prevent_misoperation_text}!')
                    details_switcher_dom.current = 'box_warning'
                elif self.warning_checkbox_status == True:
                    block_ip_status = self.block_ip(self.ip)
                    if block_ip_status == True:
                        log.write_line(f'\n {self.block_ip_success_text}!')
                        log.write_line(f' {self.block_ip_text}: ' + self.ip)
                    else:
                        log.write_line(f'\n {self.block_fail_text}!')
                        log.write_line(' Error: ' + str(block_ip_status))
            # self.query_one('#details_switcher').current = 'box_warning'

        #确认封禁
        elif event.button.id == 'yes_button':
            block_ip_status = self.block_ip(self.ip)
            if block_ip_status == True:
                log.write_line(f'\n {self.block_ip_success_text}!')
                log.write_line(f' {self.block_ip_text}: ' + self.ip)
            else:
                log.write_line(f'\n {self.block_fail_text}!')
                log.write_line(f' {self.error_text}: ' + str(block_ip_status))
            details_switcher_dom.current = 'details'
        #取消封禁
        elif event.button.id == 'no_button':
            log.write_line(f'\n {self.cancle_window_text}...')
            details_switcher_dom.current = 'details'

    #快捷键绑定事件
    def action_slow_sleep_time(self) -> None:
        self.sleep_time = 5

    def action_sleep_time(self) -> None:
        self.sleep_time = 1


    #快捷键绑定事件
    def action_quit(self) -> None:
        self.exit()

    #快捷键绑定事件
    def action_input_command(self) -> None:
        self.query_one('#input_command').focus()
    #快捷键绑定事件
    def action_sort_connect(self) -> None:
        self.order_by = """
            ORDER BY 
                connect_ip DESC
            """
        self.listen_value = None
        self.outside_value = None
        self.details_value = None
    #快捷键绑定事件
    def action_sort_ip(self) -> None:
        self.order_by = """
            ORDER BY 
                ip_num DESC
            """
        self.listen_value = None
        self.outside_value = None
        self.details_value = None
        
    #快捷键绑定事件
    def action_sort_up(self) -> None:
        self.order_by = """
            ORDER BY 
                upload DESC
            """
        self.pid_order_by = """
            ORDER BY 
                    upload DESC
            """
        self.listen_value = None
        self.outside_value = None
        self.details_value = None
    #快捷键绑定事件
    def action_sort_down(self) -> None:
        self.order_by = """
            ORDER BY 
                download DESC
            """
        self.pid_order_by = """
            ORDER BY 
                    download DESC
            """
        self.listen_value = None
        self.outside_value = None
        self.details_value = None
    #快捷绑定事件
    def action_sort_cpu(self) -> None:
        self.order_by = """
            ORDER BY 
                cpu DESC
            """
        self.listen_value = None
        self.outside_value = None
        self.details_value = None
    def action_sort_men(self) -> None:
        self.order_by = """
            ORDER BY 
                men DESC
            """
        self.listen_value = None
        self.outside_value = None
        self.details_value = None
    def action_sort_io_r(self) -> None:
        self.order_by = """
            ORDER BY 
                read DESC
            """
        self.listen_value = None
        self.outside_value = None
        self.details_value = None
    def action_sort_io_w(self) -> None:
        self.order_by = """
            ORDER BY 
                write DESC
            """
        self.listen_value = None
        self.outside_value = None
        self.details_value = None

    #定时器执行的任务
    @work(exclusive=True,thread=True)
    async def update_tables(self) -> None:
        while True:
            conn = self.connectSqlite()
            cat_command = self.localExecuteCommand("cat /proc/net/dev")
            ss_command = self.localExecuteCommand('ss -ni  state established  && echo "Davin system" && sleep 1 && ss -ni  state established')
            cat_command_sleep_1 = self.localExecuteCommand("cat /proc/net/dev")
            netstat_command = self.localExecuteCommand('ss -atpn')
            ps_command = self.localExecuteCommand("ps axu | grep -v '%CPU' | grep -v grep")
            one,two = self.ssDataProcessing(ss_command)
            net = self.netstatDataProcessing(netstat_command)
            ps = self.psDataProcessing(ps_command)
            self.insertData(conn=conn,table='one',data=one)
            self.insertData(conn=conn,table='two',data=two)
            self.insertData(conn=conn,table="net",data=net)
            self.insertData(conn=conn,table='ps',data=ps)
            self.selectTotalListen(conn=conn)
            self.selectTotalOut(conn=conn)
            self.selectDetails(conn=conn,pid=self.pid_number,port=self.pid_port)
            self.network = self.search(name='network',data=self.networkCardTraffic(cat_command,cat_command_sleep_1))
            self.listen = self.search(name='listen',data=self.selectServiceAll(conn=conn))
            self.outside = self.search(name='outside',data=self.selectProcessAll(conn=conn))
            self.detailed = self.search(name='detailed',data=self.selectDetailsAll(conn=conn))
            self.query_one('#outside').loading = False
            self.query_one('#network').loading = False
            self.query_one('#listen').loading = False
            self.query_one('#details_switcher').loading = False
            time.sleep(self.sleep_time)

    def search(self,name,data) -> None:
        search_string = self.query_one("#input_command").value
        if name == 'listen':
            listen = [t for t in data if any(search_string in s for s in t[1:])]
            if listen:
                return listen
            else:
                return data
        elif name == 'network':
            network = [t for t in data if any(search_string in s for s in t)]
            if network:
                return network
            else:
                return data
        elif name == 'outside':
            outside = [t for t in data if any(search_string in s for s in t[1:])]
            if outside:
                return outside
            else:
                return data
        elif name == 'detailed':
            detailed = [t for t in data if any(search_string in s for s in t[1:])]
            if detailed:
                return detailed
            else:
                return data

    #使用geoip获取ip信息
    def get_ip_info(self,ip_address):
        # 设置数据库文件的相对路径（假设它在脚本同一目录下）
        current_module_path = os.path.dirname(os.path.abspath(__file__))
        database_path = os.path.join(current_module_path, 'data/GeoLite2-City.mmdb')
        with Reader(database_path) as geoip_reader:
            try:
                response = geoip_reader.city(ip_address)

                # 获取详细的地理位置信息，并优先显示中文名称（如果有）
                country_name = response.country.names.get(self.language) or 'null'
                city_name = response.city.names.get(self.language) or 'null'
                subdivision_name = 'null'
                if len(response.subdivisions) > 0:
                    subdivision_name = response.subdivisions[0].names.get(self.language) or 'null'
                return (f"{country_name}/{subdivision_name}/{city_name}")

            except Exception:
                return ("null")

    #禁止ip访问
    def block_ip(self,ip):
        try:
            # 使用 sudo 执行 iptables 命令
            subprocess.run(['iptables', '-A', 'INPUT', '-s', ip, '-j', 'DROP'], check=True)
            return True
        except subprocess.CalledProcessError as e:
            return (f"{self.error_iptables_text}: {e}")
        except Exception as e:
            return (f"{self.unknown_error_text}: {e}")

    #获取执行的指令
    def selectPidCommand(self,pid_number):
        cat_command = self.localExecuteCommand("cat /proc/"+ str(pid_number) + "/cmdline")
        new_command = cat_command.replace('\x00',' ')
        return new_command


    #执行命令
    def localExecuteCommand(self,command):
        # Python 3.7及以上版本
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, command, result.stderr)
            return result.stdout
        except Exception as e:
            print(e)
            sys.exit(0)

    #连接sqlite数据库
    def connectSqlite(self):
        conn = sqlite3.connect(':memory:')
        # current_module_path = os.path.dirname(os.path.abspath(__file__))
        # db_file_path = os.path.join(current_module_path, 'data/tmd-top.db')
        # conn = sqlite3.connect(db_file_path)

        cursor = conn.cursor()

        #创建表
        cursor.execute('''CREATE TABLE IF NOT EXISTS one (
                            local_ip TEXT NOT NULL,
                            local_port TEXT NOT NULL,
                            remote_ip TEXT NOT NULL,
                            remote_port TEXT NOT NULL,
                            bytes_acked TEXT ,
                            bytes_received TEXT )''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS two (
                            local_ip TEXT NOT NULL,
                            local_port TEXT NOT NULL,
                            remote_ip TEXT NOT NULL,
                            remote_port TEXT NOT NULL,
                            bytes_acked TEXT,
                            bytes_received TEXT)''')
        cursor.execute('''CREATE TABLE IF NOT EXISTS net (
                            local_ip TEXT NOT NULL,
                            local_port TEXT NOT NULL,
                            remote_ip TEXT NOT NULL,
                            remote_port TEXT NOT NULL,
                            state TEXT,
                            pid TEXT,
                            program_name TEXT)'''
        )
        cursor.execute('''CREATE TABLE IF NOT EXISTS ps (
                            pid TEXT,
                            cpu REAL,
                            men REAL)'''
        )
        cursor.execute('''CREATE TABLE IF NOT EXISTS pidstat (
                            pid TEXT,
                            read REAL,
                            write REAL)'''
        )
        cursor.execute('''CREATE TABLE IF NOT EXISTS network_card (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            network TEXT NOT NULL,
                            up TEXT NOT NULL,
                            down TEXT NOT NULL)'''
        )

        cursor.execute('''CREATE TABLE IF NOT EXISTS service (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            pid TEXT NOT NULL,
                            service TEXT NOT NULL,
                            bind_ip TEXT NOT NULL,
                            bind_port TEXT NOT NULL,
                            uv TEXT NOT NULL,
                            pv TEXT NOT NULL,
                            up  TEXT NOT NULL,
                            down TEXT NOT NULL,
                            cpu REAL,
                            men REAL)'''
        )
        cursor.execute('''CREATE TABLE IF NOT EXISTS process (
                            id INTEGER PRIMARY KEY AUTOINCREMENT,
                            pid TEXT NOT NULL,
                            service TEXT NOT NULL,
                            uv TEXT NOT NULL,
                            pv TEXT NOT NULL,
                            up  TEXT NOT NULL,
                            down TEXT NOT NULL,
                            cpu REAL,
                            men REAL)'''
        )
        cursor.execute('''CREATE TABLE IF NOT EXISTS details (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        client_ip TEXT NOT NULL,
                        client_port TEXT NOT NULL,
                        up  TEXT NOT NULL,
                        down TEXT NOT NULL,
                        area TEXT NOT NULL)'''
        )

        conn.commit()
        cursor.close()
        return conn

    #ps命令结果数据处理
    def psDataProcessing(self,data):
        ps_data_all = []
        for line in data.splitlines():
            ps_dict = {}
            ps_pid_info = line.split()
            ps_dict['pid'] = ps_pid_info[1]
            ps_dict['cpu'] = ps_pid_info[2] + '%'
            ps_dict['men'] = ps_pid_info[3] + '%'
            ps_data_all.append(ps_dict)
        return ps_data_all


    #处理第一次数据和第二次的数据，过滤掉无用数据。
    def ssDataProcessing(self,data):
        one_data_all = []
        two_data_all = []
        one_data_list = str(data).split('Davin system')[0].split('tcp')
        two_data_list = str(data).split('Davin system')[1].split('tcp')
        for o in one_data_list:
            one_tcp_dict = {}
            if "Recv-Q" in o:
                continue
            one_tcp_rinse_list = []
            one_tcp_list = o.split()
            # print(one_tcp_list,"123")
            ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$'
            ipv6_pattern = r'^(::ffff:)?([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}:(\d{1,5})$'
            for item in one_tcp_list:
                item = item.replace('::ffff:','').replace('[', '').replace(']', '')
                if (re.match(ipv4_pattern, item) or re.match(ipv6_pattern, item)):
                    one_tcp_rinse_list.append(item)
                elif "bytes_acked" in item or "bytes_received" in item:
                    one_tcp_rinse_list.append(item)
            try:
                one_local_info = one_tcp_rinse_list[0].replace('::ffff:','').split(":")
            except IndexError:
                continue
            one_local_ip = one_local_info[0].replace('::ffff:','').split(":")[0]
            one_local_port = one_local_info[1]
            one_remote_info = one_tcp_rinse_list[1].replace('::ffff:','').split(":")
            one_remote_ip = one_remote_info[0].replace('::ffff:','').split(":")[0]
            one_remote_port = one_remote_info[1]
            try:
                one_bytes_acked = difflib.get_close_matches('bytes_acked',one_tcp_rinse_list,cutoff=0.6)[0].split(":")
            except Exception:
                one_bytes_acked = ['bytes_acked',0]
            one_bytes_acked_key_name = one_bytes_acked[0]
            one_bytes_acked_values = one_bytes_acked[1] 
            try:
                one_bytes_received = difflib.get_close_matches('bytes_received',one_tcp_rinse_list,cutoff=0.6)[0].split(":")
            except Exception:
                one_bytes_received = ['bytes_received',0]
            one_bytes_received_key_name = one_bytes_received[0]
            one_bytes_received_values = one_bytes_received[1]
            one_tcp_dict['local_ip'] = one_local_ip
            one_tcp_dict['local_port'] = one_local_port
            one_tcp_dict['remote_ip'] = one_remote_ip
            one_tcp_dict['remote_port'] = one_remote_port
            one_tcp_dict[one_bytes_acked_key_name] = one_bytes_acked_values
            one_tcp_dict[one_bytes_received_key_name] = one_bytes_received_values
            if one_tcp_dict['remote_ip']:
                one_data_all.append(one_tcp_dict)
        for t in two_data_list:
            two_tcp_dict = {}
            if "Recv-Q" in t or "u_str" in t or "udp" in t:
                continue
            two_tcp_rinse_list = []
            two_tcp_list = t.split()
            ipv4_pattern = r'^(\d{1,3}\.){3}\d{1,3}:\d{1,5}$'
            ipv6_pattern = r'^(::ffff:)?([0-9a-fA-F]{1,4}:){7,7}[0-9a-fA-F]{1,4}:(\d{1,5})$'
            for item2 in two_tcp_list:
                item2 = item2.replace('::ffff:','').replace('[', '').replace(']', '')
                if (re.match(ipv4_pattern, item2) or re.match(ipv6_pattern, item2)):
                        two_tcp_rinse_list.append(item2)
                elif "bytes_acked" in item2 or "bytes_received" in item2:
                    two_tcp_rinse_list.append(item2)
            try:
                two_local_info = two_tcp_rinse_list[0].replace('::ffff:','').split(":")
            except IndexError:
                continue
            two_local_ip = two_local_info[0].replace('::ffff:','').split(":")[0]
            two_local_port = two_local_info[1]
            two_remote_info = two_tcp_rinse_list[1].replace('::ffff:','').split(":")
            two_remote_ip = two_remote_info[0].replace('::ffff:','').split(":")[0]
            two_remote_port = two_remote_info[1]
            try:
                two_bytes_acked = difflib.get_close_matches('bytes_acked',two_tcp_rinse_list,cutoff=0.6)[0].split(":")
            except Exception:
                two_bytes_acked = ['bytes_acked',0]
            two_bytes_acked_key_name = two_bytes_acked[0]
            two_bytes_acked_values = two_bytes_acked[1] 
            try:
                two_bytes_received = difflib.get_close_matches('bytes_received',two_tcp_rinse_list,cutoff=0.6)[0].split(":")
            except Exception:
                two_bytes_received = ['bytes_received',0]
            two_bytes_received_key_name = two_bytes_received[0]
            two_bytes_received_values = two_bytes_received[1]
            two_tcp_dict['local_ip'] = two_local_ip
            two_tcp_dict['local_port'] = two_local_port
            two_tcp_dict['remote_ip'] = two_remote_ip
            two_tcp_dict['remote_port'] = two_remote_port
            two_tcp_dict[two_bytes_acked_key_name] = two_bytes_acked_values
            two_tcp_dict[two_bytes_received_key_name] = two_bytes_received_values
            if two_tcp_dict['remote_ip']:
                two_data_all.append(two_tcp_dict)
        return(one_data_all,two_data_all)

    #处理netstat命令的数据
    def netstatDataProcessing(self,data):
        netstat_list = []
        for i in data.splitlines():
            netstat_dict = {}
            if 'Active Internet' in i or 'Recv-Q Send-Q' in i or 'State' in i:
                continue
            else:
                netstat_all_data = i.split()
                local_info = netstat_all_data[3].replace('[::]','::').replace('::ffff:','').replace('[','').replace(']','')
                local_ip = local_info.split(':')[0].replace('::ffff:','').split(":")[0]
                local_port = local_info.split(':')[1]
                remote_info = netstat_all_data[4].replace('[::]','::').replace('::ffff:','').replace('[','').replace(']','')
                remote_ip = remote_info.split(':')[0].replace('::ffff:','').split(":")[0]
                remote_port = remote_info.split(":")[1]
                state = netstat_all_data[0].replace('ESTAB','ESTABLISHED')
                pid_programName = netstat_all_data[-1].replace('users:(','').replace('))',')').replace('"','').split('),')[-1].replace('(','').replace('pid=','').split(',')
                if len(pid_programName) == 1:
                    pid = "-"
                    pid_programName = []
                else:
                    pid = pid_programName[1]

                try:
                    program_name = pid_programName[0]
                except IndexError:
                    program_name = "-"
                if local_ip == "":
                    local_ip = local_info.replace('::ffff:','').split(":")[0]
                if local_port == "":
                    local_port = local_info.split(':')[-1]
                if remote_ip == "":
                    remote_ip = remote_info.replace('::ffff:','').split(":")[0]
                if remote_port == "":
                    remote_port = remote_info.split(":")[-1]
            netstat_dict['local_ip'] = local_ip
            netstat_dict['local_port'] = local_port
            netstat_dict['remote_ip'] =remote_ip
            netstat_dict['remote_port'] = remote_port
            netstat_dict['state'] = state
            netstat_dict['pid'] = pid
            netstat_dict['program_name'] = program_name 
            netstat_list.append(netstat_dict)
        return (netstat_list)  

    #插入数据
    def insertData(self,conn,table,data):
        insert_data = conn.cursor()
        if table == "one":
            insert_data.execute('delete from one;')
        elif table == 'two':
            insert_data.execute('delete from two;')
        elif table == "net":
            insert_data.execute('delete from net;')
        elif table == "ps":
            insert_data.execute('delete from ps;')
        elif table == "pidstat":
            insert_data.execute('delete from pidstat;')
        # elif table == "network_card":
        #     insert_data.execute('delete from service_card;')
        elif table == "service":
            insert_data.execute("DELETE FROM sqlite_sequence WHERE name='service';")
            insert_data.execute('delete from service;')
        elif table == "process":
            insert_data.execute("DELETE FROM sqlite_sequence WHERE name='process';")
            insert_data.execute('delete from process;')
        elif table == "details":
            insert_data.execute("DELETE FROM sqlite_sequence WHERE name='details';")
            insert_data.execute('delete from details;')
        else:
            print("Pass in the error table name.")
            sys.exit(0)

        if table == "one" or table == "two":    
            for i in data:
                local_ip = i['local_ip']
                local_port = i['local_port']
                remote_ip = i['remote_ip']
                remote_port = i['remote_port']
                bytes_acked =i['bytes_acked']  if ('bytes_acked' in i) else None
                bytes_received =  i['bytes_received'] if ('bytes_received' in i) else None
                if table == "one":
                    insert_data.execute('insert into one(local_ip,local_port,remote_ip,remote_port,bytes_acked,bytes_received) values(?,?,?,?,?,?)',(local_ip,local_port,remote_ip,remote_port,bytes_acked,bytes_received))
                elif table == "two":
                    insert_data.execute('insert into two(local_ip,local_port,remote_ip,remote_port,bytes_acked,bytes_received) values(?,?,?,?,?,?)',(local_ip,local_port,remote_ip,remote_port,bytes_acked,bytes_received))
        elif table == "net":
            for s in data:
                local_ip = s['local_ip']
                local_port = s['local_port']
                remote_ip = s['remote_ip']
                remote_port = s['remote_port']
                state = s['state']
                pid = s['pid']
                program_name = s['program_name']
                insert_data.execute('insert into net(local_ip,local_port,remote_ip,remote_port,state,pid,program_name) values(?,?,?,?,?,?,?)',(local_ip,local_port,remote_ip,remote_port,state,pid,program_name))
        elif table == "ps":
            for z in data:
                ps_pid = z['pid']
                ps_cpu = z['cpu']
                ps_men = z['men']
                insert_data.execute('insert into ps(pid,cpu,men) values(?,?,?)',(ps_pid,ps_cpu,ps_men))
        elif table == 'pidstat':
            for k in data:
                pidstat_pid = k['pid']
                pidstat_read = k['read']
                pidstat_write = k['write']
                insert_data.execute('insert into pidstat(pid,read,write) values(?,?,?)',(pidstat_pid,pidstat_read,pidstat_write))
        elif table == 'service':
            for p in data:
                service_pid = p[0]
                service_name = p[1]
                service_ip = p[2]
                service_port = p[3]
                service_uv = p[4]
                service_pv = p[5]
                service_up = p[6]
                service_down = p[7]
                service_cpu = p[8]
                service_men = p[9]
                insert_data.execute('insert into service(pid,service,bind_ip,bind_port,uv,pv,up,down,cpu,men) values(?,?,?,?,?,?,?,?,?,?)',(service_pid,service_name,service_ip,service_port,service_uv,service_pv,service_up,service_down,service_cpu,service_men))
        elif table == "process":
            for j in data:
                process_pid = j[0]
                process_name = j[1]
                process_uv = j[2]
                process_pv = j[3]
                process_up = j[4]
                process_down = j[5]  
                process_cpu = j[6]
                process_men = j[7]
                insert_data.execute('insert into process(pid,service,uv,pv,up,down,cpu,men) values(?,?,?,?,?,?,?,?)',(process_pid,process_name,process_uv,process_pv,process_up,process_down,process_cpu,process_men))
        elif table == "details":
            for d in data:
                details_client_ip = d[0]
                details_client_port = d[1]
                details_up = d[2]
                details_down = d[3]
                details_area = d[4]
                insert_data.execute('insert into details(client_ip,client_port,up,down,area) values(?,?,?,?,?)',(details_client_ip,details_client_port,details_up,details_down,details_area))
        else:
            print("传入错误表名。")
            sys.exit(0)

        conn.commit()
        insert_data.close()

    
    #流量转换单位
    def convert_network_traffic(self,size_in_kb, target_unit="auto"):
        units = ["KB", "MB", "GB", "TB", "PB", "EB", "ZB", "YB"]  # 注意：从KB开始
        factor = 1024.0

        if target_unit == "auto":
            size = size_in_kb
            if size == None:
                size = 0
            for u in units:
                if size < factor:
                    return f"{size:.2f} {u}"
                size /= factor
            return f"{size:.2f} {units[-1]}"

        elif target_unit in units:
            index = units.index(target_unit)
            size /= factor ** (index - 1)  # 因为size_in_kb已经是KB单位
            return f"{size:.2f} {target_unit}"

        else:
            raise ValueError(f"Invalid target unit: {target_unit}. Valid units are: {' '.join(units)}")

    #查询监听流量的数据
    def selectTotalListen(self,conn):
        select_linsten_sql = '''
        /*获取内部流量*/
             select 
                net_listen.pid as pid,
                net_listen.program_name  as program_name,
                net_listen.local_ip  as ip,
                net_listen.local_port  as port,
                COUNT(DISTINCT netstat_en.remote_ip) as ip_num,
                COUNT(netstat_en.remote_ip) as connect_ip,
                sum(two.bytes_acked - one.bytes_acked) / 1024 as upload,
                sum(two.bytes_received - one.bytes_received) / 1024 as download,
                ps.cpu as cpu,
                ps.men as men
            from (select * FROM net where state = "LISTEN" GROUP by local_port ) as net_listen
            LEFT JOIN (select * from net where state = "ESTABLISHED") as netstat_en on net_listen.local_port == netstat_en.local_port
            LEFT join one on one.local_port == netstat_en.local_port
                and one.remote_ip == netstat_en.remote_ip
                and one.remote_port == netstat_en.remote_port
            LEFT join two on one.local_ip == two.local_ip 
                and one.local_port == two.local_port 
                and one.remote_ip == two.remote_ip 
                and one.remote_port == two.remote_port 
            LEFT JOIN ps on ps.pid  == net_listen.pid 
            GROUP BY 
                net_listen.pid,
                net_listen.program_name,
                net_listen.local_ip,
                net_listen.local_port,
                net_listen.local_port,
                ps.cpu,
                ps.men
        ''' + self.order_by + ';'
        conn_db = conn.cursor()
        select_linsten_data = conn_db.execute(select_linsten_sql).fetchall()
        table = []
        for row in select_linsten_data:
            row_list = list(row)
            if row_list[6] == None or row_list[7] == None:
                row_list[6] = 0
                row_list[7] = 0
            row_list[6] = self.convert_network_traffic(row_list[6])
            row_list[7] = self.convert_network_traffic(row_list[7])
            row_list = [str(item) for item in row_list]
            table.append(tuple(row_list))
        conn_db.close()
        self.insertData(conn=conn, table="service", data=table)
        return table

    #查询程序外部连接的流量数据
    def selectTotalOut(self,conn):
        select_out_sql = '''
            /*获取访问外部的流量*/
                SELECT 
                    netstat.pid as pid,
                    netstat.program_name as program_name,
                    count(DISTINCT netstat.remote_ip) as ip_num,
                    count(netstat.remote_ip) as connect_ip,
                    ROUND(SUM(two.bytes_acked - one.bytes_acked) / 1024 ,2) as upload,
                    ROUND(SUM(two.bytes_received - two.bytes_received) /1024 ,2) as download,
                    ps.cpu as cpu,
                    ps.men as men
                FROM 
                    (SELECT * FROM net WHERE state = 'ESTABLISHED'and local_port not in (select local_port  from net WHERE state = 'LISTEN')) as netstat
                LEFT JOIN one on netstat.local_ip == one.local_ip 
                    AND netstat.local_port == one.local_port 
                    AND netstat.remote_ip == one.remote_ip
                    AND netstat.remote_port == one.remote_port 
                LEFT JOIN two on netstat.local_ip == two.local_ip
                    AND netstat.local_port == two.local_port 
                    AND netstat.remote_ip == two.remote_ip
                    AND netstat.remote_port == two.remote_port 
                LEFT JOIN ps on ps.pid == netstat.pid
                GROUP BY 
                    netstat.pid,
                    netstat.program_name
        ''' + self.order_by + ';'
        select_conn = conn.cursor()
        select_out_data = select_conn.execute(select_out_sql).fetchall()
        table = []
        for row2 in select_out_data:
            row_list = list(row2)
            # row_list.insert(2,"-")
            # row_list.insert(3,"-")
            row_list[4] = self.convert_network_traffic(row_list[4])
            row_list[5] = self.convert_network_traffic(row_list[5])
            if "-" in row_list[4]:
                row_list[4] = "0.00 KB"
            elif "-" in row_list[5]:
                row_list[5] = "0.00 KB"
            row_list = [str(item) for item in row_list]
            table.append(tuple(row_list))
        select_conn.close()
        self.insertData(conn=conn, table="process", data=table)
        return table


    #网卡数据处理
    def networkCardTraffic(self,data,data_sleep_1):
        table = []
        for one_line in data.splitlines():
            if "Receive" in one_line or "bytes" in one_line:
                continue
            one_line_list = one_line.split()
            one_face = one_line_list[0].replace(":","")
            one_rbytes = one_line_list[1]
            one_tbytes = one_line_list[9]
            for two_line in data_sleep_1.splitlines():
                contents = []
                two_line_list=two_line.split()
                two_face = two_line_list[0].replace(":","")
                if one_face == two_face:
                    two_rbytes = two_line_list[1]
                    two_tbytes = two_line_list[9]
                    rbytes = self.convert_network_traffic(size_in_kb=(int(two_rbytes) - int(one_rbytes)) / 1024)
                    tbytes = self.convert_network_traffic(size_in_kb=(int(two_tbytes) - int(one_tbytes)) / 1024)
                    contents.append(one_face)    
                    contents.append(tbytes)
                    contents.append(rbytes)
                    table.append(tuple(contents))
        return table

    #获取详细流量数据
    def selectDetails(self,conn,pid,port):
        select_conn = conn.cursor()
        if self.listen_or_outsude:
            select_established_sql = '''
            /*查询详细pid进程的连接信息*/
                SELECT 
                    netstat.remote_ip as remote_ip,
                    netstat.remote_port as remote_port,
                    (two.bytes_acked - one.bytes_acked) / 1024  as upload,
                    (two.bytes_received - one.bytes_received) / 1024  as download
                FROM 
                    (SELECT * FROM  net WHERE state = "ESTABLISHED") as netstat
                LEFT JOIN one ON netstat.local_ip == one.local_ip 
                    AND netstat.local_port == one.local_port 
                    AND netstat.remote_ip == one.remote_ip 
                    AND netstat.remote_port = one.remote_port 
                LEFT JOIN two ON netstat.local_ip == two.local_ip 
                    AND netstat.local_port == two.local_port 
                    AND netstat.remote_ip == two.remote_ip 
                    AND netstat.remote_port == two.remote_port 
                WHERE 
                    netstat.local_port =  ?
            ''' + self.pid_order_by + ';'
            select_established_data =select_conn.execute(select_established_sql,(port,)).fetchall()
        else:
            select_established_sql = '''
            /*查询详细pid进程的连接信息*/
                SELECT 
                    netstat.remote_ip as remote_ip,
                    netstat.remote_port as remote_port,
                    (two.bytes_acked - one.bytes_acked) / 1024  as upload,
                    (two.bytes_received - one.bytes_received) / 1024  as download
                FROM 
                    (SELECT * FROM  net WHERE state = "ESTABLISHED") as netstat
                LEFT JOIN one ON netstat.local_ip == one.local_ip 
                    AND netstat.local_port == one.local_port 
                    AND netstat.remote_ip == one.remote_ip 
                    AND netstat.remote_port = one.remote_port 
                LEFT JOIN two ON netstat.local_ip == two.local_ip 
                    AND netstat.local_port == two.local_port 
                    AND netstat.remote_ip == two.remote_ip 
                    AND netstat.remote_port == two.remote_port 
                WHERE 
                    netstat.pid = ?
            ''' + self.pid_order_by + ';'
            select_established_data =select_conn.execute(select_established_sql,(pid,)).fetchall()
        table = []
        for row in select_established_data:       
            row_list = list(row)
            row_list[2] = self.convert_network_traffic(row_list[2])
            row_list[3] = self.convert_network_traffic(row_list[3])
            row_list.append(self.get_ip_info(row_list[0]))
            table.append(tuple(row_list))
        select_conn.close()
        self.insertData(conn=conn, table="details", data=table)
        return table

    def selectServiceAll(self,conn):
        select_conn = conn.cursor()
        select_service_sql = '''
            select 
                *
            from service;
        '''
        select_service_data = select_conn.execute(select_service_sql).fetchall()
        select_conn.close()
        return select_service_data


    def selectProcessAll(self,conn):
        select_conn = conn.cursor()
        select_process_sql = '''
            select 
                *
            from process;
        '''
        select_process_data = select_conn.execute(select_process_sql).fetchall()
        select_conn.close()
        return select_process_data

    def selectDetailsAll(self,conn):
        select_conn = conn.cursor()
        select_details_sql = '''
            select 
                *
            from details;
        '''
        select_details_data = select_conn.execute(select_details_sql).fetchall()
        select_conn.close()
        return select_details_data

def main():
    #运行tui界面
    app = GridLayout()
    app.run() 

if __name__ == "__main__":
    main()
