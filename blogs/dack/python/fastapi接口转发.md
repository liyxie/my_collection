

python接收请求转发到 `FastApi` 接口

- 文件上传为 from表单上传
- 其他为请求体
- 均为post请求

```python
async def __call__(self, path: str, request: Request):
        baseClient = self.gui().app().client
        from yxd.config import api_base

        try:
            # 转发目标url
            url = f"{api_base}/cloud_api/{path}"
            content_type = request.headers.get("content-type", "").lower()
            # 处理文件上传（multipart/form-data）
            if "multipart/form-data" in content_type:
                print("文件上传")
                form_data = await request.form()
                file = form_data.get("file")
                files = form_data.getlist("files")
                # print("file:", file)
                # print("files1:", files)
                if files or file:
                    data = {k: v for k, v in form_data.items() if not hasattr(v, 'filename')}
                    files_new = []
                    if file:
                        print("单文件")
                        file_content = await file.read()
                        files_new = {"file": (file.filename, file_content, file.content_type or 'application/octet-stream')}
                    if files:
                        print("多文件")
                        for file in files:
                            file_content = await file.read()
                            files_new.append(("files", (file.filename, file_content, file.content_type or 'application/octet-stream')))
                    # 加入额外参数
                    data["access_token"] = baseClient.access_token
                    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-type', 'content-length']}
                    resp = requests.post(
                        url,
                        data=data,
                        files=files_new,
                        stream=True,
                        headers=headers,
                        timeout=300
                    )
                else:
                    print("表单请求")
                    data = {k: v for k, v in form_data.items()}
                    # 加入额外参数
                    data["access_token"] = baseClient.access_token
                    headers = {k: v for k, v in request.headers.items() if k.lower() not in ['host', 'content-type', 'content-length']}
                    resp = requests.post(
                        url,
                        data=data,
                        headers=headers,
                        timeout=300
                    )
            else:
                print("json请求")
                headers = {
                    k: v for k, v in request.headers.items()
                    if k.lower() not in ['host']
                }
                if request.method == "GET":
                    # GET查询参数
                    resp = requests.get(
                        url,
                        params=dict(request.query_params),
                        headers=headers,
                        timeout=60
                    )
                else:
                    # JSON数据
                    json_data = await request.json() if await request.body() else {}
                    json_data["access_token"] = baseClient.access_token
                    resp = requests.post(
                        url,
                        json=json_data,
                        headers=headers,
                        timeout=60
                    )
            if resp.headers.get("content-type", "").lower().startswith("text/event-stream"):
                print("SSE 响应")
                def event_stream():
                    for chunk in resp.iter_content(chunk_size=None):
                        if chunk:
                            yield chunk
                return StreamingResponse(
                    event_stream(),
                    media_type="text/event-stream",
                    headers={k: v for k, v in resp.headers.items() if k.lower() in ["content-type"]}
                )
            if 'attachment' in resp.headers.get('content-disposition', '').lower():
                print("文件下载响应")
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
                print("普通响应")
                content_type = resp.headers.get("content-type", "").lower()
                if "application/json" in content_type:
                    try:
                        data = resp.json()
                    except:
                        data = {"raw": resp.text}
                else:
                    data = {"raw": resp.text}
                return responses.JSONResponse(
                    content=data,
                    status_code=resp.status_code,
                    headers={
                        key: value
                        for key, value in resp.headers.items()
                        if key.lower() not in ['content-encoding', 'transfer-encoding']
                    }
                )

        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": f"代理请求失败: {str(e)}"}
            )

```

### sse请求接口参考

```python
from sse_starlette.sse import EventSourceResponse

async def f(
            access_token: str = Form(...),
            files: List[UploadFile] = File(...),
        ):
    try:
    	······
		async def generate():
            ······
            yield {
                "event": "error",
                "data": json.dumps({"error": "没有选择文件"}, ensure_ascii=False)
            }
            ······
            for f in files:
            	yield {}
                
         return EventSourceResponse(generate())
            
```

