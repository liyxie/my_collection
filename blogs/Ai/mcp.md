## mcp接入一些问题

### error -32000: Connection closed

可能npx路径存在中文，无法自动获取；

```bash
# 打开cmd
echo %APPDATA%

# 或者PowerShell
echo $env:APPDATA
```

在配置加上路径

```json
{
  "mcpServers": {
    "context7": {
      "command": "npx",
      "args": [
        "@upstash/context7-mcp@latest"
      ],
      "env": {
        "APPDATA": "C:\\Users\\xxx\\AppData\\Roaming"    // <--- 关键在于这行
      },
      "disabled": false,
    }
  }
}
```

## vscode开启调试

- 通过 “Help（帮助）” > “Toggle Developer Tools（开发者工具）” 打开。 “Console” 标签页中，可能会有与 MCP 服务启动相关的错误信息