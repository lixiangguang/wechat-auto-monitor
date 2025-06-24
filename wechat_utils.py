##########wechat_utils.py: [微信监控工具类集合] ##################
# 变更记录: [2025-06-24] @李祥光 [创建微信自动登录工具类]########
# 变更记录: [2025-06-24] @李祥光 [修复API调用错误：使用IsOnline和LoginWnd类]########
# 输入: 无 | 输出: 工具类方法###############


###########################文件下的所有函数###########################
"""
WeChatMonitor：微信监控工具类
NotificationManager：通知管理工具类
ProcessManager：进程管理工具类
LogRotator：日志轮转工具类
"""
###########################文件下的所有函数###########################

#########mermaid格式说明所有函数的调用关系说明开始#########
"""
flowchart TD
    A[主程序] --> B[WeChatMonitor类]
    B --> C[check_status检查状态]
    B --> D[auto_login自动登录]
    B --> E[NotificationManager类]
    E --> F[send_notification发送通知]
    B --> G[ProcessManager类]
    G --> H[start_process启动进程]
    G --> I[kill_process终止进程]
    G --> J[is_process_running检查进程]
    B --> K[LogRotator类]
    K --> L[rotate_logs轮转日志]
"""
#########mermaid格式说明所有函数的调用关系说明结束#########

import os
import time
import logging
import subprocess
import psutil
from datetime import datetime, timedelta
from config import MONITOR_CONFIG, LOG_CONFIG, WECHAT_CONFIG, NOTIFICATION_CONFIG

try:
    import wxautox
    from plyer import notification
except ImportError:
    print("请先安装所需库: pip install wxautox plyer psutil")
    exit(1)

