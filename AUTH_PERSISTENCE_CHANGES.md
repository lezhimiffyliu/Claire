# 🔐 认证持久化改造总结

## 问题分析

### ❌ 原有问题

1. **OAuth Session 不持久化**
   - 登录后只保存在 `st.session_state`（服务器端内存）
   - 刷新页面 → session_state 清空 → 用户登出
   - **每次刷新都要重新登录 Google OAuth**

2. **Learning Context 无法恢复**
   - 虽然 `WorkspaceContext` 保存在 Supabase
   - 但需要 `user.id` 才能查询
   - 刷新后 `user = None` → 无法加载 context
   - **已选课程、diagnostic进度全部丢失**

### ✅ 解决方案

**核心思路**：将 Supabase session tokens 持久化到浏览器加密 cookies

```
登录成功
    ↓
保存 access_token + refresh_token 到加密 cookie
    ↓
刷新页面
    ↓
从 cookie 读取 tokens
    ↓
调用 Supabase set_session() 恢复登录状态
    ↓
用 user.id 加载 WorkspaceContext
    ↓
✅ 自动恢复：课程选择、diagnostic进度、练习题进度
```

---

## 实现改动

### 1️⃣ 添加依赖

**requirements.txt**
```diff
+ # Cookie management for persistent sessions
+ streamlit-cookies-manager>=0.2.0
```

**安装命令**
```bash
pip install streamlit-cookies-manager
```

### 2️⃣ 环境变量

**.env**
```diff
+ # Cookie encryption password for persistent sessions
+ COOKIE_PASSWORD=claire-cookie-secret-change-me-in-production-use-random-string
```

⚠️ **生产环境必须修改**：使用强随机字符串（至少32字符）

### 3️⃣ auth.py 改造

**新增功能**：

1. **`get_cookie_manager()`** - 初始化加密cookie管理器
2. **`restore_session_from_cookie()`** - 从cookie恢复登录状态
3. **`handle_oauth_callback()`** - 登录成功后保存到cookie
4. **`sign_out()`** - 登出时清除cookie

**关键代码**：

```python
def restore_session_from_cookie() -> bool:
    """页面启动时调用，从cookie恢复session"""
    cookies = get_cookie_manager()
    access_token = cookies.get("access_token")
    refresh_token = cookies.get("refresh_token")

    if access_token and refresh_token:
        # 调用 Supabase set_session 恢复登录
        resp = client.auth.set_session(access_token, refresh_token)
        if resp.user:
            st.session_state.user = resp.user
            st.session_state.supabase_session = resp.session
            return True
    return False
```

### 4️⃣ app.py 启动逻辑

**修改点**：在 OAuth callback 之前先恢复 session

```python
# 🆕 Step 1: 先从cookie恢复session（如果有）
from auth import restore_session_from_cookie
if restore_session_from_cookie():
    pass  # Session restored successfully

# Step 2: 处理新登录的OAuth callback
if handle_oauth_callback():
    st.rerun()
```

**执行顺序**：
1. 页面加载
2. 尝试从cookie恢复 → 成功则 `user` 有值
3. 加载 `WorkspaceContext.load(user.id)` → 恢复课程和进度
4. 用户看到之前的状态 ✅

---

## 测试验证

### ✅ 运行测试脚本
```bash
python test_auth_persistence.py
```

**预期输出**：
```
✅ SUPABASE_URL: https://jesfegjblkdd...
✅ SUPABASE_KEY: eyJhbGciOiJIUzI1NiIs...
✅ COOKIE_PASSWORD: claire-cookie-secret...
✅ Cookie manager initialized successfully
✅ All checks passed!
```

### 🧪 手动测试流程

1. **启动应用**
   ```bash
   streamlit run app.py
   ```

2. **第一次登录**
   - 点击 "Sign in with Google"
   - 完成 Google OAuth
   - 选择课程（如 Math 124）
   - 完成 diagnostic test

3. **刷新页面测试**
   - 按 `Cmd+R` (Mac) 或 `Ctrl+R` (Windows)
   - ✅ **应该保持登录状态**
   - ✅ **课程选择保留**（显示 Math 124）
   - ✅ **直接进入 practice 模式**（跳过 diagnostic）

4. **关闭浏览器标签页测试**
   - 关闭标签页
   - 重新打开 `http://localhost:8502`
   - ✅ **仍然保持登录** + **进度保留**

5. **登出测试**
   - 点击侧边栏 "Sign out"
   - ✅ **清除所有状态**
   - 刷新页面应该回到未登录状态

---

## 技术细节

### 🔒 安全性

1. **Token 加密存储**
   - 使用 `EncryptedCookieManager`
   - 基于 `cryptography` 库的 Fernet 对称加密
   - 需要 `COOKIE_PASSWORD` 密钥

