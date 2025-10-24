

python接收请求转发到 `FastApi` 接口

主要涉及多文件上传

目前暂未解决SSE接口

```python
async def __call__(self, path: str, request: Request):
        print("public请求", path, request)
        baseClient = self.gui().app().client
        from yxd.config import api_base

        try:
            url = f"{api_base}/public/{path}"
            content_type = request.headers.get("content-type", "").lower()

            # 处理文件上传（multipart/form-data）
            if "multipart/form-data" in content_type:
                form_data = await request.form()
                file = form_data.get("file")
                files = form_data.getlist("files")
                if files or file:
                    data = {k: v for k, v in form_data.items() if not hasattr(v, 'filename')}
                    if file:
                        file_content = await file.read()
                        files = {"file": (file.filename, file_content, file.content_type or 'application/octet-stream')}
                    if files:
                        new_files = []
                        for file in files:
                            file_content = await file.read()
                            new_files.append(("files", (file.filename, file_content, file.content_type or 'application/octet-stream')))
                    # 自定义添加其他参数
                    data["access_token"] = baseClient.access_token
                    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-type', 'content-length']}
                    # 发送带文件的POST请求
                    resp = requests.post(
                        url,
                        data=data,
                        files=new_files,
                        headers=headers,
                        timeout=300
                    )
                else:
                    data = {k: v for k, v in form_data.items()}
                    # 自定义添加其他参数
                    data["access_token"] = baseClient.access_token
                    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-type', 'content-length']}
                    resp = requests.post(
                        url,
                        data=data,
                        headers=headers,
                        timeout=300
                    )
            else:
                # 处理JSON/GET请求
                headers = {
                    k: v for k, v in request.headers.items()
                    if k.lower() not in ['host']
                }
                if request.method == "GET":
                    # 透传GET查询参数
                    resp = requests.get(
                        url,
                        params=dict(request.query_params),
                        headers=headers,
                        timeout=60
                    )
                else:
                    # 透传JSON数据
                    json_data = await request.json() if await request.body() else {}
                    resp = requests.post(
                        url,
                        json=json_data,
                        headers=headers,
                        timeout=60
                    )
            # 处理文件下载响应
            if 'attachment' in resp.headers.get('content-disposition', '').lower():
                def generate():
                    for chunk in resp.iter_content(chunk_size=8192):
                        if chunk:
                            yield chunk
                return StreamingResponse(
                    generate(),
                    status_code=resp.status_code,
                    headers={
                        k: v for k, v in resp.headers.items()
                        if k.lower() in ['content-type', 'content-disposition', 'content-length']
                    }
                )
            else:
                content_type = resp.headers.get("content-type", "").lower()
                if "application/json" in content_type:
                    try:
                        data = resp.json()
                    except:
                        data = {"raw": resp.text}
                else:
                    data = {"raw": resp.text}
                # 普通响应
                return responses.JSONResponse(
                    content=data,
                    status_code=resp.status_code,
                    headers={k: v for k, v in headers.items() if k not in ['content-encoding', 'transfer-encoding']}
                )
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"代理请求失败: {str(e)}"}
            )
```

