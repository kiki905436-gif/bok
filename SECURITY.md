# Security Policy

## Reporting a vulnerability

Please use GitHub's **Report a vulnerability** form in the Security tab. Do not disclose an unpatched vulnerability in a public issue.

Include affected versions, reproduction steps, impact, and any suggested mitigation. Never attach a real private vault, Personal Core, credential, token, or user conversation. Use synthetic data.

## Supported version

Security fixes currently target the latest public release.

## Security boundaries

Bok is local-first, binds its API to loopback, authenticates privileged endpoints, keeps Personal Core outside project repositories, and treats Markdown as the knowledge source of truth. See [Security and tests](Bok/docs/SECURITY-AND-TESTS.md).

---

# 安全策略

## 报告漏洞

请在 GitHub 仓库的 Security 页面使用 **Report a vulnerability** 私密提交，不要在公开 Issue 中披露尚未修复的漏洞。

请提供受影响版本、复现步骤、影响和可能的缓解方案。不要附带真实私人 Vault、Personal Core、凭证、token 或用户对话，请使用合成数据。

## 支持版本

安全修复目前面向最新公开版本。

## 安全边界

Bok 默认本地优先，API 仅绑定 loopback，对特权端点进行认证，将 Personal Core 放在项目仓库之外，并以 Markdown 作为知识事实源。完整说明见[安全与测试](Bok/docs/SECURITY-AND-TESTS.md)。
