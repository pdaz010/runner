# 检查github actions是否成功
import json
import logging
import os

import git
import httpx
from dotenv import load_dotenv

load_dotenv()
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
REPO_LIST = (
    ('origin', 'panda-zxs/runner'),
    ('pdaz001', 'pdaz001/runner'),
    ('pdaz002', 'pdaz002/runner'),
    ('pdaz003', 'pdaz003/runner'),
    ('pdaz004', 'pdaz004/runner'),
    ('pdaz005', 'pdaz005/runner'),
    ('pdaz006', 'pdaz006/runner'),
    ('pdaz007', 'pdaz007/runner'),
    ('pdaz008', 'pdaz008/runner'),
    ('pdaz009', 'pdaz009/runner'),
    ('pdaz010', 'pdaz010/runner'),
)


def main():
    logger.info('检查github actions')
    for name, repo in REPO_LIST:
        url = f'https://api.github.com/repos/{repo}/actions/runs?per_page=1"'
        headers = {'Authorization': f'token {GITHUB_TOKEN}', 'Accept': 'application/vnd.github.v3+json'}
        res = httpx.get(url, headers=headers)
        data = json.loads(res.text)
        logger.info(f'仓库 {repo} 最新Actions状态: {data["workflow_runs"][0]["status"]}')
        if data['workflow_runs']:
            run = data['workflow_runs'][0]
            if run['status'] == 'completed':
                # 重新触发Actions
                logger.info(f'仓库 {repo} 完成, 重新触发Actions')
                git.Repo('.').remote(name).push(force=True)
    logger.info('检查完成')


if __name__ == '__main__':
    main()