class WeChatMonitor:
    """
    WeChatMonitor 功能说明:
    # 微信状态监控和自动登录的核心类
    # 负责检查微信进程状态、登录状态、会话状态，并在需要时执行自动登录
    # 集成了进程管理、通知管理等功能，提供完整的微信监控解决方案
    # 输入: 无 | 输出: 提供状态检查和自动登录方法
    
    属性说明:
    - process_manager: 进程管理器实例，用于检查和管理微信进程
    - notification_manager: 通知管理器实例，用于发送桌面通知
    - retry_count: 当前重试次数计数器，用于控制自动登录重试逻辑
    - wx_instance: wxautox.WeChat实例，用于与微信进行交互
    """
    def __init__(self):
        """
        初始化微信监控器
        创建必要的管理器实例并初始化状态变量
        """
        self.process_manager = ProcessManager()  # 初始化进程管理器
        self.notification_manager = NotificationManager()  # 初始化通知管理器
        self.retry_count = 0  # 重试计数器，用于控制登录重试次数
        self.wx_instance = None  # 微信实例，延迟初始化
        
    def initialize_wechat(self):
        """
        initialize_wechat 功能说明:
        # 初始化wxautox.WeChat实例，建立与微信客户端的连接
        # 这是与微信进行所有交互操作的基础，必须在其他微信操作之前调用
        # 如果微信未启动或连接失败，会抛出异常
        # 输入: 无 | 输出: bool (True=初始化成功, False=初始化失败)
        
        返回值说明:
        - True: 成功创建微信实例，可以进行后续操作
        - False: 初始化失败，通常是微信未启动或权限不足
        """
        try:
            # 创建wxautox.WeChat实例，自动连接到当前运行的微信客户端
            self.wx_instance = wxautox.WeChat()
            logging.debug("微信实例初始化成功")
            return True
        except Exception as e:
            # 记录详细的错误信息，便于问题排查
            logging.error(f"初始化微信实例失败: {str(e)}")
            logging.error("可能原因：1.微信未启动 2.权限不足 3.微信版本不兼容")
            return False
    
    def check_status(self):
        """
        check_status 功能说明:
        # 全面检查微信的运行状态，包括进程状态、登录状态和会话状态
        # 这是监控系统的核心方法，通过多层检查确保微信处于可用状态
        # 输入: 无 | 输出: bool (True=微信完全在线可用, False=微信离线或不可用)
        
        检查流程:
        1. 检查微信进程是否在系统中运行
        2. 如果进程未运行且配置了自动启动，则尝试启动微信
        3. 初始化微信实例（如果尚未初始化）
        4. 检查微信是否已登录（IsOnline状态）
        5. 验证会话列表是否可获取（确认登录状态正常）
        
        返回值说明:
        - True: 微信进程运行中、已登录、会话列表正常，可以正常使用
        - False: 任一检查项失败，微信不可用
        """
        # 第一步：检查微信进程是否在系统中运行
        # 这是最基础的检查，如果进程都没有运行，后续操作都无法进行
        if not self.process_manager.is_process_running(WECHAT_CONFIG['process_name']):
            logging.info(f"微信进程 {WECHAT_CONFIG['process_name']} 未运行")
            
            # 如果配置了自动启动微信，尝试启动微信进程
            # 这个功能可以在微信意外关闭时自动重启
            if WECHAT_CONFIG['auto_start_wechat'] and WECHAT_CONFIG['install_path']:
                logging.info(f"根据配置自动启动微信: {WECHAT_CONFIG['install_path']}")
                self.process_manager.start_process(WECHAT_CONFIG['install_path'])
                time.sleep(5)  # 等待微信启动完成，给足够的启动时间
                logging.info("微信启动等待完成，继续检查状态")
            else:
                logging.info("未配置自动启动微信，请手动启动微信")
            
            return False
        
        # 第二步：初始化微信实例（如果尚未初始化）
        # 只有微信进程运行后，才能建立与微信的连接
        if not self.wx_instance and not self.initialize_wechat():
            logging.warning("微信进程运行中但无法建立连接，可能微信正在启动中")
            return False
        
        try:
            # 第三步：检查微信是否已登录 - 使用IsOnline方法
            # IsOnline()方法检查微信是否处于已登录状态
            # 即使微信启动了，如果用户没有登录，这里也会返回False
            if not self.wx_instance.IsOnline():
                logging.info("微信已启动但用户未登录，需要登录")
                return False
            
            # 第四步：检查微信会话列表是否可获取
            # 这是一个更深层的检查，确保微信不仅登录了，而且功能正常
            # 如果会话列表为空，可能表示登录状态异常或网络问题
            sessions = self.wx_instance.GetSession()
            if not sessions:
                logging.info("微信会话列表获取失败，可能登录状态异常或网络连接问题")
                return False
                
            # 所有检查都通过，微信状态完全正常
            logging.info(f"微信状态正常，已在线，当前有 {len(sessions)} 个会话")
            self.retry_count = 0  # 重置重试计数，因为状态正常
            return True
            
        except Exception as e:
            # 捕获所有可能的异常，记录详细错误信息
            logging.error(f"检查微信状态时发生错误: {str(e)}")
            logging.error("可能原因：1.微信版本不兼容 2.权限不足 3.微信功能异常")
            return False
    
    def auto_login(self):
        """
        auto_login 功能说明:
        # 自动登录微信的核心方法，使用LoginWnd类实现登录流程
        # 包含重试机制、超时控制、用户通知等完整的登录管理功能
        # 输入: 无 | 输出: bool (True=登录成功, False=登录失败或超时)
        
        登录流程:
        1. 检查重试次数是否超过限制
        2. 使用LoginWnd类打开登录窗口
        3. 发送通知提醒用户扫码
        4. 循环检查登录状态直到成功或超时
        5. 根据结果发送相应通知
        
        重试机制:
        - 每次调用都会增加重试计数
        - 超过最大重试次数时暂停登录并通知用户
        - 登录成功后重置重试计数
        
        返回值说明:
        - True: 用户成功扫码登录，微信状态正常
        - False: 登录失败、超时或达到重试上限
        """
        # 第一步：增加重试计数，用于控制登录尝试频率
        # 防止无限重试造成系统资源浪费
        self.retry_count += 1
        logging.info(f"开始第 {self.retry_count} 次自动登录尝试")
        
        # 检查是否超过最大重试次数
        # 这是一个保护机制，避免在用户长时间不在电脑前时持续尝试登录
        if self.retry_count > MONITOR_CONFIG['max_retry_count']:
            logging.warning(f"已达到最大重试次数 {MONITOR_CONFIG['max_retry_count']}，暂停自动登录")
            # 发送桌面通知，提醒用户需要手动处理
            self.notification_manager.send_notification(
                "微信自动登录失败", 
                f"已尝试 {MONITOR_CONFIG['max_retry_count']} 次登录，请手动检查微信状态"
            )
            # 等待更长时间再重置，给用户足够的处理时间
            self.retry_count = 0  # 重置重试计数，允许后续重新尝试
            return False
        
        try:
            logging.info("开始执行自动登录流程...")
            
            # 第二步：使用wxautox的LoginWnd类进行登录
            # LoginWnd是专门用于处理微信登录的类，支持二维码登录
            from wxautox import LoginWnd
            
            # 创建登录窗口实例
            # 这个实例将负责打开微信登录界面并处理登录流程
            login_wnd = LoginWnd()
            
            # 第三步：调用登录方法，打开登录窗口
            # timeout参数控制登录窗口的超时时间
            login_result = login_wnd.login(timeout=MONITOR_CONFIG['login_timeout'])
            
            # 检查登录窗口是否成功打开
            if login_result and hasattr(login_result, 'success') and login_result.success:
                logging.info("微信登录窗口已成功打开，等待用户扫码登录...")
                # 发送桌面通知，提醒用户需要扫码
                self.notification_manager.send_notification(
                    "微信需要登录", 
                    "请扫描二维码完成微信登录"
                )
                
                # 第四步：等待用户完成登录操作
                # 使用轮询方式检查登录状态，避免阻塞程序
                wait_time = 0
                max_wait = MONITOR_CONFIG['login_timeout']
                check_interval = 2  # 每2秒检查一次登录状态
                
                logging.info(f"开始等待登录完成，最大等待时间: {max_wait}秒")
                while wait_time < max_wait:
                    time.sleep(check_interval)
                    wait_time += check_interval
                    
                    # 重新初始化微信实例并检查登录状态
                    # 需要重新初始化是因为登录状态可能已经改变
                    if self.initialize_wechat() and self.wx_instance.IsOnline():
                        logging.info("🎉 微信登录成功！用户已完成扫码登录")
                        # 发送成功通知
                        self.notification_manager.send_notification(
                            "微信登录成功", 
                            "微信已成功登录，监控程序继续运行"
                        )
                        self.retry_count = 0  # 登录成功，重置重试计数
                        return True
                        
                    # 显示等待进度，让用户了解当前状态
                    logging.info(f"等待用户扫码登录中... ({wait_time}/{max_wait}秒)")
                
                # 超时处理：用户在规定时间内未完成登录
                logging.warning(f"登录等待超时({max_wait}秒)，请检查是否已完成扫码")
                self.notification_manager.send_notification(
                    "微信登录超时", 
                    "登录等待超时，请重新尝试扫码登录"
                )
                return False
            else:
                # 登录窗口打开失败
                logging.error("无法打开微信登录窗口，可能是微信版本不兼容或权限不足")
                return False
                
        except Exception as e:
            # 捕获登录过程中的所有异常
            logging.error(f"自动登录微信时发生错误: {str(e)}")
            logging.error("可能原因：1.微信版本不兼容 2.系统权限不足 3.网络连接问题")
            return False

