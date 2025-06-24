##########wechat_auto_login.py: [微信自动登录监控程序] ##################
# 变更记录: [2025-06-24] @李祥光 [创建微信自动登录监控程序]########
# 变更记录: [2025-06-24] @李祥光 [修复API调用错误：使用IsOnline和LoginWnd类]########
# 变更记录: [2025-06-24] @李祥光 [添加详细注释和错误处理机制]########
# 输入: 无命令行参数 | 输出: 持续监控日志和状态信息###############


###########################文件下的所有函数###########################
"""
setup_logging：配置日志系统，创建日志目录和文件输出
check_wechat_status：检查微信客户端在线状态和连接情况
auto_login_wechat：自动触发微信登录流程，打开登录窗口供用户扫码
monitor_wechat：微信状态监控主循环，7x24小时不间断监控
main：程序主入口函数，负责初始化和启动监控服务
"""
###########################文件下的所有函数###########################

#########mermaid格式说明所有函数的调用关系说明开始#########
"""
flowchart TD
    A[程序启动] --> B[main函数]
    B --> C[显示程序信息]
    C --> D[setup_logging函数]
    D --> E[初始化日志系统]
    E --> F[monitor_wechat函数]
    F --> G[开始监控循环]
    G --> H[check_wechat_status函数]
    H --> I{微信状态检查}
    I -->|在线正常| J[继续监控]
    I -->|离线异常| K[auto_login_wechat函数]
    K --> L[打开登录窗口]
    L --> M[等待用户扫码]
    M --> N{登录结果}
    N -->|成功| J
    N -->|失败| O[记录错误]
    J --> P[等待检查间隔]
    O --> P
    P --> G
    G --> Q{用户中断?}
    Q -->|是| R[优雅退出]
    Q -->|否| G
"""
#########mermaid格式说明所有函数的调用关系说明结束#########

import time
import logging
import os
from datetime import datetime
try:
    import wxautox
except ImportError:
    print("请先安装wxautox库: pip install wxautox")
    exit(1)

def setup_logging():
    """
    setup_logging 功能说明:
    # 初始化日志系统，配置日志输出格式和存储位置
    # 创建日志目录，设置双重输出（文件+控制台）
    # 按日期自动生成日志文件名，便于日志管理和查看
    # 输入: 无 | 输出: 无
    # 异常处理: 目录创建失败、文件权限不足等情况
    """
    try:
        # 第一步：确保日志存储目录存在
        # 如果logs目录不存在，自动创建
        logs_dir = 'logs'
        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir)
            print(f"✅ 已创建日志目录: {logs_dir}")
        
        # 第二步：配置日志输出格式
        # 包含时间戳、日志级别、具体消息内容
        log_format = '%(asctime)s - %(levelname)s - %(message)s'
        
        # 第三步：生成按日期命名的日志文件
        # 格式：wechat_monitor_YYYYMMDD.log
        current_date = datetime.now().strftime("%Y%m%d")
        log_filename = f'{logs_dir}/wechat_monitor_{current_date}.log'
        
        # 第四步：配置日志系统
        # 同时输出到文件和控制台，方便实时查看和历史追踪
        logging.basicConfig(
            level=logging.INFO,           # 设置日志级别为INFO
            format=log_format,            # 应用日志格式
            handlers=[
                # 文件处理器：保存到日志文件，使用UTF-8编码支持中文
                logging.FileHandler(log_filename, encoding='utf-8'),
                # 控制台处理器：实时显示在终端
                logging.StreamHandler()
            ]
        )
        
        logging.info(f"📝 日志系统初始化完成，日志文件: {log_filename}")
        
    except Exception as e:
        # 日志系统初始化失败的处理
        print(f"❌ 日志系统初始化失败: {str(e)}")
        print("程序将继续运行，但可能无法记录日志")
        # 设置基本的控制台日志
        logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

