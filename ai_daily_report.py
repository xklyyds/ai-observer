import os
import sys
from datetime import datetime

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
os.chdir(SCRIPT_DIR)

from config import EMAIL_CONFIG, DATA_SOURCES_CONFIG, REPORT_OUTPUT_DIR, LOG_FILE
from data_sources import get_all_data_sources, NewsItem
from processors import get_all_processors
from distributors import get_all_distributors, Report
from utils.logger import setup_logger
from utils.config_loader import load_env_file

load_env_file()


logger = setup_logger("AIObserver", LOG_FILE)


def fetch_all_news() -> list:
    logger.info("开始从所有数据源获取新闻...")
    all_news = []
    
    data_sources = get_all_data_sources()
    for source in data_sources:
        try:
            news = source.fetch()
            all_news.extend(news)
            logger.info(f"从 {source.name} 获取到 {len(news)} 条新闻")
        except Exception as e:
            logger.error(f"从 {source.name} 获取新闻失败: {str(e)}")
    
    logger.info(f"共获取到 {len(all_news)} 条新闻")
    return all_news


def process_news(news_items: list) -> tuple:
    logger.info("开始处理新闻...")
    trend_analyzer = None
    
    processors = get_all_processors()
    for processor in processors:
        try:
            news_items = processor.process(news_items)
            if hasattr(processor, 'get_trends'):
                trend_analyzer = processor
            logger.info(f"{processor.name} 处理完成")
        except Exception as e:
            logger.error(f"{processor.name} 处理失败: {str(e)}")
    
    return news_items, trend_analyzer


def generate_report(news_items: list, trend_analyzer=None) -> Report:
    logger.info("开始生成日报...")
    today = datetime.now().strftime("%Y年%m月%d日")
    generated_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"{'='*60}\n"
    report += f"AI前沿技术日报\n"
    report += f"日期: {today}\n"
    report += f"{'='*60}\n\n"
    
    if trend_analyzer:
        report += trend_analyzer.generate_trend_summary()
        report += "\n"
    
    report += "【今日要闻】\n"
    report += "-" * 40 + "\n\n"
    
    categories = {}
    for item in news_items:
        cat = item.category or "未分类"
        if cat not in categories:
            categories[cat] = []
        categories[cat].append(item)
    
    for category, items in categories.items():
        report += f"📁 {category}\n"
        for i, news in enumerate(items, 1):
            tags_str = f" [{' '.join(f'#{t}' for t in news.tags)}]" if news.tags else ""
            report += f"   {i}. {news.title}{tags_str}\n"
            report += f"      来源: {news.source}\n"
            report += f"      摘要: {news.description}\n"
            report += f"      链接: {news.url}\n"
            if news.author:
                report += f"      作者: {news.author}\n"
            report += "\n"
    
    report += "-" * 40 + "\n"
    report += f"报告生成时间: {generated_at}\n"
    report += f"共收录 {len(news_items)} 条新闻\n"
    report += "=" * 60 + "\n"
    
    logger.info("日报生成完成")
    return Report(report, today, len(news_items))


def distribute_report(report: Report):
    logger.info("开始分发日报...")
    
    email_config = EMAIL_CONFIG if EMAIL_CONFIG["sender_email"] else None
    distributors = get_all_distributors(email_config)
    
    for distributor in distributors:
        try:
            success = distributor.distribute(report)
            if success:
                logger.info(f"{distributor.name} 分发成功")
            else:
                logger.warning(f"{distributor.name} 分发失败")
        except Exception as e:
            logger.error(f"{distributor.name} 分发异常: {str(e)}")


def main():
    logger.info("=" * 60)
    logger.info("AI前沿观察者日报任务启动")
    logger.info("=" * 60)
    
    try:
        news_items = fetch_all_news()
        news_items, trend_analyzer = process_news(news_items)
        report = generate_report(news_items, trend_analyzer)
        distribute_report(report)
        
        logger.info("日报任务执行完成")
    except Exception as e:
        logger.error(f"日报任务执行失败: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()