class NotificationManager:
    """
    NotificationManager 功能说明:
    # 桌面通知管理器，负责向用户发送系统通知
    # 主要用于微信状态变化时的用户提醒（如需要登录、登录成功等）
    # 支持Windows系统的桌面通知功能
    # 输入: 无 | 输出: 无
    """
    
    def send_notification(self, title, message):
        """
        send_notification 功能说明:
        # 发送桌面通知给用户，提醒重要的微信状态变化
        # 通知会显示在系统托盘区域，用户可以看到标题和详细消息
        # 只有在配置文件中启用通知功能时才会实际发送
        # 输入: title (通知标题，简短描述), message (通知内容，详细信息) | 输出: 无
        # 异常处理: 如果通知发送失败，会记录错误日志但不影响主程序运行
        """
        # 检查是否启用了桌面通知功能
        # 这个配置项允许用户选择是否接收桌面通知
        if NOTIFICATION_CONFIG['enable_desktop_notification']:
            try:
                # 使用plyer库发送跨平台桌面通知
                notification.notify(
                    title=title,              # 通知标题，显示在通知顶部
                    message=message,          # 通知内容，显示详细信息
                    app_name="微信自动登录监控",  # 应用名称，标识通知来源
                    timeout=10                # 通知显示时间（秒），10秒后自动消失
                )
                # 记录通知发送成功的日志
                logging.info(f"✅ 桌面通知已发送: {title} - {message}")
            except Exception as e:
                # 通知发送失败时的错误处理
                # 常见失败原因：系统权限不足、通知服务未启动等
                logging.error(f"❌ 桌面通知发送失败: {str(e)}")
                logging.error("可能原因：1.系统通知服务未启动 2.应用权限不足 3.plyer库未正确安装")
        else:
            # 通知功能被禁用时的日志记录
            logging.debug(f"通知功能已禁用，跳过发送: {title} - {message}")

