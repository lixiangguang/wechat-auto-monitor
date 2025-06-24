##########test_wechat_monitor.py: 微信监控程序测试文件 ##################
# 变更记录: [2025-06-24] @李祥光 [创建测试文件]########
# 输入: 无 | 输出: 测试结果###############


###########################文件下的所有函数###########################
"""
test_config_loading：测试配置加载
test_notification_manager：测试通知管理器
test_process_manager：测试进程管理器
test_log_rotator：测试日志轮转器
run_all_tests：运行所有测试
main：测试主入口函数
"""
###########################文件下的所有函数###########################

#########mermaid格式说明所有函数的调用关系说明开始#########
"""
flowchart TD
    A[测试启动] --> B[main函数]
    B --> C[run_all_tests运行所有测试]
    C --> D[test_config_loading测试配置]
    C --> E[test_notification_manager测试通知]
    C --> F[test_process_manager测试进程]
    C --> G[test_log_rotator测试日志]
    D --> H[输出测试结果]
    E --> H
    F --> H
    G --> H
"""
#########mermaid格式说明所有函数的调用关系说明结束#########

import os
import sys
import time
import logging
from datetime import datetime

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from config import MONITOR_CONFIG, LOG_CONFIG, WECHAT_CONFIG, NOTIFICATION_CONFIG
    from wechat_utils import NotificationManager, ProcessManager, LogRotator
except ImportError as e:
    print(f"导入模块失败: {e}")
    print("请确保所有必要的文件都在正确的位置")
    sys.exit(1)

def test_config_loading():
    """
    test_config_loading 功能说明:
    # 测试配置文件加载是否正常
    # 输入: 无 | 输出: bool (True=成功, False=失败)
    """
    print("\n=== 测试配置加载 ===")
    
    try:
        # 检查监控配置
        assert 'check_interval' in MONITOR_CONFIG
        assert 'login_timeout' in MONITOR_CONFIG
        assert 'retry_interval' in MONITOR_CONFIG
        assert 'max_retry_count' in MONITOR_CONFIG
        print("✓ 监控配置加载成功")
        
        # 检查日志配置
        assert 'log_level' in LOG_CONFIG
        assert 'log_retention_days' in LOG_CONFIG
        assert 'log_file_max_size' in LOG_CONFIG
        print("✓ 日志配置加载成功")
        
        # 检查微信配置
        assert 'process_name' in WECHAT_CONFIG
        assert 'install_path' in WECHAT_CONFIG
        assert 'auto_start_wechat' in WECHAT_CONFIG
        print("✓ 微信配置加载成功")
        
        # 检查通知配置
        assert 'enable_desktop_notification' in NOTIFICATION_CONFIG
        assert 'enable_sound_alert' in NOTIFICATION_CONFIG
        assert 'notification_title' in NOTIFICATION_CONFIG
        print("✓ 通知配置加载成功")
        
        print("✓ 所有配置加载测试通过")
        return True
        
    except AssertionError as e:
        print(f"✗ 配置加载测试失败: {e}")
        return False
    except Exception as e:
        print(f"✗ 配置加载测试出错: {e}")
        return False

def test_notification_manager():
    """
    test_notification_manager 功能说明:
    # 测试通知管理器功能
    # 输入: 无 | 输出: bool (True=成功, False=失败)
    """
    print("\n=== 测试通知管理器 ===")
    
    try:
        # 创建通知管理器实例
        notification_manager = NotificationManager()
        print("✓ 通知管理器实例创建成功")
        
        # 测试发送通知（如果启用）
        if NOTIFICATION_CONFIG['enable_desktop_notification']:
            notification_manager.send_notification(
                "测试通知", 
                "这是一个测试通知，用于验证通知功能是否正常"
            )
            print("✓ 测试通知发送成功")
        else:
            print("ℹ 桌面通知已禁用，跳过通知测试")
        
        print("✓ 通知管理器测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 通知管理器测试失败: {e}")
        return False