2. **Token 自动刷新**
   - `restore_session_from_cookie()` 调用 `set_session()`
   - Supabase 自动刷新过期的 access_token
   - 新 token 更新回 cookie

3. **过期处理**
   - 如果 refresh_token 也过期 → 清除 cookie
   - 用户需要重新登录

### 📦 Cookie 存储内容

| Key | Value | 说明 |
|-----|-------|------|
| `claire_auth_access_token` | JWT token | Supabase access token |
| `claire_auth_refresh_token` | JWT token | Supabase refresh token |
| `claire_auth_user_id` | UUID | 用户 ID |
| `claire_auth_user_email` | string | 用户邮箱（调试用） |

### 🔄 执行流程

```
页面加载
    │
    ├─► 1. restore_session_from_cookie()
    │       ├─► 有 cookie → set_session() → st.session_state.user ✅
    │       └─► 无 cookie → 跳过
    │
    ├─► 2. handle_oauth_callback()
    │       └─► 处理新登录 → 保存到 cookie
    │
    ├─► 3. WorkspaceContext.load(user.id)
    │       ├─► user 存在 → 加载 Supabase 数据 ✅
    │       └─► user 不存在 → 跳过
    │
    └─► 4. 恢复 session_state
            ├─► mode = "diagnostic" / "practice"
            ├─► course = "124" / "125" / "126"
            └─► 题目进度
```

---

## 调试

### 查看 Cookie
**浏览器 DevTools**：
1. 打开 `http://localhost:8502`
2. F12 → Application/Storage → Cookies
3. 查看 `claire_auth_*` 开头的 cookie

### 查看日志
```bash
streamlit run app.py --logger.level=debug
```

**关键日志**：
```
[AUTH DEBUG] Saved session to cookies for user xxx@gmail.com
[AUTH DEBUG] ✅ Session restored for xxx@gmail.com
[AUTH DEBUG] Cleared cookies on sign out
```

### 常见问题

**Q: 刷新后还是未登录？**
- 检查 `.env` 中 `COOKIE_PASSWORD` 是否存在
- 检查浏览器是否禁用了 cookie
- 查看控制台是否有 `[AUTH DEBUG]` 错误日志

**Q: Token 过期怎么办？**
- Supabase refresh_token 默认 30 天有效
- 超过 30 天需要重新登录
- 可在 Supabase Dashboard 调整过期时间

**Q: 生产环境部署注意事项？**
- 修改 `COOKIE_PASSWORD` 为强随机字符串
- 使用 HTTPS（cookie 安全传输）
- 设置 cookie `secure=True, httponly=True`（需要修改库配置）

---

## 对比总结

| 场景 | 改造前 ❌ | 改造后 ✅ |
|-----|-----------|-----------|
| 刷新页面 | 登出 + 丢失进度 | 保持登录 + 恢复进度 |
| 关闭标签页重开 | 需要重新登录 | 自动恢复 |
| 选课后刷新 | 回到选课页面 | 保留课程选择 |
| Diagnostic 后刷新 | 重新做 diagnostic | 直接进入练习 |
| 练习到一半刷新 | 从头开始 | 恢复到当前题目 |
| 登出 | 清除 session_state | 清除 session_state + cookie |

---

## 下一步优化（可选）

1. **Cookie 过期时间配置**
   - 添加环境变量 `COOKIE_EXPIRY_DAYS=30`
   - 自定义 cookie 有效期

2. **多设备同步**
   - Cookie 只在单个浏览器有效
   - 如需跨设备：依赖 Supabase WorkspaceContext（已有）

3. **记住我功能**
   - 添加 UI 选项："Remember me for 30 days"
   - 根据选择设置不同的 cookie 有效期

4. **安全增强**
   - 添加 CSRF token
   - Cookie 设置 `SameSite=Strict`
   - 定期轮换 access_token

---

## 文件变更清单

✅ **已修改**：
- `requirements.txt` - 添加 `streamlit-cookies-manager`
- `.env` - 添加 `COOKIE_PASSWORD`
- `auth.py` - 添加 cookie 持久化逻辑
- `app.py` - 添加启动时恢复 session

🆕 **新增**：
- `test_auth_persistence.py` - 测试脚本
- `AUTH_PERSISTENCE_CHANGES.md` - 本文档

---

## 总结

通过引入 **加密 cookie** 持久化 Supabase session tokens，彻底解决了：
1. ✅ 刷新页面需要重新登录的问题
2. ✅ Learning context 无法恢复的问题

用户体验提升：
- 📱 登录一次，刷新/关闭浏览器都保持登录
- 📚 课程选择、diagnostic、练习进度全部自动恢复
- 🚀 无感知的状态恢复，就像原生应用一样

**现在可以正常使用了！** 🎉