def check_wechat_status():
    """
    check_wechat_status 功能说明:
    # 检查微信客户端的在线状态和连接情况
    # 通过wxautox库连接微信实例，验证登录状态和会话可用性
    # 这是监控系统的核心检查函数，用于判断是否需要自动登录
    # 输入: 无 | 输出: bool (True=微信在线且正常, False=微信离线或异常)
    # 异常处理: 微信未启动、连接失败、权限不足等情况
    """
    try:
        # 第一步：创建微信实例连接
        # wxautox.WeChat()会尝试连接到当前运行的微信客户端
        logging.debug("正在连接微信客户端...")
        wx = wxautox.WeChat()
        
        # 第二步：检查微信登录状态
        # IsOnline()方法检查微信是否已成功登录
        # 这是修复后的正确API调用方式
        if not wx.IsOnline():
            logging.info("❌ 微信未登录或连接失败")
            logging.info("可能原因：1.微信未启动 2.未扫码登录 3.网络连接问题")
            return False
        
        # 第三步：验证微信会话功能
        # 尝试获取会话列表，确保微信功能正常
        try:
            sessions = wx.GetSession()
            if sessions is not None:
                logging.debug(f"微信会话检查通过，当前会话数: {len(sessions) if hasattr(sessions, '__len__') else '未知'}")
            else:
                logging.warning("⚠️ 微信会话列表为空，可能刚刚登录")
        except Exception as session_error:
            logging.warning(f"⚠️ 获取微信会话时出现问题: {str(session_error)}")
            # 会话获取失败不一定意味着微信离线，继续检查
        
        # 微信状态检查通过
        logging.info("✅ 微信状态正常，已在线且功能正常")
        return True
        
    except Exception as e:
        # 异常处理：捕获所有可能的错误情况
        # 常见错误原因：
        # 1. 微信进程未启动 - wxautox无法连接
        # 2. 微信版本不兼容 - API调用失败
        # 3. 权限不足 - 无法访问微信进程
        # 4. 系统资源不足 - 连接超时
        logging.error(f"❌ 检查微信状态时发生错误: {str(e)}")
        logging.error("建议检查：1.微信是否正常启动 2.wxautox版本兼容性 3.管理员权限")
        return False

def auto_login_wechat():
    """
    auto_login_wechat 功能说明:
    # 自动触发微信登录流程，打开登录窗口供用户扫码
    # 使用wxautox的LoginWnd类实现自动化登录操作
    # 包含登录超时控制、状态轮询检查、错误重试机制
    # 输入: 无 | 输出: bool (True=登录成功, False=登录失败或超时)
    # 依赖: wxautox库的LoginWnd类和WeChat类
    # 注意: 需要用户手动扫码确认登录
    """
    try:
        logging.info("🚀 开始自动登录微信流程...")
        
        # 第一步：导入并初始化登录窗口类
        # LoginWnd是wxautox提供的专门用于微信登录的类
        from wxautox import LoginWnd
        logging.debug("LoginWnd类导入成功")
        
        # 第二步：创建登录窗口实例
        # 这个实例将负责打开微信登录界面
        login_wnd = LoginWnd()
        logging.debug("登录窗口实例创建完成")
        
        # 第三步：调用登录方法打开登录窗口
        # timeout=60: 设置登录窗口打开的超时时间为60秒
        # 这个操作会显示二维码供用户扫描
        logging.info("正在打开微信登录窗口...")
        login_result = login_wnd.login(timeout=60)
        
        # 第四步：检查登录窗口是否成功打开
        # login_result包含登录操作的结果信息
        # 需要验证结果对象存在且success属性为True
        if login_result and hasattr(login_result, 'success') and login_result.success:
            logging.info("✅ 微信登录窗口已成功打开")
            logging.info("📱 请使用手机微信扫描二维码完成登录...")
            
            # 第五步：轮询检查登录状态
            # 设置等待参数：每2秒检查一次，最多等待60秒
            wait_time = 0  # 已等待时间计数器
            max_wait = 60  # 最大等待时间（秒）
            check_interval = 2  # 检查间隔（秒）
            
            logging.info(f"开始轮询检查登录状态，最大等待时间: {max_wait}秒")
            
            # 轮询循环：持续检查直到登录成功或超时
            while wait_time < max_wait:
                time.sleep(check_interval)  # 等待检查间隔
                wait_time += check_interval  # 更新等待时间计数
                
                # 第六步：验证登录状态
                # 重新创建微信实例来检查最新的登录状态
                # 这是必要的，因为登录状态可能在扫码后发生变化
                try:
                    wx = wxautox.WeChat()  # 创建新的微信实例
                    if wx.IsOnline():  # 检查是否已成功登录
                        logging.info("🎉 微信登录成功！用户已完成扫码验证")
                        return True
                except Exception as check_error:
                    # 状态检查失败不一定意味着登录失败，继续等待
                    logging.debug(f"状态检查时出现异常: {str(check_error)}")
                    pass
                    
                # 显示等待进度信息
                logging.info(f"⏳ 等待用户扫码登录... ({wait_time}/{max_wait}秒)")
            
            # 第七步：登录超时处理
            logging.warning("⏰ 登录等待超时！")
            logging.warning("可能原因：1.用户未及时扫码 2.网络连接问题 3.二维码已过期")
            logging.info("建议：请重新尝试登录操作")
            return False
        else:
            # 第八步：登录窗口打开失败处理
            logging.error("❌ 无法打开微信登录窗口")
            logging.error("可能原因：1.微信客户端异常 2.系统权限不足 3.wxautox版本问题")
            return False
            
    except Exception as e:
        # 第九步：异常处理和错误分析
        # 捕获登录过程中的所有异常情况
        # 常见异常类型：
        # 1. ImportError: wxautox库导入失败或版本不兼容
        # 2. AttributeError: LoginWnd类方法调用错误
        # 3. TimeoutError: 登录窗口打开超时
        # 4. ConnectionError: 与微信客户端连接失败
        # 5. PermissionError: 系统权限不足
        logging.error(f"❌ 自动登录微信时发生错误: {str(e)}")
        logging.error("错误分析建议：")
        logging.error("1. 检查wxautox库是否正确安装和版本兼容")
        logging.error("2. 确认微信客户端是否正常运行")
        logging.error("3. 验证程序是否具有足够的系统权限")
        logging.error("4. 检查防火墙或安全软件是否阻止了操作")
        return False

