import asyncio
import logging
from core.config import load_config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

config = load_config()

async def main():
    logger.info(f"Starting system in {'DEBUG' if config.DEBUG else 'PROD'} mode")
    logger.info(f"Active projects: {config.PROJECT1_ENABLED}, {config.PROJECT2_ENABLED}, {config.PROJECT3_ENABLED}")
    
    # Здесь будет запуск модулей
    while True:
        await asyncio.sleep(1)

if __name__ == "__main__":
    asyncio.run(main())