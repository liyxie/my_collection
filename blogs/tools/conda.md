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
