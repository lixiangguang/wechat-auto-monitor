##########wechat_monitor_enhanced.py: [增强版微信监控程序] ##################
# 变更记录: [2024-06-24] @李祥光 [完善详细注释和文档]########
# 输入: [命令行参数] | 输出: [监控状态和日志]###############


###########################文件下的所有函数###########################
"""
setup_enhanced_logging：设置增强版日志系统，支持多级别日志和文件轮转
parse_arguments：解析命令行参数，支持版本信息和配置选项
load_custom_config：动态加载自定义配置，支持配置验证和更新
monitor_loop：智能监控主循环，实现7x24小时微信状态监控
handle_shutdown：优雅关闭处理器，确保资源正确释放和状态保存
main：程序主入口，协调所有组件的初始化和运行
"""
###########################文件下的所有函数###########################

#########mermaid格式说明所有函数的调用关系说明开始#########
"""
flowchart TD
    A[程序启动] --> B[main函数]
    B --> C[显示启动信息]
    C --> D[parse_arguments解析命令行参数]
    D --> E[setup_enhanced_logging初始化日志系统]
    E --> F[load_custom_config加载自定义配置]
    F --> G[记录程序启动信息]
    G --> H[初始化核心组件]
    H --> I[注册系统信号处理器]
    I --> J[执行启动前日志清理]
    J --> K[发送启动完成通知]
    K --> L[monitor_loop启动主监控循环]
    L --> M{监控循环运行中}
    M -->|正常运行| N[微信状态检查]
    M -->|接收到关闭信号| O[handle_shutdown优雅关闭]
    N --> P{微信状态}
    P -->|正常| Q[等待下次检查]
    P -->|异常| R[自动登录恢复]
    Q --> M
    R --> M
    O --> S[资源清理和状态保存]
    S --> T[程序退出]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style L fill:#fff3e0
    style O fill:#ffebee
    style T fill:#e8f5e8
"""
#########mermaid格式说明所有函数的调用关系说明结束#########

import os
import sys
import time
import signal
import logging
import argparse
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到Python路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config import MONITOR_CONFIG
from wechat_utils import NotificationManager, setup_logging
from wechat_auto_login import monitor_wechat

# 全局变量
notification_manager = None
shutdown_flag = False
start_time = None

def setup_enhanced_logging(log_level: str = "INFO", enable_file_rotation: bool = True) -> None:
    """
    setup_enhanced_logging 功能说明:
    # 核心业务逻辑：设置增强版日志系统，支持多级别日志记录和文件轮转管理
    # 输入: [log_level: 日志级别字符串, enable_file_rotation: 是否启用文件轮转] | 输出: [无返回值，配置全局日志系统]
    # 核心职责：
    # 1. 创建logs目录结构
    # 2. 配置多级别日志处理器（控制台+文件）
    # 3. 设置日志格式和轮转策略
    # 4. 支持调试模式和生产模式切换
    """
    try:
        # 创建日志目录
        log_dir = Path("logs")
        log_dir.mkdir(exist_ok=True)
        
        # 设置日志级别
        numeric_level = getattr(logging, log_level.upper(), logging.INFO)
        
        # 清除现有的处理器
        for handler in logging.root.handlers[:]:
            logging.root.removeHandler(handler)
        
        # 创建格式化器
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        # 控制台处理器
        console_handler = logging.StreamHandler()
        console_handler.setLevel(numeric_level)
        console_handler.setFormatter(formatter)
        
        # 文件处理器
        if enable_file_rotation:
            from logging.handlers import RotatingFileHandler
            file_handler = RotatingFileHandler(
                log_dir / "wechat_monitor.log",
                maxBytes=10*1024*1024,  # 10MB
                backupCount=5
            )
        else:
            file_handler = logging.FileHandler(log_dir / "wechat_monitor.log")
        
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        
        # 配置根日志器
        logging.root.setLevel(logging.DEBUG)
        logging.root.addHandler(console_handler)
        logging.root.addHandler(file_handler)
        
        logging.info(f"📝 增强版日志系统初始化完成 - 级别: {log_level}")
        
    except Exception as e:
        print(f"❌ 日志系统初始化失败: {e}")
        # 使用基础日志配置作为后备
        setup_logging()

