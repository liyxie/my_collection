# GeminiCli使用记录



## 国内登录

### 1 

```
用过谷歌云或者aistudio的，使用geminicli登陆时可能会有些麻烦，可能要打开console.cloud.google.com,找到你的projectid，然后设置GOOGLECLOUD PROJECT环境变量（项目目录新建一个.env文件，里面加一行 GOOGLE_CLOUD_PROJECT=“YOUR_PROJECT_ID” 然后开tun模式），使用这种方式打开gemini cli，就可以用了
```



### 2

```
使用下面的方式解决了，直接关闭遥测
方式 1 打开配置 ~/.gemini/settings.json ，再最后面添加下面的这个参数 “usageStatisticsEnabled”: false

方式 2 直接使用 gemini --telemetry false 启动
```

### 3

```
闪退需要单独配置。

直接使用gemini --telemetry false启动
配置~/.gemini/settings.json，添加参数usageStatisticsEnabled的值为false
```



### 4

现在必须登录才能使用嘛。我配置了环境变量想用自己的api怎么输入gemini启动每次都直接跳转登录了呢。
/auth
看下自己的setting文件，可能写错了，把登录模块的删了



### 5

https://aistudio.google.com/app/api-keys?project=gen-lang-client-0505638864

设置Gemini key

## 使用

### 界面解读

```
Yes, allow once
Yes, allow always
No (esc)
Modify with external editor
```

```
是的，允许一次
是的，总是允许
没有(esc)
使用外部编辑器进行修改
```

#### 回车换行

ctrl + enter





