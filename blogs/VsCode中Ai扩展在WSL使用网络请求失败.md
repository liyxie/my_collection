## VsCode中Ai扩展在WSL使用网络请求失败

将 WSL networkMode 更改为镜像模式

### 步骤：

1. **创建或编辑 .wslconfig 文件**

   在 Windows 用户目录下创建或编辑 `.wslconfig` 文件：

   ```bash
   C:\Users\<你的用户名>\.wslconfig
   ```

2. **添加以下配置**

   在文件中添加或修改以下内容：

   ```ini
   [wsl2]
   networkingMode=mirrored
   ```

3. **完整的推荐配置示例**

   ```ini
   [wsl2]
   networkingMode=mirrored
   dnsTunneling=true
   firewall=true
   autoProxy=true
   ```

4. **关闭所有 WSL 实例**

   在 PowerShell 或命令提示符中执行：

   ```bash
   wsl --shutdown
   ```

5. **重新启动 WSL**

   ```bash
   wsl
   ```