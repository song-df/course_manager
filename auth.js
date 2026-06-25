/**
 * 智联学习云 — 鉴权模块（按需鉴权）
 * 每个课程的第一个视频免费看，后续视频需登录
 */

const Auth = {
  AUTH_BASE: '/api',

  token() {
    return localStorage.getItem('zl_token');
  },

  loggedIn() {
    return !!this.token();
  },

  async _fetch(path, options = {}) {
    const headers = { 'Content-Type': 'application/json', ...options.headers };
    const token = this.token();
    if (token) headers['Authorization'] = `Bearer ${token}`;
    const res = await fetch(`${this.AUTH_BASE}${path}`, { ...options, headers });
    return res.json();
  },

  async login(username, password) {
    const res = await fetch(this.AUTH_BASE + '/auth/login', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ username, password }),
    });
    const data = await res.json().catch(() => ({}));
    if (data.access_token) {
      localStorage.setItem('zl_token', data.access_token);
      localStorage.setItem('zl_user', JSON.stringify(data.user));
      return { success: true, user: data.user };
    }
    return { success: false, error: (data && data.detail) || '登录失败' };
  },

  async register(username, email, password, inviteCode) {
    // 1. 验证邀请码
    const verifyRes = await fetch(this.AUTH_BASE + '/redeem/external/verify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ system_secret: 'd04325db8e57094cf9d57b3127135f8a2ad28acb82f10f6b8926375e2d215a4a', code: inviteCode }),
    });
    if (verifyRes.status !== 200) {
      const err = await verifyRes.json().catch(() => ({}));
      return { success: false, error: err.detail || '邀请码无效' };
    }

    // 2. 注册到 wiselink
    const data = await this._fetch('/public/register', {
      method: 'POST',
      body: JSON.stringify({ username, email, password, referral_code: inviteCode }),
    });
    if (data.id) {
      return this.login(username, password);
    }
    return { success: false, error: data.detail || '注册失败' };
  },

  async me() {
    try {
      const data = await this._fetch('/auth/me');
      if (data.id) return data;
    } catch (e) {}
    return null;
  },

  logout() {
    localStorage.removeItem('zl_token');
    localStorage.removeItem('zl_user');
  },

  user() {
    try { return JSON.parse(localStorage.getItem('zl_user')); }
    catch (e) { return null; }
  },

  // ========== 按需登录弹窗 ==========
  // 当用户试图播放非免费视频时调用

  _mode: 'login',
  _resolve: null, // Promise resolver — 登录成功后调用

  /**
   * 弹出登录/注册窗口，返回 Promise
   * 用法: const ok = await Auth.requireLogin();
   *        if (!ok) return; // 用户取消
   */
  requireLogin() {
    if (this.loggedIn()) return Promise.resolve(true);
    return new Promise(resolve => {
      this._resolve = resolve;
      this._renderOverlay();
    });
  },

  _renderOverlay() {
    const old = document.getElementById('zl-auth-overlay');
    if (old) { old.remove(); }

    const html = `
    <div id="zl-auth-overlay" style="position:fixed;top:0;left:0;width:100%;height:100%;background:rgba(0,0,0,.75);z-index:9999;display:flex;align-items:center;justify-content:center">
      <div style="background:var(--bg2,#1e293b);border:1px solid var(--border,#334155);border-radius:12px;padding:32px;width:380px;max-width:90vw;box-shadow:0 8px 30px rgba(0,0,0,.5);position:relative">
        <!-- 关闭按钮 -->
        <span onclick="Auth._close()" style="position:absolute;top:12px;right:16px;font-size:20px;color:var(--text3,#64748b);cursor:pointer">&times;</span>

        <!-- 标题切换 -->
        <div style="display:flex;gap:16px;margin-bottom:18px;border-bottom:2px solid var(--border,#334155)">
          <div id="zl-tab-login" onclick="Auth._switchTab('login')" style="padding-bottom:8px;font-size:17px;font-weight:700;color:var(--text,#f1f5f9);border-bottom:2px solid var(--primary,#4f46e5);margin-bottom:-2px;cursor:pointer">登录</div>
          <div id="zl-tab-reg"  onclick="Auth._switchTab('register')" style="padding-bottom:8px;font-size:17px;font-weight:600;color:var(--text3,#64748b);cursor:pointer">注册</div>
        </div>

        <div style="font-size:13px;color:var(--text2,#94a3b8);margin-bottom:16px">登录后观看全部课程视频</div>

        <div id="zl-msg" style="background:#7f1d1d;color:#fca5a5;padding:8px 12px;border-radius:6px;font-size:13px;margin-bottom:14px;display:none"></div>

        <input id="zl-username" type="text" placeholder="用户名" style="width:100%;padding:10px 12px;border:1px solid var(--border,#334155);border-radius:8px;background:var(--bg3,#334155);color:var(--text,#f1f5f9);font-size:14px;margin-bottom:12px;outline:none;box-sizing:border-box">
        <input id="zl-password" type="password" placeholder="密码" style="width:100%;padding:10px 12px;border:1px solid var(--border,#334155);border-radius:8px;background:var(--bg3,#334155);color:var(--text,#f1f5f9);font-size:14px;margin-bottom:12px;outline:none;box-sizing:border-box" onkeydown="if(event.key==='Enter')Auth._submit()">
        <div id="zl-reg-extra" style="display:none">
          <input id="zl-email" type="text" placeholder="邮箱（必填）" style="width:100%;padding:10px 12px;border:1px solid var(--border,#334155);border-radius:8px;background:var(--bg3,#334155);color:var(--text,#f1f5f9);font-size:14px;margin-bottom:8px;outline:none;box-sizing:border-box" onkeydown="if(event.key=='Enter')Auth._submit()">
          <input id="zl-invite-code" type="text" placeholder="邀请码（必填）" style="width:100%;padding:10px 12px;border:1px solid var(--border,#334155);border-radius:8px;background:var(--bg3,#334155);color:var(--text,#f1f5f9);font-size:14px;margin-bottom:8px;outline:none;box-sizing:border-box;text-transform:uppercase" onkeydown="if(event.key==='Enter')Auth._submit()">
          <div style="text-align:right;margin-bottom:12px"><a href="https://wiselink.cc/course" target="_blank" style="color:var(--primary-light);font-size:12px;text-decoration:none">获取邀请码 →</a></div>
          <input id="zl-password2" type="password" placeholder="确认密码" style="width:100%;padding:10px 12px;border:1px solid var(--border,#334155);border-radius:8px;background:var(--bg3,#334155);color:var(--text,#f1f5f9);font-size:14px;margin-bottom:16px;outline:none;box-sizing:border-box" onkeydown="if(event.key==='Enter')Auth._submit()">
        </div>

        <button id="zl-submit-btn" onclick="Auth._submit()" style="width:100%;padding:10px;border:none;border-radius:8px;background:var(--primary,#4f46e5);color:#fff;font-size:15px;font-weight:600;cursor:pointer">登 录</button>

        <div id="zl-switch-hint" style="text-align:center;margin-top:14px;font-size:12px;color:var(--text3,#64748b)">
          还没有账号？<a href="javascript:Auth._switchTab('register')" style="color:var(--primary-light,#818cf8)">立即注册</a>
        </div>
      </div>
    </div>`;
    document.body.insertAdjacentHTML('beforeend', html);
  },

  _close() {
    const el = document.getElementById('zl-auth-overlay');
    if (el) el.remove();
    if (this._resolve) { this._resolve(false); this._resolve = null; }
  },

  _switchTab(mode) {
    this._mode = mode;
    const tabL = document.getElementById('zl-tab-login');
    const tabR = document.getElementById('zl-tab-reg');
    const btn  = document.getElementById('zl-submit-btn');
    const hint = document.getElementById('zl-switch-hint');
    const extra = document.getElementById('zl-reg-extra');
    const msg = document.getElementById('zl-msg');
    msg.style.display = 'none';

    if (mode === 'register') {
      tabL.style.cssText = 'padding-bottom:8px;font-size:17px;font-weight:600;color:var(--text3,#64748b);border-bottom:2px solid transparent;margin-bottom:-2px;cursor:pointer';
      tabR.style.cssText = 'padding-bottom:8px;font-size:17px;font-weight:700;color:var(--text,#f1f5f9);border-bottom:2px solid var(--primary,#4f46e5);margin-bottom:-2px;cursor:pointer';
      btn.textContent = '注 册';
      hint.innerHTML = '已有账号？<a href="javascript:Auth._switchTab(\'login\')" style="color:var(--primary-light,#818cf8)">立即登录</a>';
      extra.style.display = 'block';
    } else {
      tabL.style.cssText = 'padding-bottom:8px;font-size:17px;font-weight:700;color:var(--text,#f1f5f9);border-bottom:2px solid var(--primary,#4f46e5);margin-bottom:-2px;cursor:pointer';
      tabR.style.cssText = 'padding-bottom:8px;font-size:17px;font-weight:600;color:var(--text3,#64748b);border-bottom:2px solid transparent;margin-bottom:-2px;cursor:pointer';
      btn.textContent = '登 录';
      hint.innerHTML = '还没有账号？<a href="javascript:Auth._switchTab(\'register\')" style="color:var(--primary-light,#818cf8)">立即注册</a>';
      extra.style.display = 'none';
    }
  },

  async _submit() {
    const username = document.getElementById('zl-username').value.trim();
    const password = document.getElementById('zl-password').value;
    const msgEl = document.getElementById('zl-msg');
    const btn = document.getElementById('zl-submit-btn');

    if (!username || !password) {
      this._showMsg('请输入用户名和密码', 'error');
      return;
    }

    let inviteCode = '', email = '';
    if (this._mode === 'register') {
      email = document.getElementById('zl-email').value.trim();
      if (!email) { this._showMsg('请输入邮箱', 'error'); return; }
      inviteCode = document.getElementById('zl-invite-code').value.trim();
      if (!inviteCode) { this._showMsg('请输入邀请码', 'error'); return; }
      const pwd2 = document.getElementById('zl-password2').value;
      if (password !== pwd2) { this._showMsg('两次密码不一致', 'error'); return; }
      if (password.length < 6) { this._showMsg('密码至少6位', 'error'); return; }
    }

    btn.textContent = this._mode === 'register' ? '注册中...' : '登录中...';
    btn.disabled = true;

    const result = this._mode === 'register'
      ? await this.register(username, email, password, inviteCode)
      : await this.login(username, password);

    if (result.success) {
      document.getElementById('zl-auth-overlay').remove();
      this.renderUserArea('navUser');
      if (this._resolve) { this._resolve(true); this._resolve = null; }
    } else {
      this._showMsg(result.error || '操作失败', 'error');
      btn.textContent = this._mode === 'register' ? '注 册' : '登 录';
      btn.disabled = false;
    }
  },

  _showMsg(text, type) {
    const el = document.getElementById('zl-msg');
    el.textContent = text;
    el.style.display = 'block';
    el.style.background = type === 'success' ? '#14532d' : '#7f1d1d';
    el.style.color = type === 'success' ? '#86efac' : '#fca5a5';
  },

  /** 在导航栏渲染用户区 */
  renderUserArea(containerId) {
    const el = document.getElementById(containerId);
    if (!el) return;
    const u = this.user();
    if (u) {
      el.innerHTML = '<span style="color:#c7d2fe">👤 <b style="color:#fff">' + u.display_name + '</b></span>'
        + '<a href="javascript:Auth.logout();location.reload()" style="color:var(--text3);font-size:12px;margin-left:8px">退出</a>';
    } else {
      el.innerHTML = '<a href="javascript:Auth.requireLogin()" style="color:var(--primary-light)">🔐 登录</a>';
    }
  }
};
