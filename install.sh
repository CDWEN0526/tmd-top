#!/bin/bash


# 判断并创建 /tmp 目录（通常这个步骤是不必要的，因为/tmp在大多数Linux系统中默认存在）
if [ ! -d "/tmp" ]; then
    mkdir -p /tmp
fi

# 检查并安装基本软件包
if command -v apt-get > /dev/null; then
    echo "检测到基于Debian的系统，将使用apt进行操作。"
    
    # 安装Python3、pip3和net-tools等基础软件包
    sudo apt-get install -y python3 python3-pip net-tools zlib1g-dev libtiff5-dev libffi-dev sqlite sqlite-devel sysstat
    
elif command -v yum > /dev/null || command -v dnf > /dev/null; then
    if command -v yum; then
        echo "检测到基于Red Hat的系统，将使用yum进行操作。"
        
        # 安装对应的RHEL/CentOS系统下的基础软件包
        sudo yum install -y python3 python3-pip net-tools zlib-devel libtiff-devel libffi-devel sqlite sqlite-devel sysstat
        
    elif command -v dnf; then
        echo "检测到基于Red Hat的系统，将使用dnf进行操作。"
        
        # 安装Fedora或RHEL 8+系统的基础软件包
        sudo dnf install -y python3 python3-pip net-tools zlib-devel libtiff-devel libffi-devel sqlite sqlite-devel sysstat
        
    fi
    
else
    echo "无法识别当前系统的包管理器（支持apt或yum/dnf）。"
fi

#判断是否python3.8或更高
PY_VERSION=$(python3 -c 'import sys; print(sys.version_info.major, sys.version_info.minor)')
# 将版本号转换为整数以便比较（这里假设输出格式始终为 "major minor"）
IFS=' ' read -r MAJOR MINOR <<< "$PY_VERSION"
if ((MAJOR > 3 || (MAJOR == 3 && MINOR >= 8))); then
    echo "检查到当前python >= 3.8 准备安装"
else
    echo "检查到当前python < 3.8 无法安装，请安装使用另一种安装方式！"
	exit 1
fi


# 升级pip至最新版本
python3 -m pip install --upgrade pip

# 检查并安装requirements.txt中的依赖
if [ -f "requirements.txt" ]; then
    echo "检测到当前目录下存在 requirements.txt 文件。"

    if ! python3 -m pip install -r requirements.txt; then
        echo "安装 requirements.txt 中的依赖时发生错误！请检查输出以了解具体问题。"
        exit 1
    fi
    
    echo "requirements.txt 中的依赖已成功安装。"

else
    echo "当前目录下未找到 requirements.txt 文件。"
fi

# 检查并处理 tmd-top.py 文件
if [ -f "tmd-top.py" ]; then
    echo "检测到当前目录下存在 tmd-top.py 文件。"

    # 复制文件到 /usr/sbin/tmd-top，并重命名（如果目标文件已存在，可能会覆盖）
    sudo cp -f tmd-top.py /usr/bin/tmd-top
    
    # 赋予执行权限
    sudo chmod 777 /usr/bin/tmd-top
    
    echo "tmd-top.py 已成功复制至 /usr/bin/tmd-top，并赋予了执行权限。"
    
else
    echo "当前目录下未找到 tmd-top.py 文件。"
fi

echo "脚本执行完毕，您可以在终端上执行：tmp-top命令来验证安装是否成功。"

# 如果需要确保终端显示中文，请确保您的系统和终端支持UTF-8编码。