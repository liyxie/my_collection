## Nginx Proxy Manager + 腾讯EdgeOne ，域名访问 出现 “JS 文件返回 text/html” 错误

报错信息：

```
Failed to load module script: Expected a JavaScript-or-Wasm module script but the server responded with a MIME type of "text/html". Strict MIME type checking is enforced for module scripts per HTML spec.
```

- **直接访问 `http://IP:3000` → 正常**
- **把其他域名映射到 3000 端口 → 也正常**
- **唯独 `xxx.xxx.com` 域名映射到 3000 端口 → 出现 “JS 文件返回 text/html” 错误**
- 并且这些报错的 JS 文件内容，其实是 **3000 端口服务返回的 HTML 页面**（不是 JS）。

### 问题

服务和 JS 文件本身没问题，问题出在 **反代链路（EdgeOne + Nginx Proxy Manager + 域名配置）**，而且是 **域名特定**。

常见可能性有：

1. **缓存污染（EdgeOne CDN / 浏览器缓存）**
   - EdgeOne 可能缓存了错误的响应，把 HTML 当成 JS 返回。
   - 所以同一个域名（`admin.liy1900.top`）一直错误，而其他域名映射同端口却正常。
2. **EdgeOne SSL / 回源模式配置问题**
   - EdgeOne 到源站请求 `admin.liy1900.top/js/xxx.js` 时，被源站（Nginx Proxy Manager）当成 SPA 路由请求，直接返回了 `index.html`。
   - 这通常出现在 **代理 Host Header 配置** 或 **Nginx try_files 配置**不对。
3. **Nginx Proxy Manager 的 Proxy Host 配置特殊**
   - 你可能在 NPM 里对 `admin.liy1900.top` 的 Proxy Host 配置了 `Force SSL` 或某些重定向规则，导致静态文件请求走错了。
   - 其他域名没有这种规则，所以没问题。

### 解决

在edgeone上删除域名管理，再重建，edgeone申请ssl证书