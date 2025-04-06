from loguru import logger
from API.api_iirose import APIIirose  # 导入接口
from globals.globals import GlobalVal  # 全局变量
from API.api_get_config import get_master_id  # 获取主人的唯一标识
from API.decorator.command import on_command, MessageType  # 注册指令装饰器和消息类型Enum
import datetime  # 导入datetime模块
import os  # 导入os模块，用于文件路径操作
import asyncio  # 导入asyncio用于异步任务管理

API = APIIirose()  # 实例化 APIIirose

# 假设有一个全局字典记录用户的聊天次数
chat_count = {}

async def load_chat_count():
    """从文本文件加载聊天次数的函数"""
    global chat_count
    file_name = os.path.join("exports", "chat_counts.txt")  # 指定加载路径

    if os.path.exists(file_name):
        with open(file_name, 'r', encoding='utf-8') as file:
            for line in file:
                user_id, date, count = line.strip().split(';')  # 使用分号分割每行
                if user_id not in chat_count:
                    chat_count[user_id] = {}
                chat_count[user_id][date] = int(count)  # 将聊天次数转为整数

        logger.info("成功加载聊天记录")
async def update_chat_count(user_id):
    """更新用户聊天次数的函数"""
    global chat_count
    today = str(datetime.date.today())  # 获取今天的日期
    if user_id not in chat_count:
        chat_count[user_id] = {}
    if today not in chat_count[user_id]:
        chat_count[user_id][today] = 0
    chat_count[user_id][today] += 1  # 增加聊天次数
    await export_to_txt()  # 每次更新后导出到文本文件

async def export_to_txt():
    """将聊天次数导出到文本文件的函数"""
    export_dir = "exports"
    os.makedirs(export_dir, exist_ok=True)

    file_name = os.path.join(export_dir, "chat_counts.txt")  # 指定保存路径
    with open(file_name, 'w', encoding='utf-8') as file:
        for user_id, dates in chat_count.items():
            for date, count in dates.items():
                file.write(f"{user_id};{date};{count}\n")  # 使用分号作为分隔符

@on_command('/cu', False, command_type=[MessageType.room_chat, MessageType.private_chat])  # 注册/cu指令
async def check_chat_count(Message):
    """处理/cu指令的函数，返回用户当天的聊天次数"""
    user_id = Message.user_id  # 获取用户ID
    user_name = Message.user_name  # 获取用户名
    today = str(datetime.date.today())

    count = chat_count.get(user_id, {}).get(today, 0)  # 查找用户当天的聊天次数
    response_msg = f" [*{user_name}*] 您今日的发言为 {count} 句 "  # 艾特用户

    await API.send_msg(Message, response_msg)  # 返回聊天次数给用户

async def room_message(Message):
    """接收到房间消息时触发的函数，更新聊天次数"""
    # 更新用户的聊天次数
    await update_chat_count(Message.user_id)  # 每次接收到消息时更新聊天次数

async def reset_chat_count():
    """重置聊天次数的函数"""
    global chat_count
    chat_count.clear()  # 清空聊天次数
    await export_to_txt()  # 导出到文本文件

async def schedule_reset():
    """定期重置聊天次数的任务"""
    while True:
        # 获取当前时间并判断是否为午夜
        now = datetime.datetime.now()
        if now.hour == 0 and now.minute == 0:  # 每天0点重置
            await reset_chat_count()  # 执行重置
            await asyncio.sleep(60)  # 等待60秒以避免重复执行
        await asyncio.sleep(30)  # 每30秒检查一次时间

async def on_init():
    """初始化时执行的函数"""
    logger.info('框架会在登陆成功后执行这个函数，只会执行一次')  # 框架使用logger日志管理器
    await load_chat_count()  # 加载聊天次数记录
    asyncio.create_task(schedule_reset())  # 启动定时重置任务
