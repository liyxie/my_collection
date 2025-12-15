连接WSL

1. 下载插件 Open Remote - WSL
2. `Ctil+Shift+P`，命令 ` Configure Runtime Arguments`，编辑文件`argv.json`，添加

```json
    "enable-proposed-api": [
        "jeanp413.open-remote-wsl",
    ]
```

