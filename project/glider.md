[glider](https://github.com/nadoo/glider)

3个场景中可以用到这个转发神器

## vmss/ss转换

买了类似vmss/ss等等很“先进时髦”的协议，如何把他用到我程序只支撑http/socks协议上呢

通过这个工具可进行转换，docker或者二进制运行，非常简单进行转发+转换。 这样买个ji场等于有了全球代理

## 海外代理转发

好多海外代理只支持海外使用。买个HK，9.9服务器进行转发即可

优势在于，比起其他类似v2ray等，这个资源消耗非常非常小，最低配的0.5c/512M内存也很轻松

举例：

```
wget https://github.com/nadoo/glider/releases/download/v0.16.4/glider_0.16.4_freebsd_amd64.tar.gz

glider -listen :20170 -forward socks5://xxx:xx@jxx:30513  -verbose
```

## 动态隧道代理

3.实现类似动态隧道代理,一个入口，n个出口，支持几种负载均衡

## 其他

搭配tailscale，chrome使用omega proxy 就可以直接用tailscale 地址 加端口