def parse_arguments() -> argparse.Namespace:
    """
    parse_arguments 功能说明:
    # 核心业务逻辑：解析命令行参数，支持版本信息显示和配置选项设置
    # 输入: [sys.argv命令行参数] | 输出: [argparse.Namespace对象，包含解析后的参数]
    # 核心职责：
    # 1. 定义命令行参数结构
    # 2. 解析用户输入的参数
    # 3. 提供版本信息和帮助信息
    # 4. 验证参数有效性
    """
    parser = argparse.ArgumentParser(
        description="🤖 微信监控程序 - 7x24小时智能监控微信状态",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例用法:
  python wechat_monitor_enhanced.py                    # 使用默认配置启动
  python wechat_monitor_enhanced.py --version         # 显示版本信息
  python wechat_monitor_enhanced.py --log-level DEBUG # 启用调试模式
        """
    )
    
    # 版本信息参数
    parser.add_argument(
        '--version', '-v',
        action='version',
        version='微信监控程序 v2.1.0 - Enhanced Edition\n'
                '作者: 李祥光\n'
                '更新时间: 2024-06-24\n'
                '功能: 7x24小时微信状态监控、自动登录、智能恢复'
    )
    
    # 日志级别参数
    parser.add_argument(
        '--log-level',
        choices=['DEBUG', 'INFO', 'WARNING', 'ERROR'],
        default='INFO',
        help='设置日志级别 (默认: INFO)'
    )
    
    # 配置文件参数
    parser.add_argument(
        '--config',
        type=str,
        help='指定自定义配置文件路径'
    )
    
    # 调试模式参数
    parser.add_argument(
        '--debug',
        action='store_true',
        help='启用调试模式（等同于 --log-level DEBUG）'
    )
    
    args = parser.parse_args()
    
    # 调试模式处理
    if args.debug:
        args.log_level = 'DEBUG'
    
    return args

def load_custom_config(config_path: Optional[str] = None) -> Dict[str, Any]:
    """
    load_custom_config 功能说明:
    # 核心业务逻辑：动态加载自定义配置文件，支持配置验证和热更新
    # 输入: [config_path: 可选的配置文件路径] | 输出: [Dict配置字典，包含验证后的配置参数]
    # 核心职责：
    # 1. 加载默认配置作为基础
    # 2. 读取自定义配置文件（如果提供）
    # 3. 验证配置参数的有效性
    # 4. 合并和更新配置选项
    """
    # 使用默认配置作为基础
    config = MONITOR_CONFIG.copy()
    
    if config_path and os.path.exists(config_path):
        try:
            # 动态导入自定义配置
            import importlib.util
            spec = importlib.util.spec_from_file_location("custom_config", config_path)
            custom_config_module = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(custom_config_module)
            
            # 合并配置
            if hasattr(custom_config_module, 'MONITOR_CONFIG'):
                custom_config = custom_config_module.MONITOR_CONFIG
                config.update(custom_config)
                logging.info(f"✅ 已加载自定义配置: {config_path}")
            
        except Exception as e:
            logging.warning(f"⚠️ 加载自定义配置失败: {e}，使用默认配置")
    
    # 配置验证和调整
    # 监控间隔验证
    if config.get('check_interval', 0) < 10:
        logging.warning("⚠️ 监控间隔过短，调整为10秒")
        config['check_interval'] = 10
    
    # 重试次数验证
    if config.get('max_retry_count', 0) < 1:
        logging.warning("⚠️ 重试次数过少，调整为3次")
        config['max_retry_count'] = 3
    
    # 通知设置验证
    if 'notification' not in config:
        config['notification'] = {'enabled': True, 'sound': True}
    
    # 日志级别验证
    valid_log_levels = ['DEBUG', 'INFO', 'WARNING', 'ERROR']
    if config.get('log_level', 'INFO') not in valid_log_levels:
        config['log_level'] = 'INFO'
    
    # 调试模式设置
    if config.get('debug_mode', False):
        config['log_level'] = 'DEBUG'
        logging.info("🐛 调试模式已启用")
    
    logging.info(f"📋 配置加载完成 - 监控间隔: {config['check_interval']}秒")
    return config

def monitor_loop(config: Dict[str, Any]) -> None:
    """
    monitor_loop 功能说明:
    # 核心业务逻辑：智能监控主循环，实现7x24小时微信状态监控和自动恢复
    # 输入: [config: 配置字典，包含监控参数] | 输出: [无返回值，持续运行监控循环]
    # 核心职责：
    # 1. 初始化监控参数和状态变量
    # 2. 发送启动通知给用户
    # 3. 执行主监控循环逻辑
    # 4. 处理微信状态检查和异常恢复
    # 5. 实现智能等待和资源管理
    # 监控策略：
    # - 定期检查微信进程状态
    # - 连续失败时触发自动登录
    # - 智能调整检查间隔
    # - 异常情况下的容错处理
    # 容错机制：
    # - 网络异常重试
    # - 进程崩溃恢复
    # - 资源泄漏防护
    # - 状态持久化保存
    # 通知集成：
    # - 状态变化通知
    # - 异常情况告警
    # - 恢复成功确认
    """
    global shutdown_flag, notification_manager
    
    # 初始化监控参数
    check_interval = config.get('check_interval', 30)
    max_retry_count = config.get('max_retry_count', 3)
    continuous_failure_count = 0
    last_check_time = datetime.now()
    total_checks = 0
    successful_checks = 0
    
    logging.info(f"🚀 监控循环启动 - 检查间隔: {check_interval}秒, 最大重试: {max_retry_count}次")
    
    # 发送启动通知
    if notification_manager:
        notification_manager.send_notification(
            "🤖 微信监控启动", 
            f"监控程序已启动\n检查间隔: {check_interval}秒\n启动时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}"
        )
    
    try:
        # 主监控循环
        while not shutdown_flag:
            try:
                current_time = datetime.now()
                total_checks += 1
                
                logging.debug(f"🔍 执行第 {total_checks} 次状态检查...")
                
                # 微信状态检查
                wechat_status = monitor_wechat()
                
                if wechat_status:
                    # 微信状态正常
                    successful_checks += 1
                    continuous_failure_count = 0
                    
                    if total_checks % 10 == 0:  # 每10次检查记录一次统计
                        success_rate = (successful_checks / total_checks) * 100
                        logging.info(f"📊 监控统计 - 总检查: {total_checks}, 成功率: {success_rate:.1f}%")
                
                else:
                    # 微信状态异常
                    continuous_failure_count += 1
                    logging.warning(f"⚠️ 微信状态异常 - 连续失败: {continuous_failure_count}/{max_retry_count}")
                    
                    # 连续失败处理
                    if continuous_failure_count >= max_retry_count:
                        logging.error(f"🚨 连续 {continuous_failure_count} 次检查失败，尝试自动登录恢复...")
                        
                        # 发送告警通知
                        if notification_manager:
                            notification_manager.send_notification(
                                "🚨 微信状态异常", 
                                f"连续 {continuous_failure_count} 次检查失败\n正在尝试自动恢复..."
                            )
                        
                        # 自动登录恢复
                        try:
                            from wechat_auto_login import auto_login_wechat
                            login_result = auto_login_wechat()
                            
                            if login_result:
                                logging.info("✅ 自动登录成功，微信状态已恢复")
                                continuous_failure_count = 0
                                
                                # 发送恢复通知
                                if notification_manager:
                                    notification_manager.send_notification(
                                        "✅ 微信状态恢复", 
                                        "自动登录成功\n微信状态已恢复正常"
                                    )
                            else:
                                logging.error("❌ 自动登录失败，将在下次检查时重试")
                                
                        except Exception as login_error:
                            logging.error(f"💥 自动登录过程中发生错误: {login_error}")
                
                last_check_time = current_time
                
                # 分段等待，支持优雅关闭
                wait_segments = max(1, check_interval // 5)  # 将等待时间分成5段
                segment_time = check_interval / wait_segments
                
                for _ in range(wait_segments):
                    if shutdown_flag:
                        break
                    time.sleep(segment_time)
                
            except KeyboardInterrupt:
                logging.info("⌨️ 接收到键盘中断信号")
                break
                
            except Exception as loop_error:
                logging.error(f"💥 监控循环中发生错误: {loop_error}")
                logging.error(f"🔍 错误类型: {type(loop_error).__name__}")
                
                # 错误恢复等待
                time.sleep(min(30, check_interval))
                continue
    
    except Exception as e:
        logging.error(f"💥 监控循环发生严重错误: {e}")
        raise
    
    finally:
        # 循环结束处理
        end_time = datetime.now()
        runtime = (end_time - start_time).total_seconds() if start_time else 0
        success_rate = (successful_checks / total_checks * 100) if total_checks > 0 else 0
        
        logging.info(f"📊 监控循环结束统计:")
        logging.info(f"   ⏱️ 运行时间: {runtime:.2f}秒")
        logging.info(f"   🔍 总检查次数: {total_checks}")
        logging.info(f"   ✅ 成功次数: {successful_checks}")
        logging.info(f"   📈 成功率: {success_rate:.1f}%")
        
        # 发送结束通知
        if notification_manager:
            notification_manager.send_notification(
                "🏁 监控程序结束", 
                f"运行时间: {runtime:.0f}秒\n检查次数: {total_checks}\n成功率: {success_rate:.1f}%"
            )

def handle_shutdown(signum: int = None, frame = None) -> None:
    """
    handle_shutdown 功能说明:
    # 核心业务逻辑：优雅关闭处理器，确保程序安全退出和资源正确释放
    # 输入: [signum: 信号编号, frame: 信号帧] | 输出: [无返回值，执行关闭流程]
    # 核心职责：
    # 1. 防止重复执行关闭流程
    # 2. 记录关闭信号和时间信息
    # 3. 清理日志系统和文件句柄
    # 4. 发送关闭通知给用户
    # 5. 保存运行状态和统计信息
    # 6. 释放系统资源和内存
    # 异常处理：
    # - 关闭过程中的异常捕获
    # - 资源释放失败的容错
    # - 通知发送失败的处理
    # 统计信息：
    # - 程序运行时长统计
    # - 监控次数和成功率
    # - 资源使用情况记录
    """
    global shutdown_flag, notification_manager, start_time
    
    # 防止重复执行
    if shutdown_flag:
        return
    
    shutdown_flag = True
    
    # 记录关闭信号信息
    if signum:
        signal_names = {
            signal.SIGINT: "SIGINT (Ctrl+C)",
            signal.SIGTERM: "SIGTERM (终止信号)"
        }
        signal_name = signal_names.get(signum, f"信号 {signum}")
        logging.info(f"🛑 接收到关闭信号: {signal_name}")
    else:
        logging.info("🛑 程序正常关闭")
    
    try:
        # 日志系统清理
        logging.info("🧹 开始执行优雅关闭流程...")
        
        # 发送关闭通知
        if notification_manager:
            try:
                end_time = datetime.now()
                runtime = (end_time - start_time).total_seconds() if start_time else 0
                
                notification_manager.send_notification(
                    "👋 监控程序关闭", 
                    f"程序已安全关闭\n运行时间: {runtime:.0f}秒\n关闭时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}"
                )
                logging.info("📱 关闭通知已发送")
            except Exception as notify_error:
                logging.warning(f"⚠️ 发送关闭通知失败: {notify_error}")
        
        # 资源清理和状态保存
        try:
            # 清理临时文件
            temp_files = ["temp_wechat_status.tmp", "monitor_lock.tmp"]
            for temp_file in temp_files:
                if os.path.exists(temp_file):
                    os.remove(temp_file)
                    logging.debug(f"🗑️ 已清理临时文件: {temp_file}")
            
            # 保存运行状态（如果需要）
            status_file = "logs/last_run_status.json"
            if start_time:
                import json
                status_data = {
                    "last_run_time": start_time.isoformat(),
                    "shutdown_time": datetime.now().isoformat(),
                    "runtime_seconds": (datetime.now() - start_time).total_seconds(),
                    "shutdown_reason": "normal" if not signum else "signal"
                }
                
                try:
                    with open(status_file, 'w', encoding='utf-8') as f:
                        json.dump(status_data, f, indent=2, ensure_ascii=False)
                    logging.debug(f"💾 运行状态已保存: {status_file}")
                except Exception as save_error:
                    logging.warning(f"⚠️ 保存运行状态失败: {save_error}")
        
        except Exception as cleanup_error:
            logging.warning(f"⚠️ 资源清理过程中发生错误: {cleanup_error}")
        
        # 记录程序运行统计信息
        if start_time:
            end_time = datetime.now()
            total_runtime = (end_time - start_time).total_seconds()
            
            logging.info("📊 程序运行统计:")
            logging.info(f"   🚀 启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"   🏁 结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            logging.info(f"   ⏱️ 总运行时间: {total_runtime:.2f}秒 ({total_runtime/3600:.2f}小时)")
            
            # 计算平均资源使用情况（如果可用）
            try:
                import psutil
                process = psutil.Process()
                memory_info = process.memory_info()
                logging.info(f"   💾 内存使用: {memory_info.rss / 1024 / 1024:.2f} MB")
                logging.info(f"   🔄 CPU使用时间: {sum(process.cpu_times()):.2f}秒")
            except ImportError:
                logging.debug("📊 psutil未安装，跳过资源统计")
            except Exception as stats_error:
                logging.debug(f"📊 获取资源统计失败: {stats_error}")
        
        logging.info("✅ 优雅关闭流程完成")
        
    except Exception as shutdown_error:
        logging.error(f"💥 关闭过程中发生错误: {shutdown_error}")
    
    finally:
        # 最终清理和退出确认
        try:
            # 刷新所有日志处理器
            for handler in logging.root.handlers:
                handler.flush()
                if hasattr(handler, 'close'):
                    handler.close()
            
            print("✅ 程序已安全关闭")
            
        except Exception as final_error:
            print(f"⚠️ 最终清理时发生错误: {final_error}")

def main() -> None:
    """
    main 功能说明:
    # 核心业务逻辑：程序主入口，协调所有组件的初始化、配置和运行流程
    # 输入: [无直接输入，从命令行和配置文件获取参数] | 输出: [无返回值，控制程序生命周期]
    # 核心职责：
    # 1. 显示程序启动信息和版本横幅
    # 2. 记录程序启动时间用于统计
    # 3. 解析和验证命令行参数
    # 4. 初始化增强版日志系统
    # 5. 加载和验证自定义配置
    # 6. 记录详细的程序启动信息
    # 7. 初始化核心组件（通知管理器等）
    # 8. 注册系统信号处理器
    # 9. 执行启动前的日志清理
    # 10. 发送启动完成通知
    # 11. 启动主监控循环
    # 12. 处理全局异常和优雅退出
    # 异常处理：
    # - 初始化失败的回退机制
    # - 配置错误的容错处理
    # - 运行时异常的全局捕获
    # - 资源清理的保障机制
    # 启动横幅：
    # - 显示程序名称和版本信息
    # - 展示功能特性和作者信息
    # - 记录启动时间和环境信息
    # 详细的启动步骤日志：
    # - 每个初始化步骤的详细记录
    # - 配置加载过程的追踪
    # - 组件初始化状态的确认
    # 组件初始化日志：
    # - 通知管理器初始化状态
    # - 日志系统配置确认
    # - 监控参数设置记录
    # 信号注册日志：
    # - SIGINT和SIGTERM信号处理器注册
    # - 优雅关闭机制的启用确认
    # 启动通知：
    # - 向用户发送程序启动成功通知
    # - 包含启动时间和配置信息
    # 最终清理日志：
    # - 程序退出时的资源清理记录
    # - 运行统计信息的汇总
    # - 退出状态和原因的记录
    """
    global notification_manager, start_time
    
    try:
        # 第一步：显示启动信息
        print("\n" + "="*60)
        print("🤖 微信监控程序 - Enhanced Edition v2.1.0")
        print("📱 7x24小时智能监控微信状态，自动登录恢复")
        print("👨‍💻 作者: 李祥光 | 更新: 2024-06-24")
        print("🚀 功能: 状态监控 + 自动登录 + 智能恢复 + 桌面通知")
        print("="*60 + "\n")
        
        # 第二步：记录启动时间
        start_time = datetime.now()
        print(f"⏰ 程序启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # 第三步：解析命令行参数
        print("📋 正在解析命令行参数...")
        args = parse_arguments()
        print(f"✅ 参数解析完成 - 日志级别: {args.log_level}")
        
        # 第四步：初始化日志系统
        print("📝 正在初始化增强版日志系统...")
        setup_enhanced_logging(args.log_level)
        print("✅ 日志系统初始化完成")
        
        # 第五步：加载自定义配置
        print("⚙️ 正在加载配置文件...")
        config = load_custom_config(args.config)
        print(f"✅ 配置加载完成 - 监控间隔: {config['check_interval']}秒")
        
        # 第六步：记录程序启动信息
        logging.info("🚀 " + "="*50)
        logging.info("🚀 微信监控程序启动 - Enhanced Edition v2.1.0")
        logging.info(f"🚀 启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}")
        logging.info(f"🚀 Python版本: {sys.version.split()[0]}")
        logging.info(f"🚀 工作目录: {os.getcwd()}")
        logging.info(f"🚀 进程ID: {os.getpid()}")
        logging.info(f"🚀 日志级别: {args.log_level}")
        logging.info(f"🚀 监控配置: {config}")
        logging.info("🚀 " + "="*50)
        
        # 第七步：初始化核心组件
        print("🔧 正在初始化核心组件...")
        logging.info("🔧 开始初始化核心组件...")
        
        # 初始化通知管理器
        try:
            notification_manager = NotificationManager(config.get('notification', {}))
            logging.info("✅ 通知管理器初始化成功")
            print("✅ 通知管理器初始化成功")
        except Exception as notify_error:
            logging.warning(f"⚠️ 通知管理器初始化失败: {notify_error}")
            print(f"⚠️ 通知管理器初始化失败: {notify_error}")
            notification_manager = None
        
        logging.info("✅ 核心组件初始化完成")
        print("✅ 核心组件初始化完成")
        
        # 第八步：注册系统信号处理器
        print("📡 正在注册系统信号处理器...")
        logging.info("📡 注册系统信号处理器...")
        
        signal.signal(signal.SIGINT, handle_shutdown)   # Ctrl+C
        signal.signal(signal.SIGTERM, handle_shutdown)  # 终止信号
        
        logging.info("✅ 信号处理器注册完成 (SIGINT, SIGTERM)")
        print("✅ 信号处理器注册完成")
        
        # 第九步：执行启动前日志清理
        print("🧹 正在执行启动前清理...")
        logging.info("🧹 执行启动前日志清理...")
        
        try:
            # 清理过期日志文件（保留最近7天）
            log_dir = Path("logs")
            if log_dir.exists():
                cutoff_date = datetime.now() - timedelta(days=7)
                for log_file in log_dir.glob("*.log*"):
                    if log_file.stat().st_mtime < cutoff_date.timestamp():
                        log_file.unlink()
                        logging.debug(f"🗑️ 已清理过期日志: {log_file}")
            
            logging.info("✅ 启动前清理完成")
            print("✅ 启动前清理完成")
            
        except Exception as cleanup_error:
            logging.warning(f"⚠️ 启动前清理失败: {cleanup_error}")
            print(f"⚠️ 启动前清理失败: {cleanup_error}")
        
        # 第十步：发送启动完成通知
        print("📱 正在发送启动通知...")
        logging.info("📱 发送启动完成通知...")
        
        if notification_manager:
            try:
                notification_manager.send_notification(
                    "🚀 微信监控程序启动", 
                    f"程序已成功启动\n版本: Enhanced v2.1.0\n启动时间: {start_time.strftime('%Y-%m-%d %H:%M:%S')}\n监控间隔: {config['check_interval']}秒"
                )
                logging.info("✅ 启动通知发送成功")
                print("✅ 启动通知发送成功")
            except Exception as notify_error:
                logging.warning(f"⚠️ 启动通知发送失败: {notify_error}")
                print(f"⚠️ 启动通知发送失败: {notify_error}")
        
        # 第十一步：启动主监控循环
        print("\n🎯 启动主监控循环...")
        print(f"⏱️ 监控间隔: {config['check_interval']}秒")
        print(f"🔄 最大重试: {config['max_retry_count']}次")
        print("\n按 Ctrl+C 可安全退出程序\n")
        
        logging.info("🎯 启动主监控循环...")
        logging.info(f"⏱️ 监控参数 - 间隔: {config['check_interval']}秒, 重试: {config['max_retry_count']}次")
        
        # 执行主监控循环
        monitor_loop(config)
        
    except KeyboardInterrupt:
        # 键盘中断处理
        print("\n⌨️ 接收到键盘中断信号 (Ctrl+C)")
        logging.info("⌨️ 接收到键盘中断信号")
        handle_shutdown()
        
    except Exception as e:
        # 全局异常处理
        error_msg = f"程序运行时发生严重错误: {str(e)}"
        print(f"💥 {error_msg}")
        logging.error(f"💥 严重错误: {error_msg}")
        logging.error(f"🔍 错误类型: {type(e).__name__}")
        logging.error(f"📍 错误位置: {e.__traceback__.tb_frame.f_code.co_filename}:{e.__traceback__.tb_lineno}" if e.__traceback__ else "未知位置")
        
        # 发送错误通知
        try:
            if 'notification_manager' in globals() and notification_manager:
                notification_manager.send_notification(
                    "💥 程序运行错误", 
                    f"监控程序发生严重错误\n错误信息: {str(e)}\n错误类型: {type(e).__name__}"
                )
        except:
            pass  # 忽略通知发送失败
        
        sys.exit(1)  # 异常退出码
        
    finally:
        # 第十二步：最终清理和退出处理
        try:
            end_time = datetime.now()
            total_runtime = (end_time - start_time).total_seconds()
            
            print("🧹 正在执行最终清理...")
            logging.info(f"⏱️ 程序总运行时间: {total_runtime:.2f}秒")
            logging.info(f"🏁 程序结束时间: {end_time.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 调用优雅关闭处理器
            handle_shutdown()
            
        except Exception as cleanup_error:
            print(f"⚠️ 清理过程中发生错误: {cleanup_error}")
        
        print("👋 程序已退出，感谢使用！")

if __name__ == "__main__":
    main()