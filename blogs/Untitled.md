

nginxProxyManager

直接修改conf配置文件只能暂时生效，当使用web页面停止代码，再开启代理时，NginxProxyManager会先删除该配置文件，再重新生成一份配置文件，直接修改的内容将会丢失；

要修改只能在web页面配置