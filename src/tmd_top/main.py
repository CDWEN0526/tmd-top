# -*- coding: utf-8 -*-
from textual.app import App,ComposeResult
from textual.widgets import Static,Header,Footer,DataTable,Input,Log,Button,TextArea
from textual.widgets.data_table import Column 
from itertools import cycle
from rich.text import Text
from textual import events
from textual._two_way_dict import TwoWayDict
import sqlite3
import sys
import subprocess
from textual.reactive import reactive
import difflib
import re
from textual import work
from textual.coordinate import Coordinate
from textual._two_way_dict import TwoWayDict
from typing_extensions import Self
import time
import random
import os
import json
from geoip2.database import Reader

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
            self.cursor_coordinate = Coordinate(0, 0)
            self.hover_coordinate = Coordinate(0, 0)
            self._label_column = Column(self._label_column_key, Text(), auto_width=True)
            self._labelled_row_exists = False
            self.refresh()
            #self.scroll_x = 0
            #self.scroll_y = 0
            self.scroll_target_x = 0
            self.scroll_target_y = 0
            return self

class GridLayout(App):
    CSS = """
    Screen {
        layout: grid;
        grid-size: 3 3;
        grid-columns: 20% 45% 35%;
        grid-rows: 45% 45% 10%;
    }

    Header {
        height: 6%;
        text-style: bold;
        text-align: center;
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

    #details {
        row-span:2;
    }

    #export_ip {
        row-span: 1;
        border: solid red;
        text-align: center;
        width: 100%;
    }

    #input_command {
        height: 100%;
        border: solid round  #f36c21 100%;
        padding: 1 2;
    }

    #input_command:focus {
        height: 100%;
        border: solid round  #d71345 100%;
        padding: 1 2;
    }

    #Introduction {
        height: 100%;
        border: solid round  #00BFFF 30%;
    }
    
    .box {
        height: 100%;
        border: solid round  #00BFFF 30%;
        padding: 1 2;
    }

    .box:focus {
        height: 100%;
        border: solid round #fcf16e 100%;
        padding: 1 2;
    }

    """
    IntroductionText = """
===Welcome to TMD-TOP===
按tab键切换窗口,按住shift键不放,鼠标可选复制;
Cpu, men 单位 %

author: Davin
gitee: https://gitee.com/Davin168/tmd-top
github: https://github.com/CDWEN0526/tmd-top
email: 949178863@qq.com
version: v2.1.3
geoip更新时间: 2024-08-13
更新: pip install tmd-top --upgrade
    """
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        ("q","quit","(退出)"),
        ('v','input_command','(输入PID)'),
        ('t','slow_sleep_time','(慢速刷新数据)'),
        ('y','sleep_time','(恢复数据刷新)'),
        ('c','sort_connect','(连接数排序)'),
        ('i','sort_ip','(IP数排序)'),
        ('u','sort_up','(上传排序)'),
        ('d','sort_down','(下载排序)'),   
        ('z','sort_cpu','(CPU排序)'), 
        ('x','sort_men','(内存排序)'),
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
    pid_number = reactive(None)
    davin = None
    sleep_time = 0.8
    listen_value = None
    outside_value = None
    ip = None
    log_value = None
    search_string = None
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTables(id="network", classes="box",name="network")
        yield DataTables(classes="box", id="listen",name="listen")
        yield DataTables(classes="box",id="details",name="details")
        yield Log(id="Introduction")
        yield DataTables(classes="box",id="outside",name="outside")
        yield Static('当前PID: None',classes="box",id="instruction_display")
        yield Input(placeholder="请输入搜索关键词",id="input_command")
        yield Button('[点击导出IP列表到当前路径下的ip.txt文件]',classes='box',id='export_ip')
        yield Footer()

    def on_mount(self) -> None:
        self.title = "TMD-TOP"
        self.query_one('#network').border_title = "网卡"
        self.query_one('#network').border_subtitle = "总共 0"
        self.query_one('#network').loading = True
        self.query_one('#listen').border_title = "监听服务"
        self.query_one('#listen').border_subtitle = "总共 0"
        self.query_one('#listen').loading = True
        self.query_one('#outside').border_title = "运行程序"
        self.query_one('#outside').border_subtitle = "总共 0"
        self.query_one('#outside').loading = True
        self.query_one('#details').border_title = "详细"
        self.query_one('#details').border_subtitle = "总共 0"
        self.query_one('#details').loading = True
        self.query_one('#Introduction').border_title = "日志"
        self.query_one('#instruction_display').border_title = 'PID'
        self.query_one('#input_command').border_title = '搜索'
        log = self.query_one(Log)
        log.write_line(self.IntroductionText)
        self.update_tables()
        network_table = self.query_one('#network')
        network_table.cursor_type = next(cycle(["row"]))
        #network_table.add_columns(*("网卡", "上传", "下载"))
        network_table.add_column("网卡",key='name')
        network_table.add_column("上传",key='up')
        network_table.add_column("下载",key='down')
        for row in self.network:
            styled_row = [
                Text(str(cell),style="##008000",justify="center") for cell in row
            ]
            network_table.add_row(*styled_row)

        listen_table = self.query_one('#listen')
        listen_table.cursor_type = next(cycle(["row"])) 
        listen_table.add_column("PID",key='pid')
        listen_table.add_column("名称",key='name')
        listen_table.add_column("监听地址",key='ip')
        listen_table.add_column("监听端口",key='port')
        listen_table.add_column("IP数",key='ip_number')
        listen_table.add_column("连接数",key='connect_number')
        listen_table.add_column("上传",key='up')
        listen_table.add_column("下载",key='down')
        listen_table.add_column("CPU",key='cpu')
        listen_table.add_column("内存",key='men')
        for row2 in self.listen:
            styled_row = [
                Text(str(cell2),style="##008000",justify="center") for cell2 in row2
            ]
            listen_table.add_row(*styled_row)
        
        details_table = self.query_one('#details')
        details_table.cursor_type = next(cycle(["row"])) 
        details_table.add_column("客户端IP",key='ip')
        details_table.add_column("客户端PORT",key='port')
        details_table.add_column("上传",key='up')
        details_table.add_column("下载",key='down')
        details_table.add_column("地区",key='area')
        for row3 in self.detailed:
            details_table.add_row(*row3)

    
        outside_table = self.query_one('#outside')
        outside_table.cursor_type = next(cycle(["row"])) 
        outside_table.add_column("PID",key='pid')
        outside_table.add_column("名称",key='name')
        outside_table.add_column("IP数",key='ip')
        outside_table.add_column("连接数",key='connect')
        outside_table.add_column("上传",key='up')
        outside_table.add_column("下载",key='down')
        outside_table.add_column("CPU",key='cpu')
        outside_table.add_column("内存",key='men')
        for row4 in self.outside:
            styled_row = [
                Text(str(cell4),style="##008000",justify="center") for cell4 in row4
            ]
            outside_table.add_row(*styled_row)

    #监视network变量的改变，改变则触发事件
    def watch_network(self) -> None:
        network_dom = self.query_one("#network")
        network_dom.clear()
        network_dom.add_rows(self.network)
        row_number = self.query_one('#network').row_count
        network_dom.border_subtitle = "总共 " + str(row_number)
        
    #监视listen变量的改变，改变则触发事件
    def watch_listen(self) -> None:
        listen_dom = self.query_one('#listen')
        listen_dom.clear()
        for i in self.listen:
            data = list(i)
            listen_dom.add_row(*data,key=str(i[0]) + "_" + str(i[1]) + "_" + str(i[2]) + "_" + str(i[3]) )
        if self.listen_value != None:
            try:
                index_data = listen_dom.get_row_index(row_key=str(self.listen_value[0] + "_" + self.listen_value[1] + "_" + self.listen_value[2] + "_" + self.listen_value[3]))
            except Exception:
                index_data = 0
            listen_dom.move_cursor(row=int(index_data))
        row_number = self.query_one('#listen').row_count
        listen_dom.border_subtitle = "总共 " + str(row_number)

    #监视outside变量的改变，改变则触发事件
    def watch_outside(self) -> None:
        outside_dom = self.query_one('#outside')
        outside_dom.clear()
        #outside_dom.add_rows(self.outside)
        for i in self.outside:
            data = list(i)
            outside_dom.add_row(*data,key=str(i[0]) + '_' + str(i[1]))
        if self.outside_value != None:
            try:
                index_data = outside_dom.get_row_index(row_key=str(self.outside_value[0] + "_" + self.outside_value[1]))
            except Exception:
                index_data = 0
            outside_dom.move_cursor(row=int(index_data))
        row_number = self.query_one('#outside').row_count
        outside_dom.border_subtitle = "总共 " + str(row_number)
    
    #监视detailed变量的改变，改变则触发事件
    def watch_detailed(self) -> None:
        log = self.query_one(Log)
        details_dom = self.query_one('#details')
        #框架bug，处理手段：清空数据
        details_dom.rows = {}
        details_dom._row_locations = TwoWayDict({})
        details_dom.clear()
        for i in self.detailed:
            data = list(i)
            details_dom.add_row(*data,key=str(i[0]) + '_' + str(i[1]))
        row_number = self.query_one('#details').row_count
        details_dom.border_subtitle = "总共 " + str(row_number)
        
    #点击表格触发事件
    def on_data_table_row_selected(self,event):
        log = self.query_one(Log)
        value =  event.control.get_row(event.row_key)
        if self.log_value != value[0]:
            if event.control.name == 'listen':
                self.listen_value = value
                self.pid_number = value[0]
                cmd = self.selectPidCommand(value[0])
                log.write_line('\n查询: \n')
                log.write_line('  PID的指令: ' + str(cmd))
                log.write_line('  PID是: ' + str(self.pid_number))
                instruction_display = self.query_one("#instruction_display")
                instruction_display.update('当前PID: ' + value[0])
                self.outside_value = None
                self.log_value = value[0]
            if event.control.name == 'outside':
                self.outside_value = value
                self.pid_number = value[0]
                cmd = self.selectPidCommand(value[0])
                log.write_line('\n查询: \n')
                log.write_line('  PID的指令: ' + str(cmd))
                log.write_line('  PID是: ' + str(self.pid_number))
                instruction_display = self.query_one("#instruction_display")
                instruction_display.update('当前PID: ' + value[0])
                self.listen_value = None
                self.log_value = value[0]
            if event.control.name == "details":
                log.write_line('\n选择的IP: \n  ' + str(value[0]))
                self.log_value = value[0]
                #使用api请求显示详细的ip信息
                #self.identify_address(value[1])


    #输入框查询pid回车触发事件
    def on_key(self,event: events.Key):
        self.davin = event.key
        if event.key == 'enter':
            pass

    #按钮消息接收(导出ip按钮)
    def on_button_pressed(self, event: Button.Pressed) -> None:
        log = self.query_one(Log)
        log.write_line('\n开始导出IP列表信息,耐心等待...')
        if event.button.id == 'export_ip':
            export_file_path = os.getcwd() + '/' + 'ip.txt'
            with open(export_file_path, 'w') as f:
                for i in self.detailed:
                    keys = ['ip','port','up','down','location']
                    f.write(json.dumps(dict(zip(keys,i)),ensure_ascii=False) + '\n')
            log.write_line('导出IP详情结束')
            log.write_line('导出路径: ' + export_file_path)
    #快捷键绑定事件
    def action_slow_sleep_time(self) -> None:
        self.sleep_time = 5

    def action_sleep_time(self) -> None:
        self.sleep_time = 0.8


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
    #快捷键绑定事件
    def action_sort_ip(self) -> None:
        self.order_by = """
            ORDER BY 
                ip_num DESC
            """
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
    #快捷绑定事件
    def action_sort_cpu(self) -> None:
        self.order_by = """
            ORDER BY 
                cpu DESC
            """
    def action_sort_men(self) -> None:
        self.order_by = """
            ORDER BY 
                men DESC
            """
    def action_sort_io_r(self) -> None:
        self.order_by = """
            ORDER BY 
                read DESC
            """
    def action_sort_io_w(self) -> None:
        self.order_by = """
            ORDER BY 
                write DESC
            """
    #异步识别ip，使用太平洋网络接口
    # @work(exclusive=True,thread=True)
    # async def identify_address(self,ip):
    #     try:
    #         headers = {
    #             'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
    #         }
    #         url = 'http://whois.pconline.com.cn/ipJson.jsp?ip={}&json=true'.format(ip)

    #         response = requests.get(url=url, headers=headers, timeout=3)
    #         ret = response.json()['addr']
    #         log = self.query_one(Log)
    #         log.write_line(str(ret) + '\n')
    #     except Exception:  
    #         log = self.query_one(Log) 
    #         log.write_line('识别IP失败\n')

    #定时器执行的任务
    @work(exclusive=True,thread=True)
    async def update_tables(self) -> None:
        current_module_path = os.path.dirname(os.path.abspath(__file__))
        db_file_path = os.path.join(current_module_path, 'data/tmd-top.db')
        while True:
            conn = self.connectSqlite(db_file_path)
            cat_command = self.localExecuteCommand("sudo cat /proc/net/dev")
            ss_command = self.localExecuteCommand('sudo ss -ni  state established  && echo "Davin system" && sleep 1 && sudo ss -ni  state established')
            cat_command_sleep_1 = self.localExecuteCommand("sudo cat /proc/net/dev")
            netstat_command = self.localExecuteCommand('sudo ss -atpn')
            ps_command = self.localExecuteCommand("sudo ps axu | grep -v '%CPU' | grep -v grep")
            one,two = self.ssDataProcessing(ss_command)
            net = self.netstatDataProcessing(netstat_command)
            ps = self.psDataProcessing(ps_command)
            self.insertData(conn=conn,table='one',data=one)
            self.insertData(conn=conn,table='two',data=two)
            self.insertData(conn=conn,table="net",data=net)
            self.insertData(conn=conn,table='ps',data=ps)
            self.listen = self.search(name='listen',data=self.selectTotalListen(conn=conn))
            self.outside = self.search(name='outside',data=self.selectTotalOut(conn=conn))
            self.network = self.search(name='network',data=self.networkCardTraffic(cat_command,cat_command_sleep_1))
            if self.pid_number:
                self.detailed = self.search(name='detailed',data=self.selectDetails(conn=conn,pid=self.pid_number))
            self.query_one('#outside').loading = False
            self.query_one('#network').loading = False
            self.query_one('#listen').loading = False
            self.query_one('#details').loading = False
            time.sleep(self.sleep_time)

    def search(self,name,data) -> None:
        search_string = self.query_one("#input_command").value
        if name == 'listen':
            listen = [t for t in data if any(search_string in s for s in t)]
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
            outside = [t for t in data if any(search_string in s for s in t)]
            if outside:
                return outside
            else:
                return data
        elif name == 'detailed':
            detailed = [t for t in data if any(search_string in s for s in t)]
            if detailed:
                return detailed
            else:
                return data

    #使用geoip获取ip信息
    def get_ip_info(self,ip_address):
        language = 'zh-CN'
        # 设置数据库文件的相对路径（假设它在脚本同一目录下）
        current_module_path = os.path.dirname(os.path.abspath(__file__))
        database_path = os.path.join(current_module_path, 'data/GeoLite2-City.mmdb')
        with Reader(database_path) as geoip_reader:
            try:
                response = geoip_reader.city(ip_address)

                # 获取详细的地理位置信息，并优先显示中文名称（如果有）
                country_name = response.country.names.get(language) or 'null'
                city_name = response.city.names.get(language) or 'null'
                subdivision_name = 'null'
                if len(response.subdivisions) > 0:
                    subdivision_name = response.subdivisions[0].names.get(language) or 'null'
                return (f"{country_name}/{subdivision_name}/{city_name}")

            except Exception:
                return ("null")

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
    def connectSqlite(self,db_path):
        conn = sqlite3.connect(db_path)
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
        conn.commit()
        cursor.close()
        return conn

    # #pidstat命令结果数据处理
    # def pidstatDataProcessing(self,data):
    #     pidstat_data_all = []
    #     for line in data.splitlines():
    #         pidstat_dict = {}
    #         pidstat_pid_info = line.split()
    #         pidstat_dict['pid'] = pidstat_pid_info[2]
    #         pidstat_dict['read'] = pidstat_pid_info[3]
    #         pidstat_dict['write'] = pidstat_pid_info[4]
    #         pidstat_data_all.append(pidstat_dict)
    #     return pidstat_data_all

    #ps命令结果数据处理
    def psDataProcessing(self,data):
        ps_data_all = []
        for line in data.splitlines():
            ps_dict = {}
            ps_pid_info = line.split()
            ps_dict['pid'] = ps_pid_info[1]
            ps_dict['cpu'] = ps_pid_info[2]
            ps_dict['men'] = ps_pid_info[3]
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
                item = item.replace('::ffff:','')
                if (re.match(ipv4_pattern, item) or re.match(ipv6_pattern, item)):
                        one_tcp_rinse_list.append(item)
                elif "bytes_acked" in item or "bytes_received" in item:
                    one_tcp_rinse_list.append(item)
            try:
                one_local_info = one_tcp_rinse_list[0].replace('::ffff:','').split(":")
            except IndexError:
                continue
            one_local_ip = one_local_info[0]
            one_local_port = one_local_info[1]
            one_remote_info = one_tcp_rinse_list[1].replace('::ffff:','').split(":")
            one_remote_ip = one_remote_info[0]
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
                item2 = item2.replace('::ffff:','')
                if (re.match(ipv4_pattern, item2) or re.match(ipv6_pattern, item2)):
                        two_tcp_rinse_list.append(item2)
                elif "bytes_acked" in item2 or "bytes_received" in item2:
                    two_tcp_rinse_list.append(item2)
            try:
                two_local_info = two_tcp_rinse_list[0].replace('::ffff:','').split(":")
            except IndexError:
                continue
            two_local_ip = two_local_info[0]
            two_local_port = two_local_info[1]
            two_remote_info = two_tcp_rinse_list[1].replace('::ffff:','').split(":")
            two_remote_ip = two_remote_info[0]
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
                local_info = netstat_all_data[3].replace('[::]','::')
                local_ip = local_info.split(':')[0]
                local_port = local_info.split(':')[1]
                remote_info = netstat_all_data[4].replace('[::]','::')
                remote_ip = remote_info.split(':')[0]
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
                    local_ip = local_info
                if local_port == "":
                    local_port = local_info.split(':')[-1]
                if remote_ip == "":
                    remote_ip = remote_info
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
                COUNT(DISTINCT one.remote_ip) as ip_num,
                COUNT(one.remote_ip) as connect_ip,
                sum(two.bytes_acked - one.bytes_acked) / 1024 as upload,
                sum(two.bytes_received - one.bytes_received) / 1024 as download,
                ps.cpu as cpu,
                ps.men as men
            from (select * FROM net where state = "LISTEN" ) as net_listen
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
        select_conn = conn.cursor()
        select_linsten_data = select_conn.execute(select_linsten_sql).fetchall() 
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
        select_conn.close()
        return table

    #查询程序外部连接的流量数据
    def selectTotalOut(self,conn):
        select_out_sql = '''
            /*获取访问外部的流量*/
                SELECT 
                    netstat.pid as pid,
                    netstat.program_name as program_name,
                    count(DISTINCT netstat.local_ip) as ip_num,
                    count(netstat.local_ip) as connect_ip,
                    ROUND(SUM(two.bytes_acked - one.bytes_acked) / 1024 ,2) as upload,
                    ROUND(SUM(two.bytes_received - two.bytes_received) /1024 ,2) as download,
                    ps.cpu as cpu,
                    ps.men as men
                FROM 
                    (SELECT * FROM net WHERE state = 'ESTABLISHED'and local_port not in (select local_port  from net WHERE state = 'LISTEN')) as netstat
                LEFT JOIN one on netstat.local_ip == one.local_ip 
                    AND netstat.local_port == one.local_port 
                LEFT JOIN two on netstat.local_ip == two.local_ip
                    AND netstat.local_port == two.local_port 
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
        return table


    #网卡数据处理
    def networkCardTraffic(self,data,data_sleep_1):
        table = []
        for one_line in data.splitlines():
            if "Receive" in one_line or "bytes" in one_line:
                continue
            one_line_list = one_line.split()
            one_face = one_line_list[0]
            one_rbytes = one_line_list[1]
            one_tbytes = one_line_list[9]
            for two_line in data_sleep_1.splitlines():
                contents = []
                two_line_list=two_line.split()
                two_face = two_line_list[0]
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
    def selectDetails(self,conn,pid):
        select_conn = conn.cursor()
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
                or netstat.local_port in (SELECT local_port from net WHERE pid = ?)
        ''' + self.pid_order_by + ';'
        select_established_data =select_conn.execute(select_established_sql,(pid,pid)).fetchall()
        table = []
        for row in select_established_data:       
            row_list = list(row)
            row_list[2] = self.convert_network_traffic(row_list[2])
            row_list[3] = self.convert_network_traffic(row_list[3])
            row_list.append(self.get_ip_info(row_list[0]))
            table.append(tuple(row_list))
        select_conn.close()
        return table

def command_exists(cmd):
    return subprocess.call(['which', cmd], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL) == 0

def main():
    #运行tui界面
    app = GridLayout()
    app.run()   

if __name__ == "__main__":
    main()