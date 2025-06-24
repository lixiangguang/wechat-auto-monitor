##########config.py: 微信自动登录监控程序配置文件 ##################
# 变更记录: [2025-06-24] @李祥光 [创建配置文件]########
# 输入: 无 | 输出: 配置参数###############


###########################文件下的所有函数###########################
"""
无函数，仅包含配置参数
"""
###########################文件下的所有函数###########################

#########mermaid格式说明所有函数的调用关系说明开始#########
"""
flowchart TD
    A[配置文件] --> B[主程序读取配置]
    B --> C[应用配置参数]
"""
#########mermaid格式说明所有函数的调用关系说明结束#########

# 监控配置
MONITOR_CONFIG = {
    # 检查间隔时间（秒）
    'check_interval': 30,
    
    # 登录超时时间（秒）
    'login_timeout': 60,
    
    # 重试间隔时间（秒）
    'retry_interval': 10,
    
    # 最大重试次数
    'max_retry_count': 3
}

# 日志配置
LOG_CONFIG = {
    # 日志级别
    'log_level': 'INFO',
    
    # 日志文件保存天数
    'log_retention_days': 7,
    
    # 日志文件大小限制（MB）
    'log_file_max_size': 10
}

# 微信配置
WECHAT_CONFIG = {
    # 微信进程名
    'process_name': 'WeChat.exe',
    
    # 微信安装路径（可选，用于启动微信）
    'install_path': '',
    
    # 是否自动启动微信
    'auto_start_wechat': True
}

# 通知配置
NOTIFICATION_CONFIG = {
    # 是否启用桌面通知
    'enable_desktop_notification': True,
    
    # 是否启用声音提醒
    'enable_sound_alert': False,
    
    # 通知标题
    'notification_title': '微信监控提醒'
}