class ProcessManager:
    """
    ProcessManager 功能说明:
    # 系统进程管理器，负责监控和控制系统进程
    # 主要用于检查微信进程状态、启动微信程序、终止异常进程等
    # 使用psutil库实现跨平台的进程管理功能
    # 输入: 无 | 输出: 无
    """
    
    def is_process_running(self, process_name):
        """
        is_process_running 功能说明:
        # 检查指定名称的进程是否正在系统中运行
        # 通过遍历系统所有进程，匹配进程名称（不区分大小写）
        # 主要用于检查微信进程(WeChat.exe)是否已启动
        # 输入: process_name (进程名称，如'WeChat.exe') | 输出: bool (True=进程运行中, False=进程未运行)
        # 异常处理: 忽略进程访问权限错误和僵尸进程
        """
        # 遍历系统中所有正在运行的进程
        # psutil.process_iter(['name'])只获取进程名称信息，提高性能
        for proc in psutil.process_iter(['name']):
            try:
                # 进程名称比较（不区分大小写）
                # 例如：'wechat.exe' 和 'WeChat.exe' 都会匹配成功
                if proc.info['name'].lower() == process_name.lower():
                    logging.debug(f"✅ 找到运行中的进程: {process_name}")
                    return True
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                # 处理进程访问异常：
                # NoSuchProcess: 进程在检查过程中已结束
                # AccessDenied: 没有权限访问该进程信息
                # ZombieProcess: 僵尸进程（已结束但未被清理）
                continue
        
        # 未找到匹配的进程
        logging.debug(f"❌ 未找到运行中的进程: {process_name}")
        return False
    
    def start_process(self, process_path):
        """
        start_process 功能说明:
        # 启动指定路径的可执行程序
        # 主要用于自动启动微信程序，当检测到微信未运行时调用
        # 使用subprocess.Popen以非阻塞方式启动进程
        # 输入: process_path (可执行文件的完整路径，如'C:\\Program Files\\Tencent\\WeChat\\WeChat.exe') | 输出: bool (True=启动成功, False=启动失败)
        # 异常处理: 文件不存在、权限不足、路径错误等情况
        """
        try:
            # 第一步：验证可执行文件是否存在
            # 避免尝试启动不存在的程序导致错误
            if os.path.exists(process_path):
                # 第二步：使用subprocess.Popen启动进程
                # Popen是非阻塞的，不会等待程序启动完成就返回
                # 这样可以避免程序被阻塞，继续执行后续逻辑
                subprocess.Popen(process_path)
                logging.info(f"🚀 进程启动成功: {process_path}")
                logging.info("程序已在后台启动，请等待几秒钟完成初始化")
                return True
            else:
                # 文件路径不存在的错误处理
                logging.error(f"❌ 可执行文件不存在: {process_path}")
                logging.error("请检查微信安装路径是否正确，或重新安装微信")
                return False
        except Exception as e:
            # 启动进程时的异常处理
            # 常见错误：权限不足、文件损坏、系统资源不足等
            logging.error(f"❌ 启动进程时发生错误: {str(e)}")
            logging.error("可能原因：1.权限不足 2.文件损坏 3.系统资源不足 4.路径包含特殊字符")
            return False
    
    def kill_process(self, process_name):
        """
        kill_process 功能说明:
        # 强制终止指定名称的进程
        # 主要用于处理微信程序异常或需要重启微信的情况
        # 使用psutil.terminate()优雅地终止进程，避免数据丢失
        # 输入: process_name (进程名称，如'WeChat.exe') | 输出: bool (True=终止成功, False=终止失败或进程不存在)
        # 异常处理: 进程访问权限错误、进程已结束等情况
        """
        try:
            # 遍历系统中所有进程，查找匹配的进程名
            killed_count = 0  # 记录成功终止的进程数量
            
            for proc in psutil.process_iter(['name']):
                try:
                    # 进程名称匹配（不区分大小写）
                    if proc.info['name'].lower() == process_name.lower():
                        # 使用terminate()优雅地终止进程
                        proc.terminate()
                        killed_count += 1
                        logging.info(f"🔄 已终止进程: {process_name} (PID: {proc.pid})")
                        
                        # 等待进程完全结束
                        try:
                            proc.wait(timeout=5)  # 等待最多5秒
                            logging.info(f"✅ 进程 {process_name} 已完全结束")
                        except psutil.TimeoutExpired:
                            # 如果进程5秒内没有结束，强制杀死
                            logging.warning(f"⚠️ 进程 {process_name} 未在5秒内结束，强制终止")
                            proc.kill()
                        
                        return True
                        
                except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                    # 处理进程访问异常：
                    # NoSuchProcess: 进程在终止过程中已结束
                    # AccessDenied: 没有权限终止该进程（如系统进程）
                    # ZombieProcess: 僵尸进程（已结束但未被清理）
                    continue
            
            # 未找到匹配的进程
            if killed_count == 0:
                logging.warning(f"⚠️ 未找到需要终止的进程: {process_name}")
                logging.info("进程可能已经结束或进程名称不正确")
                return False
            else:
                logging.info(f"✅ 成功终止 {killed_count} 个 {process_name} 进程")
                return True
                
        except Exception as e:
            # 终止进程时的异常处理
            logging.error(f"❌ 终止进程时发生错误: {str(e)}")
            logging.error("可能原因：1.权限不足 2.系统保护进程 3.进程正在被其他程序使用")
            return False

