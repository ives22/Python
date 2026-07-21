import os
import logging
from logging.handlers import TimedRotatingFileHandler



LOG_FILE = '/var/log/openvpn/hw_auth.log'

def setup_logging():
    handler = TimedRotatingFileHandler(
        LOG_FILE,
        when="midnight",       # Day
        interval=1,     # 间隔1天
        backupCount=30, # 保留30个文件
        encoding='utf-8'
    )

    handler.namer = lambda name: name + ".gz"
    handler.compressor = lambda data: __import__('gzip').compress(data)

    formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s', datefmt='%Y-%m-%d %H:%M:%S')
    handler.setFormatter(formatter)

    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    logger.addHandler(handler)

def write_log(message: str):
    """统一日志写入"""
    try:
        with open(LOG_FILE, 'a', encoding='utf-8') as f:
            f.write(message + '\n')
    except Exception as err:
        print(str(err))
        pass

def main():
    for k, v in os.environ.items():
        logging.info(f"{k}: {v}")

if __name__ == "__main__":
    setup_logging()
    main()