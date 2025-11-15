## Cli配置

### 样例1

在 ~/.codex/config.toml 文件开头添加以下配置：

```toml
model_provider = "crs"
model = "gpt-5-codex"
model_reasoning_effort = "high"
disable_response_storage = true
preferred_auth_method = "apikey"
[model_providers.crs]
name = "crs"
base_url = "https://codex.zenscaleai.com/openai"
wire_api = "responses"
requires_openai_auth = true
env_key = "CRS_OAI_KEY"
```

在 ~/.codex/auth.json 文件中配置API密钥：

```json
{
"OPENAI_API_KEY": null
}
```

将 OPENAI_API_KEY 设置为 null，然后设置环境变量 CRS_OAI_KEY 为您的 API 密钥（格式如 cr_xxxxxxxxxx）。

环境变量设置方法
Windows:

```bash
set CRS_OAI_KEY=cr_xxxxxxxxxx
```

### 样例2

```toml
model_provider = "duckcoding"
model = "gpt-5-codex"		
model_reasoning_effort = "high"
network_access = "enabled"
disable_response_storage = true

[model_providers.duckcoding]
name = "duckcoding"
base_url = "https://jp.duckcoding.com/v1"
wire_api = "responses"
requires_openai_auth = true
```

```json
{
  "OPENAI_API_KEY": "粘贴为CodeX专用分组令牌key"
}
```