def monitor_wechat(check_interval=30):
    """
    monitor_wechat 功能说明:
    # 微信状态监控的主循环函数，实现7x24小时不间断监控
    # 核心功能：定期检查微信在线状态，自动处理掉线情况
    # 监控策略：状态检查 -> 异常检测 -> 自动登录 -> 状态恢复
    # 适用场景：需要保持微信长期在线的自动化应用
    # 输入: check_interval (状态检查间隔，单位秒，默认30秒)
    # 输出: 无返回值（持续运行直到手动停止）
    # 异常处理: 包含完整的错误恢复机制
    """
    logging.info("🔄 启动微信状态监控服务")
    logging.info(f"📊 监控配置 - 检查间隔: {check_interval}秒")
    logging.info("💡 监控策略: 状态检查 -> 异常检测 -> 自动登录 -> 状态恢复")
    
    # 监控统计变量
    check_count = 0  # 检查次数计数器
    login_attempts = 0  # 登录尝试次数
    
    # 主监控循环：无限循环直到程序被手动停止
    while True:
        try:
            check_count += 1  # 增加检查计数
            logging.info(f"🔍 第 {check_count} 次状态检查开始...")
            
            # 第一步：执行微信状态检查
            # 调用check_wechat_status()检查微信是否在线
            if not check_wechat_status():
                # 检测到微信离线，开始自动恢复流程
                login_attempts += 1
                logging.warning(f"⚠️ 检测到微信离线！开始第 {login_attempts} 次自动登录尝试...")
                
                # 第二步：执行自动登录操作
                # 调用auto_login_wechat()尝试恢复微信登录状态
                if auto_login_wechat():
                    logging.info("✅ 微信自动登录成功！状态已恢复，继续监控")
                    logging.info(f"📈 本次监控统计 - 总检查: {check_count}次, 登录尝试: {login_attempts}次")
                else:
                    logging.error("❌ 微信自动登录失败")
                    logging.error(f"🔄 将在 {check_interval} 秒后重新尝试")
                    logging.warning("建议检查：1.网络连接 2.微信客户端状态 3.系统权限")
            else:
                # 微信状态正常，记录正常状态
                logging.info(f"✅ 微信状态正常 (第 {check_count} 次检查)")
            
            # 第三步：等待下次检查
            # 使用sleep暂停指定时间，避免过于频繁的检查
            logging.info(f"⏱️ 等待 {check_interval} 秒后进行下次状态检查...")
            time.sleep(check_interval)
            
        except KeyboardInterrupt:
            # 第四步：优雅处理用户中断
            # 捕获Ctrl+C信号，实现程序的优雅退出
            # 这是正常的程序终止方式，不记录为错误
            logging.info("🛑 收到用户中断信号 (Ctrl+C)，正在优雅停止监控服务...")
            logging.info(f"📊 监控统计总结 - 总检查次数: {check_count}, 登录尝试次数: {login_attempts}")
            logging.info("👋 微信监控服务已安全停止")
            break  # 跳出while循环，结束监控
        except Exception as e:
            # 第五步：处理监控过程中的意外异常
            # 捕获所有其他未预期的异常，确保监控服务的稳定性
            # 常见异常：系统资源不足、网络中断、权限变更等
            logging.error(f"❌ 监控过程中发生未知错误: {str(e)}")
            logging.error("错误类型分析：")
            logging.error("1. 系统资源不足 - 内存或CPU占用过高")
            logging.error("2. 网络连接异常 - 网络中断或代理问题")
            logging.error("3. 权限变更 - 系统权限被修改")
            logging.error("4. 微信客户端崩溃 - 微信程序异常退出")
            logging.info(f"🔄 监控服务将在 {check_interval} 秒后自动重试...")
            time.sleep(check_interval)  # 等待后继续监控循环

