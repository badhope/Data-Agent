# Security Policy / 安全政策

## Supported Versions / 支持的版本

| Version | Supported          |
| ------- | ------------------ |
| 1.0.x   | :white_check_mark: |
| < 1.0   | :x:                |

## Reporting a Vulnerability / 报告漏洞

If you discover a security vulnerability, please report it to us:

如果您发现安全漏洞，请向我们报告：

1. **Do not** open a public issue / **不要**公开创建Issue
2. Email us at: [security@example.com] / 发送邮件至: [security@example.com]
3. Include the following / 包含以下信息:
   - Description of the vulnerability / 漏洞描述
   - Steps to reproduce / 复现步骤
   - Possible impact / 可能的影响
   - Suggested fix (if any) / 建议的修复方案（如有）

We will respond within 48 hours and keep you updated on the progress.

我们将在48小时内回复，并随时向您通报进展。

## Security Best Practices / 安全最佳实践

When using this library, please follow these security guidelines:

使用本库时，请遵循以下安全准则：

- **API Keys**: Never commit API keys to version control / **API密钥**: 永远不要将API密钥提交到版本控制
- **Environment Variables**: Use `.env` files and add them to `.gitignore` / **环境变量**: 使用`.env`文件并将其添加到`.gitignore`
- **Input Validation**: Always validate user inputs before passing to AI / **输入验证**: 在传递给AI之前始终验证用户输入
- **Tool Execution**: Be cautious when executing tools with user-provided arguments / **工具执行**: 使用用户提供的参数执行工具时要谨慎

## Security Features / 安全特性

This library includes several security features:

本库包含多个安全特性：

- **No sensitive data logging**: API keys are never logged / **不记录敏感数据**: API密钥从不被记录
- **HTTPS only**: All API calls use HTTPS / **仅HTTPS**: 所有API调用使用HTTPS
- **Input sanitization**: Basic input validation / **输入清理**: 基本输入验证
- **Timeout protection**: Prevents hanging requests / **超时保护**: 防止请求挂起
