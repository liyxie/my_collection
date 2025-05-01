# win10双开（多开）微信

新建txt文件，内容如下，修改内容保存后文件改名为.bat文件，点击启动即可多开

```bash
TASKKILL/E/IM wechat.exe
start C:\"Program Files (x86)"\Tencent\WeChat\WeChat.exe
start C:\"Program Files (x86)"\Tencent\WeChat\WeChat.exe
```

- `C:\"Program Files (x86)"\Tencent\WeChat\WeChat.exe` 是微信安装路径，自己修改，要开多少个微信就写多少个start 行；
- 启动后多个微信框会叠在一起，拉开就看到是多开；

