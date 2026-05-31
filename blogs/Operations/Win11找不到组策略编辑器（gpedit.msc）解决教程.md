

1.在[Win11](https://zhida.zhihu.com/search?content_id=240770838&content_type=Article&match_order=1&q=Win11&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODAyMTkwNDgsInEiOiJXaW4xMSIsInpoaWRhX3NvdXJjZSI6ImVudGl0eSIsImNvbnRlbnRfaWQiOjI0MDc3MDgzOCwiY29udGVudF90eXBlIjoiQXJ0aWNsZSIsIm1hdGNoX29yZGVyIjoxLCJ6ZF90b2tlbiI6bnVsbH0.nkj8olqTYlpJeB9ZkP8UZq0us5xz1SXatQyNXVQ08ps&zhida_source=entity)中，同时按下Win+R，输入【[gpedit.msc](https://zhida.zhihu.com/search?content_id=240770838&content_type=Article&match_order=1&q=gpedit.msc&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODAyMTkwNDgsInEiOiJncGVkaXQubXNjIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjQwNzcwODM4LCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.SHYksqsUnn_rDbnVjFKUVCxjvKT6AnE3Nt9Tq_gmTdE&zhida_source=entity)】

2.显示找不到‘gpedit.msc’文件

3.按下Win+R，输入【notepad】，打开[记事本]

4.在记事本中输入以下内容：

\```batch

@echo off

pushd "%~dp0"

dir /b %systemroot%\Windows\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientExtensions-Package~3*.mum >gp.txt

dir /b %systemroot%\servicing\Packages\Microsoft-Windows-GroupPolicy-ClientTools-Package~3*.mum >>gp.txt

for /f %%i in ('findstr /i . gp.txt 2^>nul') do [dism](https://zhida.zhihu.com/search?content_id=240770838&content_type=Article&match_order=1&q=dism&zd_token=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJpc3MiOiJ6aGlkYV9zZXJ2ZXIiLCJleHAiOjE3ODAyMTkwNDgsInEiOiJkaXNtIiwiemhpZGFfc291cmNlIjoiZW50aXR5IiwiY29udGVudF9pZCI6MjQwNzcwODM4LCJjb250ZW50X3R5cGUiOiJBcnRpY2xlIiwibWF0Y2hfb3JkZXIiOjEsInpkX3Rva2VuIjpudWxsfQ.MlGsD_zhfEOBi7S6k9hvXVfCVp5_fzfpLYmLBo8SllE&zhida_source=entity) /online /norestart /add-package:"%systemroot%\servicing\Packages\%%i"

pause

5.保存记事本，文件名设为【gpedit.bat`】，保存类型选择【所有文件】

6.右键【gpedit.bat】文件，选择【以管理员身份运行】

7.出现如下画面即可成功

```
C:\Windows\System32>```batch
'```batch' 不是内部或外部命令，也不是可运行的程序
或批处理文件。
系统找不到指定的路径。

部署映像服务和管理工具
版本: 10.0.26100.5074

映像版本: 10.0.26200.8457

正在处理 1 (共 1) - 正在添加程序包 Microsoft-Windows-GroupPolicy-ClientTools-Package~31bf3856ad364e35~amd64~zh-CN~10.0.26100.1591
[==========================100.0%==========================]
操作成功完成。

部署映像服务和管理工具
版本: 10.0.26100.5074

映像版本: 10.0.26200.8457

正在处理 1 (共 1) - 正在添加程序包 Microsoft-Windows-GroupPolicy-ClientTools-Package~31bf3856ad364e35~amd64~zh-CN~10.0.26100.8117
[==========================100.0%==========================]
操作成功完成。

部署映像服务和管理工具
版本: 10.0.26100.5074

映像版本: 10.0.26200.8457

正在处理 1 (共 1) - 正在添加程序包 Microsoft-Windows-GroupPolicy-ClientTools-Package~31bf3856ad364e35~amd64~zh-CN~10.0.26100.8457
[==========================100.0%==========================]
操作成功完成。

部署映像服务和管理工具
版本: 10.0.26100.5074

映像版本: 10.0.26200.8457

正在处理 1 (共 1) - 正在添加程序包 Microsoft-Windows-GroupPolicy-ClientTools-Package~31bf3856ad364e35~amd64~~10.0.26100.1591
[==========================100.0%==========================]
操作成功完成。

部署映像服务和管理工具
版本: 10.0.26100.5074

映像版本: 10.0.26200.8457

正在处理 1 (共 1) - 正在添加程序包 Microsoft-Windows-GroupPolicy-ClientTools-Package~31bf3856ad364e35~amd64~~10.0.26100.8246
[==========================100.0%==========================]
操作成功完成。

部署映像服务和管理工具
版本: 10.0.26100.5074

映像版本: 10.0.26200.8457

正在处理 1 (共 1) - 正在添加程序包 Microsoft-Windows-GroupPolicy-ClientTools-Package~31bf3856ad364e35~amd64~~10.0.26100.8457
[==========================100.0%==========================]
操作成功完成。
请按任意键继续. . .
```

