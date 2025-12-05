# 检查github actions是否成功
import asyncio
import json
import logging
import os
import random
import time
from uuid import uuid4

import git
import httpx
from dotenv import load_dotenv
from redis.asyncio import ConnectionPool, Redis

load_dotenv()
REDISPASSWORD = os.environ.get('REDISPASSWORD', '')
REDISURL = os.environ.get('REDISURL', '')


# 配置日志记录
# 添加时间格式
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# 禁用 httpx 日志器
httpx_logger = logging.getLogger('httpx')
httpx_logger.addHandler(logging.NullHandler())
httpx_logger.propagate = False  # 阻止日志向上传播

# 禁用 httpcore 日志器（若有）
httpcore_logger = logging.getLogger('httpcore')
httpcore_logger.addHandler(logging.NullHandler())
httpcore_logger.propagate = False

GITHUB_TOKEN = os.environ.get('GITHUB_TOKEN', '')
REPO_LIST = [repo.split('|') for repo in os.environ.get('REPO_LIST', '').split(',')]


async def get_key_len(rk):
    pool = ConnectionPool.from_url(REDISURL)
    r: Redis = await Redis(connection_pool=pool, password=REDISPASSWORD)
    return await r.llen(rk)


def main():
    worker_tasks_nums = 50
    rk = 'insurance:tasks:company_tasks_action'
    length = asyncio.run(get_key_len(rk))
    logger.info(f'队列{rk}长度为{length}')
    logger.info('检查github actions')
    if length == 0:
        logger.info('队列为空, 退出')
        return
    tasks_per_worker = length // worker_tasks_nums
    logger.info(f'需要worker数量 {tasks_per_worker}')
    nochange = 0
    for name, repo in REPO_LIST:
        if tasks_per_worker == 0:
            break
        url = f'https://api.github.com/repos/{repo}/actions/runs?per_page=1"'
        headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        res = httpx.get(url, headers=headers)
        data = json.loads(res.text)
        # 避免Rate Limit
        time.sleep(1)
        try:
            logger.info(f'仓库 {repo} 最新Actions状态: {data["workflow_runs"][0]["status"]}')
            if data['workflow_runs']:
                run = data['workflow_runs'][0]
                if run['status'] == 'completed':
                    # 重新触发Actions
                    logger.info(f'仓库 {repo} Actions状态为完成, 重新触发Actions')
                    # 生产冷却时间 1min - 3min
                    rd_time = random.randint(60, 180)
                    logger.info(f'仓库 {repo} 冷却时间 {rd_time} 秒')
                    time.sleep(rd_time)
                    if nochange == 0:
                        # 修改1.txt
                        uid = str(uuid4()).upper()
                        with open('1.txt', 'w') as f:
                            f.write(uid)
                        git.Repo('.').index.add('1.txt')
                        git.Repo('.').index.commit(uid)
                        logger.info(f'仓库 {repo} 提交 {uid}')
                        nochange = 1
                    # 推送
                    git.Repo('.').remote(name).push(force=True)
                    tasks_per_worker -= 1
                    logger.info(f'仓库 {repo} Actions重新触发成功, 剩余wroker数 {tasks_per_worker}')
        except Exception as e:
            logger.error(f'仓库 {repo} 检查Actions状态时出错: {e}')
            continue
    logger.info('检查完成')


if __name__ == '__main__':
    main()