def main():
    """
    main 功能说明:
    # 程序主入口函数，负责整个应用的初始化和启动流程
    # 核心职责：环境初始化、日志配置、监控服务启动、异常处理
    # 执行流程：显示程序信息 -> 初始化日志 -> 启动监控 -> 异常处理 -> 清理退出
    # 适用场景：作为独立应用程序运行或被其他模块调用
    # 输入: 无参数 | 输出: 无返回值
    # 异常处理: 包含完整的启动和运行时异常处理机制
    """
    # 第一步：显示程序启动信息
    # 向用户展示程序的基本信息和功能说明
    print("="*50)
    print("🤖 微信自动登录保持在线监控程序")
    print("👨‍💻 作者: 李祥光")
    print("📅 创建时间: 2025-06-24")
    print("🎯 功能: 7x24小时监控微信状态，自动登录保持在线")
    print("🔧 技术栈: Python + wxautox + 自动化监控")
    print("📖 使用说明: 程序将持续运行，按Ctrl+C安全退出")
    print("="*50)
    
    # 第二步：初始化日志系统
    # 配置日志输出格式、文件存储和控制台显示
    print("📝 正在初始化日志系统...")
    setup_logging()
    logging.info("🚀 微信自动登录监控程序启动")
    logging.info("📋 程序配置信息:")
    logging.info("   - 监控间隔: 30秒")
    logging.info("   - 日志级别: INFO")
    logging.info("   - 自动登录: 启用")
    logging.info("   - 异常恢复: 启用")
    
    try:
        # 第三步：启动核心监控服务
        # 调用monitor_wechat函数开始微信状态监控
        logging.info("🎬 开始启动微信监控服务...")
        monitor_wechat(check_interval=30)  # 30秒检查间隔
        
    except Exception as e:
        # 第四步：处理程序运行时的致命错误
        # 捕获监控服务启动或运行过程中的严重异常
        logging.error(f"💥 程序运行时发生致命错误: {str(e)}")
        logging.error("错误分析：")
        logging.error("1. 检查wxautox库是否正确安装")
        logging.error("2. 确认微信客户端是否可正常启动")
        logging.error("3. 验证系统权限是否充足")
        logging.error("4. 检查Python环境和依赖库")
        print(f"❌ 程序运行失败: {str(e)}")
        print("请查看日志文件获取详细错误信息")
        
    finally:
        # 第五步：程序清理和退出处理
        # 无论程序如何结束，都执行清理操作
        logging.info("🏁 微信监控程序正在安全退出...")
        logging.info("📊 程序运行总结已记录到日志文件")
        logging.info("👋 程序已完全停止，感谢使用！")
        print("\n" + "="*50)
        print("📋 程序已安全退出")
        print("📁 详细日志请查看 logs/ 目录")
        print("🔄 如需重新启动，请重新运行程序")
        print("="*50)

if __name__ == "__main__":
    main()