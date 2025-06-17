# SocketIO、frp、uniapp相互间连接使用记录

## 前言

近期公司又搞了个新东西，用python搞了个智能体，连接本地大模型，开放socketio接口对接前端，还有mcp一堆的。

现在在此基础上要开发web前端、uniapp开发app，公司内网管理乱、python的只会脚本和大模型、连项目上到云服务器上都懒得干，开发测试阶段又要远程、域名那些。虽然不是博主负责开发，但下面的人技术有限，基本啥事都要看着来，因此折腾的过程中的到以下的使用记录；

## 主要内容

- frp内网穿透本地socketio服务到云服务器、NginxProxyManager代理到域名；
- uniapp使用socketio服务

本文仅记录一些使用注意事项和坑，具体使用不会展开；

**注意使用的socketio版本**；

## frp和NginxProxyManager内网穿透

版本：

- frp：0.44.0
- NginxProxyManager：latest，版本一般不影响
- 服务端socketio：python-socketio>=5.13.0、flask-socketio>=5.5.1
- python-engineio：4.12.2

因为socketio连接比较杂，既有不通用WebSocket，又有长轮询，导致基于HTTP 映射穿透比较复杂，后面直接改为tcp映射就行了

### frpc.ini配置

```ini
# ##########################
# Socket.IO 服务（TCP 模式）
# ##########################
[web-socketio-tcp]
type                = tcp
local_ip            = 127.0.0.1
# 本地 Python Socket.IO 服务端口
local_port          = 8080
# 云端开放给客户端访问的端口
remote_port         = 6001
```

8080是本地socketio服务端口、6001是云服务器frps预留端口，域名代理到6001即可

注意docker运行frps的话要映射好6001端口出来；

配置文件中注释和内容不要在同一行，frp可能把后面注释当内容，启动服务后先看web界面是否配置成功

### NginxProxyManager

新建代理、输入好基本信息后;

在Edit->Custom locations->Add location；"/api"是socketio握手路径，172.17.0.1是用了docker运行的容器ip，填自己信息即可；下面超时设置最好填，不过暂时没发现不填的问题；

![image-20250618011405325](https://www.img.liy1900.xyz/www/ty/image-20250618011405325.png)

后面再申请SSL证书即可；

### 其他问题

启动socketio服务，启动内网穿透，socketio控制台有可能报：

```powershell
The client is using an unsupported version of the Socket.IO or Engine.IO protocols (further occurrences of this error will be logged with level INFO)
127.0.0.1 - - [17/Jun/2025 02:08:04] "GET /api/?EIO=3&transport=polling&t=PTvxGM1 HTTP/1.1" 400 -
```

报错提示客户端与服务端的EIO（Engine.IO）版本不兼容，报错请求中 `EIO=3`代表客户端用`Engine.IO v3`版本，而python-socketio是5版本，默认使用`Engine.IO v4`;

如果是前端还没连接就有这个错误，并且一直不停报，那大概是因为 Nginx 启动了“健康检查”或“连接探测”，代理后他不断发送请求。

- 一般这个不影响业务可不管，或者直接在NginxProxyManager的location的额外配置中加以下配置来忽略他

```
if ($arg_EIO != "4") {
    return 400;
}
```

- 降低服务端socketio版本，降到默认使用EIO=3，但这样到时客户端也要用EIO=3来连接

```powershell
pip uninstall python-socketio flask-socketio python-engineio -y
pip install flask-socketio==4.3.2 python-socketio==4.6.1 python-engineio==3.13.2
```

- 兼容EIO=3和EIO=4，据说能这样配置能兼容，但博主试了不行

```python
self.socketio = SocketIO(
    app,
    path="/api",
    cors_allowed_origins="*",
    async_mode='threading',  # 或 eventlet/gevent，根据实际情况
    engineio_logger=True,
    engineio_options={
        'allow_upgrades': True,
        'max_http_buffer_size': 100000000,
        'ping_timeout': 60,
        'ping_interval': 25,
        'async_handlers': True,
        'cors_allowed_origins': '*',
        'protocols': ['3', '4']  # <== 兼容 EIO v3 和 v4
    }
)
```

- 博主没改配置和版本，后面莫名其妙报错消失了，下面是服务端代码

```python
from flask import Flask
from flask_socketio import SocketIO
def build(self):
	app = self.flask_app = Flask(__name__, static_folder=None)
	self.socketio = SocketIO(app, path="/api", cors_allowed_origins="*")
```

## uniapp使用socketio

一开始和web前端项目一样用了`socket.io-client`组件，然后观察网络请求发现他一直用EIO=3去连接，但服务端是EIO=4，报一堆`CORS`、`xhr poll error`。实际是EIO版本问题；

看了一堆网上资料，得出这结果：

- Uniapp 平台编译的 JS 版本与 Socket.io 存在兼容性，新版本的 Socket.io 会出现错误，老版本有可能可以工作，但存在很多不确定性。毕竟 Socket.io 是先出来的，后面有了 Uniapp 这个平台，但是缺少官方的适配工作，所以二者兼容性差。

- 原socket.io-client无法使用是XMLHttpRequst、WebSocket无法识别，可能是打包后把引用包搞丢了

### 换改进版

更换了为`@hyoga/uni-socket.io`组件，这个是别的大佬重写过的，使用方法一样；

```powershell
pnpm i @hyoga/uni-socket.io
```

```javascript
import io from '@hyoga/uni-socket.io';
this.socket = io('https://xx.com', {
	path: '/api',
});
```

## 其他问题

### ws链接

有时发现socketio请求链接是ws链接请求，这种也是报错了，原因可能是：

Flask 自带开发服务器并不支持 WebSocket（即使用的是降级版），必须用支持 WebSocket 的 WSGI server

```
pip install eventlet==0.33.3
```

```python
import eventlet
eventlet.monkey_patch()  # 一定要添加

# self.flask_app.run(debug=True, port=8080)  # ❌ 不支持 socketio
self.socketio.run(app, host="0.0.0.0", port=8080)

```

而客户端是可以通过配置控制链接参数的，但不太会用，感觉有时会失效

```js
    const socket = io('https://socketio.yuxindazhineng.com', {
        path: '/api',
        transports: ['websocket'],
        secure: true
    })
```

```javascript
// vue.config.js
module.exports = {
  devServer: {
    proxy: {
      '/': {
        target: 'https://socketio.yuxindazhineng.com',
        ws: false, // 禁用 WebSocket 代理
        changeOrigin: true
      }
    }
  }
}
```

### 版本适配

![image-20250618020617478](https://www.img.liy1900.xyz/www/ty/image-20250618020617478.png)

## 参考文章

[简介 — Flask-SocketIO 文档](https://flask-socketio.readthedocs.io/en/latest/intro.html#version-compatibility)