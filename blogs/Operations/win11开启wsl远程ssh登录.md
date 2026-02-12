

## 开放防火墙

修改端口后，需要在宿主机的防火墙中开放对应的端口，在宿主机的 powershell 中以管理员权限执行如下命令：

New-NetFirewallRule -DisplayName '"Allow SSH on Port xxxxx"' -Direction Inbound -Protocol TCP -LocalPort xxxxx -Action Allow

## 修改 wsl2 网络模式

wsl2 的默认网络模式是 NAT，在此模式下：

windows 可以使用 localhost 访问 wsl2 网络应用
wsl2 需要通过获取主机 ip 访问 windows 应用
局域网设备需要通过主机端口转发访问 wsl2 应用
在运行 Windows 11 22H2 及更高版本的宿主机上，wsl2 支持镜像网络模式，在此模式下，windows 主机可以使用 localhost 访问 wsl2 网络应用，局域网设备可以直接使用宿主机 ip 访问 wsl2 网络应用。

wsl2 配置文件路径为 %UserProfile%/.wslconfig，修改为以下内容：

[experimental]
networkingMode=mirrored
dnsTunneling=true
firewall=true
autoProxy=true
上述配置中还启用了自动代理、防火墙和 dns 隧道。修改完成后，重启 wsl 即可应用该配置：

wsl --shutdown
wsl

## 显卡驱动查不到

which nvidia-smi

在标准的现代 WSL2 环境中，通常会输出： `/usr/lib/wsl/lib/nvidia-smi`

建立软链接 

sudo ln -s /usr/lib/wsl/lib/nvidia-smi /usr/bin/nvidia-smi