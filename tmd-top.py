#!/usr/bin/python3
# -*- coding:utf-8 -*-
import sqlite3
import sys
import difflib
import os
import asyncio
import subprocess
from rich.console import Console
from rich.table import Column, Table
from rich import print as printr
import re
from rich.layout import Layout
from rich.panel import Panel
from rich.padding import Padding
import getpass
import time

def pidRichTable():
    console = Console()
    table = Table(show_header=True, header_style="bold magenta",title="程序流量")
    table.add_column("name")
    table.add_column("local ip")
    table.add_column("local port")
    table.add_column("remote ip")
    table.add_column("remote port")
    table.add_column("up")
    table.add_column("down")
    return table,console

def networkCard():
    console = Console()
    table = Table(show_header=True, header_style="bold magenta",title="网卡流量")
    table.add_column("network")
    table.add_column("up")
    table.add_column("down")
    return table,console

def homeListenRichTable():
    console = Console()
    table = Table(show_header=True, header_style="bold magenta",title="监听服务流量")
    table.add_column("pid")
    table.add_column("name")
    table.add_column("listen addr")
    table.add_column("listen port")
    table.add_column("ip number")
    table.add_column("conn ip")
    table.add_column("up")
    table.add_column("down")
    return table,console

def homeServerRichTable():
    console = Console()
    table = Table(show_header=True, header_style="bold magenta",title="程序访外流量")
    table.add_column("pid")
    table.add_column("name")
    table.add_column("ip number")
    table.add_column("conn ip")
    table.add_column("up")
    table.add_column("down")
    return table,console

