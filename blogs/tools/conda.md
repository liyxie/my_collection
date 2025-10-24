# conda使用记录

## powershell中无法使用conda，无报错信息

用conda activate pytorch激活pytorch环境，然后用conda info --envs显示当前环境，发现仍然为base，未激活成功；且输入提示的"PS"前不显示(base)。

### 原因

conda在PowerShell中未正确配置，导致conda activate不能用。

### 解决

1. 初始化conda
2. 修改PowerShell限制策略
3. 重启PowerShell

```
PS C:\WINDOWS\system32> conda init powershell
no change     D:\Anacanda\Scripts\conda.exe
no change     D:\Anacanda\Scripts\conda-env.exe
no change     D:\Anacanda\Scripts\conda-script.py
no change     D:\Anacanda\Scripts\conda-env-script.py
no change     D:\Anacanda\condabin\conda.bat
no change     D:\Anacanda\Library\bin\conda.bat
no change     D:\Anacanda\condabin\_conda_activate.bat
no change     D:\Anacanda\condabin\rename_tmp.bat
no change     D:\Anacanda\condabin\conda_auto_activate.bat
no change     D:\Anacanda\condabin\conda_hook.bat
no change     D:\Anacanda\Scripts\activate.bat
no change     D:\Anacanda\condabin\activate.bat
no change     D:\Anacanda\condabin\deactivate.bat
no change     D:\Anacanda\Scripts\activate
no change     D:\Anacanda\Scripts\deactivate
no change     D:\Anacanda\etc\profile.d\conda.sh
no change     D:\Anacanda\etc\fish\conf.d\conda.fish
no change     D:\Anacanda\shell\condabin\Conda.psm1
no change     D:\Anacanda\shell\condabin\conda-hook.ps1
no change     D:\Anacanda\Lib\site-packages\xontrib\conda.xsh
no change     D:\Anacanda\etc\profile.d\conda.csh
modified      C:\Users\��\Documents\WindowsPowerShell\profile.ps1

==> For changes to take effect, close and re-open your current shell. <==

PS C:\WINDOWS\system32> Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope LocalMachine

执行策略更改
执行策略可帮助你防止执行不信任的脚本。更改执行策略可能会产生安全风险，如 https:/go.microsoft.com/fwlink/?LinkID=135170
中的 about_Execution_Policies 帮助主题所述。是否要更改执行策略?
[Y] 是(Y)  [A] 全是(A)  [N] 否(N)  [L] 全否(L)  [S] 暂停(S)  [?] 帮助 (默认值为“N”): Y
PS C:\WINDOWS\system32>
```

### 注意

`conda init powershell` 后日志的目录有中文，显示乱码，会失败，需要改掉中文

### 参考

[安装Anaconda（miniconda）后如何在powershell使用conda activate命令（Windows）-CSDN博客](https://blog.csdn.net/m0_57170739/article/details/134833229)

[[Windows\]解决：无法使用conda activate；IMPORTANT: You may need to close and restart...‘conda init‘无用_important: you may need to close and restart your -CSDN博客](https://blog.csdn.net/qq_42839752/article/details/132085531?spm=1001.2014.3001.5502)



## Linux安装conda

```bash
# 安装 Miniconda
wget https://repo.anaconda.com/miniconda/Miniconda3-latest-Linux-x86_64.sh
bash Miniconda3-latest-Linux-x86_64.sh

# 创建 Python 3.10 环境
conda create -n temp_env python=3.10
# 切换环境
conda activate sd-env

```

## Conda命令

#### **环境管理**

```bash
# 创建新环境（指定Python版本）
conda create --name myenv python=3.9
# 创建包含特定包的环境
conda create --name myenv numpy pandas matplotlib
# 激活环境（Windows/Linux/macOS命令不同）
conda activate myenv        # Windows/Linux/macOS (conda 4.6+)
source activate myenv       # Linux/macOS (旧版本)
# 退出当前环境
conda deactivate
# 列出所有环境
conda env list
# 删除环境
conda env remove --name myenv
# 导出环境配置到YAML文件
conda env export > environment.yml
# 从YAML文件创建环境
conda env create -f environment.yml
# 更新环境配置
conda env update --name myenv --file environment.yml
```

#### **包管理**

```bash
# 安装包（当前环境）
conda install numpy
# 安装指定版本的包
conda install numpy=1.21
# 安装多个包
conda install scipy pandas scikit-learn
# 从特定channel安装包
conda install -c conda-forge tensorflow
# 更新包
conda update numpy
# 更新所有包
conda update --all
# 移除包
conda remove numpy
# 列出已安装的包
conda list
# 搜索包
conda search numpy
# 安装pip包（在conda环境中）
conda install pip
pip install some-package
```

#### **信息查询**

```bash
# 检查conda版本
conda --version
# 获取conda信息
conda info
# 检查环境信息
conda info --envs
# 查看某个包的详细信息
conda search numpy --info
```

#### **配置管理**

```bash
# 添加conda channel
conda config --add channels conda-forge
# 设置channel优先级
conda config --set channel_priority strict
# 显示conda配置
conda config --show
# 显示channel列表
conda config --show channels
# 移除channel
conda config --remove channels conda-forge
```

#### **清理和维护**

```python
# 清理缓存包
conda clean --packages
# 清理所有缓存
conda clean --all
# 检查conda是否有更新
conda update conda
# 验证包完整性
conda verify package_name
```

#### **实用技巧**

```python
# 在指定环境中运行命令
conda run -n myenv python script.py
# 创建环境的精确副本
conda create --name new_env --clone old_env
# 导出显式规格文件（便于共享）
conda list --explicit > spec-file.txt
# 根据显式规格文件创建环境
conda create --name myenv --file spec-file.txt
```