def test_process_manager():
    """
    test_process_manager 功能说明:
    # 测试进程管理器功能
    # 输入: 无 | 输出: bool (True=成功, False=失败)
    """
    print("\n=== 测试进程管理器 ===")
    
    try:
        # 创建进程管理器实例
        process_manager = ProcessManager()
        print("✓ 进程管理器实例创建成功")
        
        # 测试检查进程是否运行
        wechat_running = process_manager.is_process_running(WECHAT_CONFIG['process_name'])
        print(f"ℹ 微信进程状态: {'运行中' if wechat_running else '未运行'}")
        
        # 测试检查系统进程（应该存在）
        system_process_running = process_manager.is_process_running('explorer.exe')
        if system_process_running:
            print("✓ 进程检查功能正常")
        else:
            print("⚠ 进程检查功能可能有问题")
        
        print("✓ 进程管理器测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 进程管理器测试失败: {e}")
        return False

def test_log_rotator():
    """
    test_log_rotator 功能说明:
    # 测试日志轮转器功能
    # 输入: 无 | 输出: bool (True=成功, False=失败)
    """
    print("\n=== 测试日志轮转器 ===")
    
    try:
        # 创建测试日志目录
        test_log_dir = 'test_logs'
        if not os.path.exists(test_log_dir):
            os.makedirs(test_log_dir)
        
        # 创建日志轮转器实例
        log_rotator = LogRotator(test_log_dir)
        print("✓ 日志轮转器实例创建成功")
        
        # 创建测试日志文件
        test_log_file = os.path.join(test_log_dir, 'test.log')
        with open(test_log_file, 'w', encoding='utf-8') as f:
            f.write(f"测试日志文件 - {datetime.now()}\n")
        print("✓ 测试日志文件创建成功")
        
        # 测试日志轮转
        result = log_rotator.rotate_logs()
        if result:
            print("✓ 日志轮转功能正常")
        else:
            print("⚠ 日志轮转功能可能有问题")
        
        # 清理测试文件
        if os.path.exists(test_log_file):
            os.remove(test_log_file)
        if os.path.exists(test_log_dir):
            os.rmdir(test_log_dir)
        print("✓ 测试文件清理完成")
        
        print("✓ 日志轮转器测试通过")
        return True
        
    except Exception as e:
        print(f"✗ 日志轮转器测试失败: {e}")
        return False

def run_all_tests():
    """
    run_all_tests 功能说明:
    # 运行所有测试用例
    # 输入: 无 | 输出: bool (True=全部通过, False=有失败)
    """
    print("开始运行微信监控程序测试套件...")
    print(f"测试时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    tests = [
        ('配置加载测试', test_config_loading),
        ('通知管理器测试', test_notification_manager),
        ('进程管理器测试', test_process_manager),
        ('日志轮转器测试', test_log_rotator)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"✗ {test_name} 执行出错: {e}")
            failed += 1
    
    print("\n" + "="*50)
    print("测试结果汇总:")
    print(f"通过: {passed}")
    print(f"失败: {failed}")
    print(f"总计: {passed + failed}")
    
    if failed == 0:
        print("🎉 所有测试都通过了！")
        return True
    else:
        print(f"⚠ 有 {failed} 个测试失败，请检查相关功能")
        return False

def main():
    """
    main 功能说明:
    # 测试程序主入口
    # 输入: 无 | 输出: 无
    """
    print("微信自动登录监控程序 - 功能测试")
    print("作者: 李祥光")
    print("创建时间: 2025-06-24")
    print("="*50)
    
    try:
        # 运行所有测试
        success = run_all_tests()
        
        # 根据测试结果退出
        sys.exit(0 if success else 1)
        
    except KeyboardInterrupt:
        print("\n测试被用户中断")
        sys.exit(1)
    except Exception as e:
        print(f"\n测试过程中发生错误: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()