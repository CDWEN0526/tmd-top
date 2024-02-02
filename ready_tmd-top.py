#!/usr/local/python38/bin/python3
# -*- coding: utf-8 -*-
from textual.app import App,ComposeResult
from textual.widgets import Static,Header,Footer,DataTable,Input,Log
from textual.widgets.data_table import Column 
from itertools import cycle
from rich.text import Text
from textual import events
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
import requests

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
            # self.hover_coordinate = Coordinate(0, 0)
            self._label_column = Column(self._label_column_key, Text(), auto_width=True)
            self._labelled_row_exists = False
            self.refresh()
            # self.scroll_x = 0
            # self.scroll_y = 0
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
        row-span:3;
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
===欢迎使用TMD-TOP===
按tab键切换窗口,按住shift键不放,鼠标可选复制;
cpu、men 单位是 %
io 单位是 KB

author: Davin
gitee: https://gitee.com/Davin168/tmd-top
email: 949178863@qq.com
version: v2.0.0

    """
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [
        ("q","quit","退出"),
        ('v','input_command','输入指令'),
        ('t','slow_sleep_time','低速刷新数据'),
        ('y','sleep_time','恢复刷新速度'),
        ('c','sort_connect','连接数量排序'),
        ('i','sort_ip','ip数量排序'),
        ('u','sort_up','上传排序'),
        ('d','sort_down','下载排序'),   
        ('z','sort_cpu','cpu排序'), 
        ('x','sort_men','内存排序'),
        ('n','sort_io_r','io读排序'),
        ('m','sort_io_w','io写排序')
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
    ip = None
    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield DataTables(id="network", classes="box",name="network")
        yield DataTables(classes="box", id="listen",name="listen")
        yield DataTables(classes="box",id="details",name="details")
        yield Log(id="Introduction")
        yield DataTables(classes="box",id="outside",name="outside")
        yield Static('当前查询的PID是: None',classes="box",id="instruction_display")
        yield Input(placeholder="请输入PID号按回车",id="input_command")
        yield Footer()

    def on_mount(self) -> None:
        self.title = "TMD-TOP"
        self.query_one('#network').border_title = "网卡流量"
        self.query_one('#network').border_subtitle = "总共0条"
        self.query_one('#network').loading = True
        self.query_one('#listen').border_title = "服务监听流量"
        self.query_one('#listen').border_subtitle = "总共0条"
        self.query_one('#listen').loading = True
        self.query_one('#outside').border_title = "请求外部流量"
        self.query_one('#outside').border_subtitle = "总共0条"
        self.query_one('#outside').loading = True
        self.query_one('#details').border_title = "详细pid流量"
        self.query_one('#details').border_subtitle = "总共0条"
        self.query_one('#details').loading = True
        self.query_one('#Introduction').border_title = "信息面板"
        self.query_one('#instruction_display').border_title = '提示'
        self.query_one('#input_command').border_title = '查询PID'
        log = self.query_one(Log)
        log.write_line(self.IntroductionText)
        self.update_tables()
        network_table = self.query_one('#network')
        network_table.cursor_type = next(cycle(["row"]))
        network_table.add_columns(*("网卡", "上传", "下载"))
        for row in self.network:
            styled_row = [
                Text(str(cell),style="##008000",justify="center") for cell in row
            ]
            network_table.add_row(*styled_row)

        listen_table = self.query_one('#listen')
        listen_table.cursor_type = next(cycle(["row"])) 
        listen_table.add_columns(*("pid", "名称", "监听地址","监听端口","ip数量","连接数量","上传","下载","cpu","men","io_r","io_w"))
        for row2 in self.listen:
            styled_row = [
                Text(str(cell2),style="##008000",justify="center") for cell2 in row2
            ]
            listen_table.add_row(*styled_row)
        
        details_table = self.query_one('#details')
        details_table.cursor_type = next(cycle(["row"])) 
        details_table.add_columns(*("名称","客户机地址","客户机端口","上传","下载"))
        for row3 in self.detailed:
            styled_row = [
                Text(str(cell3),style="##008000",justify="center") for cell3 in row3
            ]
            details_table.add_row(*styled_row)
    
        outside_table = self.query_one('#outside')
        outside_table.cursor_type = next(cycle(["row"])) 
        outside_table.add_columns(*("pid", "名称","ip数量","连接数量","上传","下载","cpu","men","io_r","io_w"))
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
        network_dom.border_subtitle = "总共" + str(row_number) + '条'
        
    #监视listen变量的改变，改变则触发事件
    def watch_listen(self) -> None:
        listen_dom = self.query_one('#listen')
        listen_dom.clear()
        listen_dom.add_rows(self.listen)
        row_number = self.query_one('#listen').row_count
        listen_dom.border_subtitle = "总共" + str(row_number) + '条'

    #监视outside变量的改变，改变则触发事件
    def watch_outside(self) -> None:
        outside_dom = self.query_one('#outside')
        outside_dom.clear()
        outside_dom.add_rows(self.outside)
        row_number = self.query_one('#outside').row_count
        outside_dom.border_subtitle = "总共" + str(row_number) + '条'
    
    #监视detailed变量的改变，改变则触发事件
    def watch_detailed(self) -> None:
        details_dom = self.query_one('#details')
        details_dom.clear()
        details_dom.add_rows(self.detailed)
        row_number = self.query_one('#details').row_count
        details_dom.border_subtitle = "总共" + str(row_number) + '条'
        
    #点击表格触发事件
    def on_data_table_row_selected(self,event):
        if event.control.name == 'listen':
            log = self.query_one(Log)
            value =  event.control.get_row(event.row_key)
            self.pid_number = value[0]
            cmd = self.selectPidCommand(value[0])
            log.write_line('\n查询到PID执行的命令是: \n' + str(cmd))
            instruction_display = self.query_one("#instruction_display")
            instruction_display.update('当前查询的pid是: ' + value[0])
        if event.control.name == 'outside':
            log = self.query_one(Log)
            value =  event.control.get_row(event.row_key)
            self.pid_number = value[0]
            cmd = self.selectPidCommand(value[0])
            log.write_line('\n查询到PID执行的命令是: \n' + str(cmd))
            instruction_display = self.query_one("#instruction_display")
            instruction_display.update('当前查询的pid是: ' + value[0])
        if event.control.name == "details":
            log = self.query_one(Log)
            value =  event.control.get_row(event.row_key)
            log.write_line('\n当前选项IP信息是: \n' + str(value[1]))
            self.identify_address(value[1])

    #输入框查询pid回车触发事件
    def on_key(self,event: events.Key):
        self.davin = event.key
        if event.key == 'enter':
            instruction_display = self.query_one("#instruction_display")
            input_value = self.query_one("#input_command")
            instruction_display.update('当前查询的pid是: ' + input_value.value)
            self.pid_number = input_value.value
            input_value.clear()

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
    @work(exclusive=True,thread=True)
    async def identify_address(self,ip):
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:122.0) Gecko/20100101 Firefox/122.0'
            }
            url = 'http://whois.pconline.com.cn/ipJson.jsp?ip={}&json=true'.format(ip)

            response = requests.get(url=url, headers=headers, timeout=3)
            ret = response.json()['addr']
            log = self.query_one(Log)
            log.write_line(str(ret) + '\n')
        except Exception:  
            log = self.query_one(Log) 
            log.write_line('识别IP失败\n')
            
    #定时器执行的任务
    @work(exclusive=True,thread=True)
    async def update_tables(self) -> None:
        while True:
            conn = self.connectSqlite("/tmp/sql.db")
            cat_command = self.localExecuteCommand("cat /proc/net/dev")
            ss_command = self.localExecuteCommand('ss -ni  state established  && echo "Davin system" && sleep 1 && ss -ni  state established')
            cat_command_sleep_1 = self.localExecuteCommand("cat /proc/net/dev")
            netstat_command = self.localExecuteCommand('netstat -atpn')
            ps_command = self.localExecuteCommand("ps axu | grep -v '%CPU' | grep -v grep")
            pidstat_command = self.localExecuteCommand("pidstat -d | grep -v 'kB_rd/s' | grep -v 'CPU)' | grep  -v '^$'")
            one,two = self.ssDataProcessing(ss_command)
            net = self.netstatDataProcessing(netstat_command)
            ps = self.psDataProcessing(ps_command)
            pidstat = self.pidstatDataProcessing(pidstat_command)
            self.insertData(conn=conn,table='one',data=one)
            self.insertData(conn=conn,table='two',data=two)
            self.insertData(conn=conn,table="net",data=net)
            self.insertData(conn=conn,table='ps',data=ps)
            self.insertData(conn=conn,table='pidstat',data=pidstat)
            self.listen = self.selectTotalListen(conn=conn)
            self.outside = self.selectTotalOut(conn=conn)
            self.network = self.networkCardTraffic(cat_command,cat_command_sleep_1)
            if self.pid_number:
                self.detailed = self.selectDetails(conn=conn,pid=self.pid_number)
            self.query_one('#outside').loading = False
            self.query_one('#network').loading = False
            self.query_one('#listen').loading = False
            self.query_one('#details').loading = False
            time.sleep(self.sleep_time)


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
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败：{e}")
            sys.exit(1)

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

    #pidstat命令结果数据处理
    def pidstatDataProcessing(self,data):
        pidstat_data_all = []
        for line in data.splitlines():
            pidstat_dict = {}
            pidstat_pid_info = line.split()
            pidstat_dict['pid'] = pidstat_pid_info[3]
            pidstat_dict['read'] = pidstat_pid_info[4]
            pidstat_dict['write'] = pidstat_pid_info[5]
            pidstat_data_all.append(pidstat_dict)
        return pidstat_data_all

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
            if 'Active Internet' in i or 'Recv-Q Send-Q' in i:
                continue
            else:
                netstat_all_data = i.split()
                local_info = netstat_all_data[3]
                local_ip = local_info.split(':')[0]
                local_port = local_info.split(':')[1]
                remote_info = netstat_all_data[4]
                remote_ip = remote_info.split(':')[0]
                remote_port = remote_info.split(":")[1]
                state = netstat_all_data[5]
                pid_programName = ",".join(netstat_all_data[6:]).split('/',maxsplit=1)
                pid = "-" if pid_programName[0] == "-" else pid_programName[0]
                try:
                    program_name =pid_programName[1]
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
            print("传入错误表名。")
            sys.exit(1)
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
            sys.exit(1)
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
                listen.pid as pid,
                listen.program_name as program_name,
                listen.local_ip as ip,
                listen.local_port as port,
                COUNT(DISTINCT one.remote_ip) as ip_num, 
                COUNT(one.remote_ip) as connect_ip,
                sum(two.bytes_acked - one.bytes_acked) / 1024  as upload,
                sum(two.bytes_received - one.bytes_received) / 1024  as download,
                ps.cpu as cpu,
                ps.men as men,
                pidstat.read as read,
                pidstat.write as write
            from
                one
                JOIN two on one.remote_ip = two.remote_ip
                and one.remote_port = two.remote_port
                and one.local_ip = two.local_ip
                and one.local_port = two.local_port
                JOIN (SELECT *  from net WHERE net.state = "LISTEN") as listen  
                on  one.local_port == listen.local_port 
                JOIN ps on listen.pid == ps.pid
                JOIN pidstat on listen.pid == pidstat.pid
            WHERE 
                one.local_port in (SELECT DISTINCT local_port  from net WHERE net.state = "LISTEN")
            GROUP BY 
                one.local_ip,
                one.local_port,
                listen.remote_ip,
                listen.remote_port,
                listen.pid,
                ps.cpu,
                ps.men,
                pidstat.read,
                pidstat.write
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
                connected.pid as pid,
                connected.program_name as program_name,
                COUNT(DISTINCT one.local_ip) as ip_num,
                COUNT(one.local_ip) as connect_ip,
                sum(two.bytes_acked - one.bytes_acked) / 1024  as upload,
                sum(two.bytes_received - one.bytes_received) / 1024  as download,
                ps.cpu as cpu,
                ps.men as men,
                pidstat.read as read,
                pidstat.write as write
            FROM 
                one 
            JOIN two on one.local_ip == two.local_ip 
                AND one.local_port == two.local_port 
                AND one.remote_ip == two.remote_ip 
                AND one.remote_port == two.remote_port 
            JOIN (SELECT * FROM net WHERE state="ESTABLISHED") as connected ON  one.local_ip == connected.local_ip
                AND one.local_port == connected.local_port
                AND one.remote_ip == connected.remote_ip
                AND one.remote_port == connected.remote_port
            JOIN ps on ps.pid == connected.pid
            JOIN pidstat on connected.pid == pidstat.pid
            WHERE 
                one.local_port NOT IN (SELECT local_port FROM net WHERE state="LISTEN")
            GROUP BY 
                connected.pid,
                connected.program_name,
                ps.cpu,
                ps.men,
                pidstat.read,
                pidstat.write
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
            connected.program_name as program_name,                                            
            one.remote_ip as remote_ip,
            one.remote_port as remote_port,
            (two.bytes_acked - one.bytes_acked) / 1024  as upload,
            (two.bytes_received - one.bytes_received) / 1024  as download
        FROM 
            one
        JOIN two on one.local_ip == two.local_ip 
            AND one.local_port == two.local_port 
            AND one.remote_ip == two.remote_ip 
            AND one.remote_port == two.remote_port
        JOIN (SELECT * FROM net WHERE state = "ESTABLISHED") as connected ON one.local_ip == connected.local_ip
            AND one.local_port == connected.local_port
            AND one.remote_ip == connected.remote_ip
            AND one.remote_port == connected.remote_port
        WHERE 
            connected.pid = ?
            or connected.local_port in (SELECT local_port from net where pid = ?)
        ''' + self.pid_order_by + ';'
        select_established_data =select_conn.execute(select_established_sql,(pid,pid)).fetchall()
        table = []
        for row in select_established_data:       
            row_list = list(row)
            row_list[-2] = self.convert_network_traffic(row_list[-2])
            row_list[-1] = self.convert_network_traffic(row_list[-1])
            table.append(tuple(row_list))
        select_conn.close()
        return table

if __name__ == "__main__":
    app = GridLayout()
    app.run()