# 微信自动登录保持在线监控程序

## 项目简介

本项目是一个基于Python的微信自动登录监控程序，能够实时监控微信的在线状态，当检测到微信离线时自动调用登录窗口，确保微信始终保持在线状态。

## 功能特性

- ✅ **实时监控**: 定期检查微信在线状态
- ✅ **自动登录**: 检测到离线时自动弹出登录窗口
- ✅ **智能重试**: 支持配置重试次数和间隔
- ✅ **桌面通知**: 登录状态变化时发送桌面通知
- ✅ **日志记录**: 详细的运行日志和日志轮转
- ✅ **进程管理**: 自动启动微信进程（可配置）
- ✅ **配置灵活**: 支持多种参数自定义配置

## 系统要求

- Python 3.7+
- Windows 操作系统
- 已安装微信客户端

## 安装步骤

### 1. 克隆项目
```bash
git clone https://github.com/lixiangguang/wechat-auto-monitor.git
cd wechat-auto-monitor
```

### 2. 安装依赖
```bash
pip install -r requirements.txt
```

### 3. 配置参数（可选）
编辑 `config.py` 文件，根据需要调整监控参数：

```python
# 监控配置
MONITOR_CONFIG = {
    'check_interval': 30,      # 检查间隔（秒）
    'login_timeout': 60,       # 登录超时（秒）
    'retry_interval': 10,      # 重试间隔（秒）
    'max_retry_count': 3       # 最大重试次数
}
```

## 使用方法

### 快速启动（推荐）
双击运行 `start_monitor.bat` 批处理文件，或在命令行中执行：
```bash
start_monitor.bat
```

### 手动启动
```bash
python wechat_monitor_enhanced.py
```

### 运行测试
```bash
python test_wechat_monitor.py
```

## 项目结构

```
wechat-auto-monitor/
├── wechat_monitor_enhanced.py # 增强版主程序
├── wechat_utils.py           # 工具类文件
├── config.py                 # 配置文件
├── requirements.txt          # 依赖包列表
├── start_monitor.bat         # Windows启动脚本
├── test_wechat_monitor.py    # 测试文件
├── README.md                 # 项目说明文档
└── logs/                     # 日志目录（自动创建）
    └── wechat_monitor_YYYYMMDD.log
```

## 配置说明

### 监控配置 (MONITOR_CONFIG)
- `check_interval`: 状态检查间隔时间（秒）
- `login_timeout`: 登录等待超时时间（秒）
- `retry_interval`: 重试间隔时间（秒）
- `max_retry_count`: 最大重试次数

### 日志配置 (LOG_CONFIG)
- `log_level`: 日志级别（DEBUG/INFO/WARNING/ERROR）
- `log_retention_days`: 日志文件保留天数
- `log_file_max_size`: 日志文件最大大小（MB）

### 微信配置 (WECHAT_CONFIG)
- `process_name`: 微信进程名
- `install_path`: 微信安装路径（用于自动启动）
- `auto_start_wechat`: 是否自动启动微信

### 通知配置 (NOTIFICATION_CONFIG)
- `enable_desktop_notification`: 是否启用桌面通知
- `enable_sound_alert`: 是否启用声音提醒
- `notification_title`: 通知标题

## 运行日志

程序运行时会在 `logs/` 目录下生成日志文件，文件名格式为：`wechat_monitor_YYYYMMDD.log`

日志内容包括：
- 程序启动和停止时间
- 微信状态检查结果
- 自动登录尝试记录
- 错误和异常信息
- 通知发送记录

## 常见问题

### Q1: 程序提示找不到微信进程
**A**: 请确保微信已正确安装，并在 `config.py` 中配置正确的微信安装路径。

### Q2: 自动登录失败
**A**: 请检查：
1. 微信版本是否支持
2. 是否有其他程序占用微信
3. 网络连接是否正常

### Q3: 桌面通知不显示
**A**: 请确保：
1. 已安装 `plyer` 库
2. 系统允许程序发送通知
3. 在 `config.py` 中启用了桌面通知

### Q4: 程序占用资源过高
**A**: 可以适当增加 `check_interval` 的值，减少检查频率。

## 注意事项

1. **安全性**: 本程序不会存储任何微信账号信息，仅调用微信官方登录接口
2. **兼容性**: 程序基于 wxautox 库，可能受微信版本更新影响
3. **权限**: 程序需要足够的系统权限来监控和启动进程
4. **网络**: 确保网络连接稳定，避免误判微信离线状态

## 开发信息

- **作者**: 李祥光
- **创建时间**: 2025-06-24
- **版本**: 1.0.0
- **许可证**: MIT License

## 更新日志

### v1.0.0 (2025-06-24)
- 初始版本发布
- 实现基本的微信状态监控功能
- 支持自动登录和桌面通知
- 添加配置文件和日志管理
- 提供完整的工具类支持

## 贡献指南

欢迎提交 Issue 和 Pull Request 来改进这个项目。

## 技术支持

如有问题，请通过以下方式联系：
- 邮箱: 274030396@qq.com
- 创建 GitHub Issue

---

**免责声明**: 本程序仅供学习和个人使用，请遵守相关法律法规和微信使用条款。