#非远程执行命令
def localExecuteCommand(command):
    if sys.version_info >= (3, 7):
        # Python 3.7及以上版本
        try:
            result = subprocess.run(command, shell=True, capture_output=True, text=True)
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, command, result.stderr)
            return result.stdout
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败：{e}")
            sys.exit(1)
    else:
        # Python 3.6及更低版本
        try:
            result = subprocess.run(command, shell=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
            output_bytes = result.stdout
            output_text = output_bytes.decode(sys.stdout.encoding)  # 解码为文本
            if result.returncode != 0:
                raise subprocess.CalledProcessError(result.returncode, command, output_text)
            return output_text
        except subprocess.CalledProcessError as e:
            print(f"命令执行失败：{e}")
            sys.exit(1)


#连接sqlite数据库
def connectSqlite(db_path):
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

    conn.commit()
    cursor.close()
    return conn

#插入数据
def insertData(conn,table,data):
    insert_data = conn.cursor()
    if table == "one":
        insert_data.execute('delete from one;')
    elif table == 'two':
        insert_data.execute('delete from two;')
    elif table == "net":
        insert_data.execute('delete from net;')
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
    else:
        print("传入错误表名。")
        sys.exit(1)
    conn.commit()
    insert_data.close()

#处理第一次数据和第二次的数据，过滤掉无用数据。
def ssDataProcessing(data):
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
def netstatDataProcessing(data):
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

#获取详细流量数据
def selectDetails(conn,pid):
    select_conn = conn.cursor()
    select_established_sql = '''
    /*查询详细pid进程的连接信息*/
    SELECT 
        connected.program_name as program_name,                                            
        one.local_ip as local_ip,
        one.local_port as local_ip,
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
    ''' + pid_order_by + limit + ';'
    select_established_data =select_conn.execute(select_established_sql,(pid,pid)).fetchall()
    table,console = pidRichTable()
    for row in select_established_data:       
        row_list = list(row)
        row_list[-2] = convert_network_traffic(row_list[-2])
        row_list[-1] = convert_network_traffic(row_list[-1])
        table.add_row(*row_list)
    #console.print(table)
    select_conn.close()
    return table

#查询监听流量的数据
def selectTotalListen(conn):
    select_linsten_sql = '''
    /*获取内部流量*/
        select
            listen.pid as pid,
            listen.program_name as program_name,
            listen.remote_ip as ip,
            listen.local_port as port,
            COUNT(DISTINCT one.remote_ip) as ip_num, 
            COUNT(one.remote_ip) as connect_ip,
            sum(two.bytes_acked - one.bytes_acked) / 1024  as upload,
            sum(two.bytes_received - one.bytes_received) / 1024  as download
        from
            one
            JOIN two on one.remote_ip = two.remote_ip
            and one.remote_port = two.remote_port
            and one.local_ip = two.local_ip
            and one.local_port = two.local_port
            JOIN (SELECT *  from net WHERE net.state = "LISTEN") as listen  
            on  one.local_port == listen.local_port 
        WHERE 
            one.local_port in (SELECT DISTINCT local_port  from net WHERE net.state = "LISTEN")
        GROUP BY 
            one.local_ip,
            one.local_port,
            listen.remote_ip,
            listen.remote_port,
            listen.pid
    ''' + order_by
    select_conn = conn.cursor()
    select_linsten_data = select_conn.execute(select_linsten_sql).fetchall() 
    table,console = homeListenRichTable()
    for row in select_linsten_data:
        row_list = list(row)
        if row_list[-2] == None or row_list[-1] == None:
            row_list[-2] = "0"
            row_list[-1] = "0"
        row_list[-2] = convert_network_traffic(row_list[-2])
        row_list[-1] = convert_network_traffic(row_list[-1])
        row_list = [str(item) for item in row_list]
        table.add_row(*row_list)
    #console.print(table)
    select_conn.close()
    return table

#查询程序外部连接的流量数据
def selectTotalOut(conn):
    select_out_sql = '''
        /*获取访问外部的流量*/
        SELECT 
            connected.pid as pid,
            connected.program_name as program_name,
            COUNT(DISTINCT one.local_ip) as ip_num,
            COUNT(one.local_ip) as connect_ip,
            sum(two.bytes_acked - one.bytes_acked) / 1024  as upload,
            sum(two.bytes_received - one.bytes_received) / 1024  as download
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
        WHERE 
            one.local_port NOT IN (SELECT local_port FROM net WHERE state="LISTEN")
        GROUP BY 
            connected.pid,
            connected.program_name
    ''' + order_by
    select_conn = conn.cursor()
    select_out_data = select_conn.execute(select_out_sql).fetchall()
    table,console = homeServerRichTable()
    for row2 in select_out_data:
        row_list = list(row2)
        row_list[-2] = convert_network_traffic(row_list[-2])
        row_list[-1] = convert_network_traffic(row_list[-1])
        if "-" in row_list[-2]:
            row_list[-2] = "0.00 KB"
        elif "-" in row_list[-1]:
            row_list[-1] = "0.00 KB"
        row_list = [str(item) for item in row_list]
        table.add_row(*row_list)
    select_conn.close()
    return table

#流量转换单位
def convert_network_traffic(size_in_kb, target_unit="auto"):
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

#网卡数据处理
def networkCardTraffic(data,data_sleep_1):
    table,console = networkCard()
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
                rbytes = convert_network_traffic(size_in_kb=(int(two_rbytes) - int(one_rbytes)) / 1024)
                tbytes = convert_network_traffic(size_in_kb=(int(two_tbytes) - int(one_tbytes)) / 1024)
                contents.append(one_face)
                contents.append(rbytes)    
                contents.append(tbytes)
                table.add_row(*contents) 
    return table     

#获取数据并写入数据库
async def run(stop_event):
    #ssh = connectSsh('120.79.14.227','22122','root',key='e:/key/davin.pem')
    conn = connectSqlite("/tmp/sql.db")
    content = 'Welcome to TMD-TOP\n'
    content += 'Author:Davin | gitee:https://gitee.com/Davin168/tmd-top \n'
    content += 'Note:TMD-TOP程序会监控键盘输入,输入指令是隐藏无回显的,回车执行指令。\n'

    while True:
        if program_quit:
            stop_event.set()
        cat_command = localExecuteCommand("cat /proc/net/dev")
        ss_command = localExecuteCommand('ss -ni  state established  && echo "Davin system" && sleep 1 && ss -ni  state established')
        cat_command_sleep_1 = localExecuteCommand("cat /proc/net/dev")
        netstat_command = localExecuteCommand('netstat -atpn')
        one,two = ssDataProcessing(ss_command)
        net = netstatDataProcessing(netstat_command)
        insertData(conn=conn,table='one',data=one)
        insertData(conn=conn,table='two',data=two)
        insertData(conn=conn,table="net",data=net)
        if pid_state:
            layout = Layout()
            pid_fast = "command:\n\n q(退出) \n\n e(返回主页) \n\n t2(刷新频率改2秒) \n\n u(上传排序) \n\n d(下载排序) \n\n l10(显示10条数据,默认:10)"
            layout.split_column(
                Layout(size=1),
                Layout(Panel(content),name="top",ratio=5),
                Layout(name="bottom",ratio=20)
            )
            layout['bottom'].split_row(
                Layout(Panel(pid_fast),name="left",ratio=5),
                Layout(Panel(selectDetails(conn=conn,pid=pid_number)),name="right",ratio=20)
            )
            printr(layout,end="")
        else:
            layout = Layout()
            fast = "command:\n\n q(退出) \n\n p2346(查pid是2346的流量详情) \n\n t2(刷新频率改2秒) \n\n u(上传排序) \n\n d(下载排序) \n\n c(连接数排序) \n\n i(ip数量排序)"
            layout.split_column(
                Layout(Padding(""),size=1),
                Layout(Panel(content),name="top",ratio=3),
                Layout(name="bottom",ratio=20),
            )
            layout['bottom'].split_row(
                Layout(Panel(fast),name="Rightmost",ratio=8),
                Layout(Panel(selectTotalListen(conn=conn)),name="left",ratio=15),
                Layout(Panel(selectTotalOut(conn=conn)),name="right",ratio=15)
            )  
            layout['Rightmost'].split_column(
                Layout(Panel(fast),name="Rightmost",ratio=8),
                Layout(Panel(networkCardTraffic(cat_command,cat_command_sleep_1)),name="total_flow",ratio=8)
            )
            # 清屏命令针对不同操作系统
            if os.name == 'posix':  # 对于Linux、Mac等类Unix系统
                os.system('clear')
            elif os.name == 'nt':  # 对于Windows系统
                os.system('cls')
            printr(layout,end="")
        await asyncio.sleep(sleep_time)
    # ssh.close()

async def user_input(stop_event):
    global program_quit,sleep_time,pid_number,pid_state,order_by,pid_order_by,limit
    while not stop_event.is_set():
        user_input = await asyncio.get_event_loop().run_in_executor(None, getpass.getpass,"")
        #退出程序
        if user_input == "q":
            program_quit = True
            os._exit(0)
        #刷新时间
        if 't' in user_input:
            time_data = user_input[1:]
            if time_data.isdigit():
                sleep_time = int(user_input[1:]) - 1
            else:
                print('你输入的时间指令有误！')
        #输入pid号
        if 'p' in user_input:
            data = user_input[1:]
            if data.isdigit():
                print('pid:' + data)
                pid_number = data
                pid_state = True
        #返回首页
        if user_input == 'e':
            pid_state = False
        #上传流量排序
        if user_input == 'u':
            order_by = """
                        ORDER BY 
                                upload DESC;
                        """
            pid_order_by = """
                        ORDER BY 
                                upload DESC
                        """
        #下载流量排序
        if user_input == 'd':
            order_by = """
                        ORDER BY 
                                download DESC;
                        """
            pid_order_by = """
                        ORDER BY 
                                download DESC
                        """
        #连接数排序
        if user_input == "c":
            order_by = """
                        ORDER BY 
                                connect_ip DESC;
                        """
        #ip数排序
        if user_input == "i":
            order_by = """
                        ORDER BY 
                                ip_num DESC;
                        """
        #条数限制
        if "l" in user_input:
            limit_num = user_input[1:]
            if limit_num.isdigit():
                print('修改打印条数为:' + limit_num)
                limit = """
                            LIMIT 
                        """ + str(limit_num)
        print(f"你输入的指令是: {user_input}")



async def main():
    if sys.version_info < (3, 7):
        task1 = asyncio.ensure_future(run(stop_event))
        task2 = asyncio.ensure_future(user_input(stop_event))
    else:
        task1 = asyncio.create_task(run(stop_event))
        task2 = asyncio.create_task(user_input(stop_event))
    # 等待所有任务完成（但这里user_input由于是无限循环，所以不会结束）
    await asyncio.gather(task1, task2)

if __name__ == "__main__":
    console = Console()
    #默认order_by
    order_by = """
    ORDER BY 
            upload DESC,
            download DESC;
    """
    #默认order_by
    pid_order_by = """
    ORDER BY 
            upload DESC,
            download DESC
    """
    #默认限制条数
    limit = """
        LIMIT 10
    """
    pid_number = None
    pid_state = False
    sleep_time = 1
    program_quit = False
    stop_event = asyncio.Event()
    if sys.version_info.major == 3 and sys.version_info.minor >= 7:
        asyncio.run(main())
    elif sys.version_info.major == 3 and sys.version_info.minor < 7:
        loop = asyncio.get_event_loop()
        try:
            main_task = loop.create_task(main())
            loop.run_forever()
        except KeyboardInterrupt:  # 按Ctrl+C时退出程序
            print('已退出TMD-TOP！')
            stop_event.set()  # 如果有必要触发stop_event以结束任务
        finally:
             # 关闭所有挂起的任务并关闭事件循环
            main_task.cancel()  # 首先取消主任务
            for task in asyncio.Task.all_tasks():
                task.cancel()
            loop.run_until_complete(asyncio.gather(*asyncio.Task.all_tasks(),return_exceptions=True))
            loop.close()
    print('已退出TMD-TOP！')