class LogRotator:
    """
    LogRotator 功能说明:
    # 日志文件轮转管理器，负责自动清理过期的日志文件
    # 防止日志文件无限增长占用过多磁盘空间
    # 根据配置的保留天数自动删除过期日志
    # 输入: log_dir (日志目录路径) | 输出: 无
    """
    
    def __init__(self, log_dir='logs'):
        """
        __init__ 功能说明:
        # 初始化日志轮转器，设置日志目录路径
        # 输入: log_dir (日志文件存储目录，默认为'logs') | 输出: 无
        """
        # 设置日志文件存储目录
        # 如果目录不存在，rotate_logs方法会自动处理
        self.log_dir = log_dir
        logging.debug(f"日志轮转器已初始化，日志目录: {self.log_dir}")
        
    def rotate_logs(self):
        """
        rotate_logs 功能说明:
        # 执行日志文件轮转，删除超过保留期限的日志文件
        # 根据LOG_CONFIG中的log_retention_days配置确定保留天数
        # 通过文件修改时间判断是否过期，过期文件将被自动删除
        # 输入: 无 | 输出: bool (True=轮转成功, False=轮转失败)
        # 异常处理: 目录不存在、文件访问权限、磁盘空间等问题
        """
        try:
            # 第一步：检查日志目录是否存在
            if not os.path.exists(self.log_dir):
                logging.debug(f"日志目录不存在，跳过轮转: {self.log_dir}")
                return True
                
            # 第二步：计算过期日期
            # 从配置文件获取日志保留天数
            retention_days = LOG_CONFIG['log_retention_days']
            expire_date = datetime.now() - timedelta(days=retention_days)
            
            logging.info(f"开始日志轮转，保留最近 {retention_days} 天的日志")
            logging.info(f"过期日期: {expire_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            # 第三步：遍历日志目录中的所有文件
            deleted_count = 0  # 记录删除的文件数量
            total_size_freed = 0  # 记录释放的磁盘空间
            
            for filename in os.listdir(self.log_dir):
                file_path = os.path.join(self.log_dir, filename)
                
                # 只处理文件，跳过子目录
                if os.path.isfile(file_path):
                    # 获取文件的最后修改时间
                    file_time = datetime.fromtimestamp(os.path.getmtime(file_path))
                    
                    # 第四步：检查文件是否过期
                    if file_time < expire_date:
                        # 记录文件大小（用于统计释放的空间）
                        try:
                            file_size = os.path.getsize(file_path)
                            total_size_freed += file_size
                        except OSError:
                            file_size = 0
                        
                        # 删除过期的日志文件
                        os.remove(file_path)
                        deleted_count += 1
                        
                        logging.info(f"🗑️ 已删除过期日志: {filename} (修改时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
                    else:
                        logging.debug(f"保留日志文件: {filename} (修改时间: {file_time.strftime('%Y-%m-%d %H:%M:%S')})")
            
            # 第五步：输出轮转结果统计
            if deleted_count > 0:
                size_mb = total_size_freed / (1024 * 1024)  # 转换为MB
                logging.info(f"✅ 日志轮转完成：删除了 {deleted_count} 个过期文件，释放空间 {size_mb:.2f} MB")
            else:
                logging.info("✅ 日志轮转完成：没有发现过期的日志文件")
            
            return True
            
        except Exception as e:
            # 日志轮转过程中的异常处理
            logging.error(f"❌ 日志轮转失败: {str(e)}")
            logging.error("可能原因：1.磁盘空间不足 2.文件被占用 3.权限不足 4.目录访问错误")
            return False

# 便捷函数：设置日志系统
def setup_logging():
    """
    setup_logging 功能说明:
    # 设置基础日志系统，创建日志目录和配置日志格式
    # 这是一个便捷函数，为整个监控系统提供统一的日志配置
    # 输入: 无 | 输出: 无
    # 功能: 创建logs目录、配置日志格式、设置日志级别
    """
    # 创建日志目录
    os.makedirs('logs', exist_ok=True)
    
    # 配置日志格式
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler('logs/wechat_monitor.log', encoding='utf-8'),
            logging.StreamHandler()
        ]
    )
    
    logging.info("日志系统初始化完成")