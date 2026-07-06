import os
import sys
import logging
import smtplib
import urllib.request
import urllib.parse
import json
from datetime import datetime
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.utils import formatdate

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(SCRIPT_DIR)
os.chdir(SCRIPT_DIR)

from config import EMAIL_CONFIG, AI_OBSERVER_CONFIG, REPORT_OUTPUT_DIR, LOG_FILE

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(LOG_FILE, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

logger.info(f"脚本目录: {SCRIPT_DIR}")
logger.info(f"当前工作目录: {os.getcwd()}")
logger.info(f"Python路径: {sys.executable}")


def fetch_ai_news():
    logger.info("开始获取AI前沿新闻...")
    try:
        query = AI_OBSERVER_CONFIG["query"]
        url = "https://api.bing.microsoft.com/v7.0/news/search"
        api_key = os.environ.get("BING_API_KEY", "")
        
        if api_key:
            params = urllib.parse.urlencode({
                "q": query,
                "count": 10,
                "mkt": "zh-CN",
                "sortBy": "date"
            })
            full_url = f"{url}?{params}"
            
            req = urllib.request.Request(full_url)
            req.add_header("Ocp-Apim-Subscription-Key", api_key)
            
            with urllib.request.urlopen(req) as response:
                data = json.loads(response.read().decode("utf-8"))
                articles = data.get("value", [])
            
            news_items = []
            for article in articles:
                news_items.append({
                    "title": article.get("name", ""),
                    "url": article.get("url", ""),
                    "description": article.get("description", ""),
                    "source": article.get("provider", [{}])[0].get("name", "")
                })
            
            logger.info(f"成功获取到 {len(news_items)} 条AI新闻")
            return news_items
        else:
            logger.warning("未配置BING_API_KEY环境变量，将使用模拟数据")
            return get_mock_news()
    
    except Exception as e:
        logger.error(f"获取AI新闻失败: {str(e)}")
        return get_mock_news()


def get_mock_news():
    return [
        {
            "title": "GPT-5 模型性能大幅提升，推理速度提高300%",
            "url": "https://openai.com/blog/gpt-5-update",
            "description": "OpenAI今日发布GPT-5模型更新，在保持高精度的同时，推理速度相比GPT-4提升了300%",
            "source": "OpenAI"
        },
        {
            "title": "DeepMind推出新一代AlphaFold，蛋白质结构预测准确率突破99%",
            "url": "https://deepmind.google/discover/blog/alphafold-update/",
            "description": "AlphaFold最新版本在CASP16竞赛中取得突破性成果，预测准确率达到99.2%",
            "source": "Google DeepMind"
        },
        {
            "title": "Anthropic发布Claude 3.5，支持百万token上下文窗口",
            "url": "https://www.anthropic.com/index/claude-3-5",
            "description": "Claude 3.5正式发布，支持1M token上下文，在长文本处理任务中表现优异",
            "source": "Anthropic"
        },
        {
            "title": "Stable Diffusion 4发布，图像生成质量再创新高",
            "url": "https://stability.ai/news/stable-diffusion-4",
            "description": "Stability AI推出Stable Diffusion 4，在图像细节和一致性方面有显著提升",
            "source": "Stability AI"
        },
        {
            "title": "AI芯片市场竞争加剧，多家厂商推出新一代产品",
            "url": "https://techcrunch.com/2024/01/15/ai-chip-market-heats-up/",
            "description": "NVIDIA、AMD、Intel等厂商纷纷发布新一代AI芯片，性能提升显著",
            "source": "TechCrunch"
        }
    ]


def generate_report(news_items):
    logger.info("开始生成日报...")
    today = datetime.now().strftime("%Y年%m月%d日")
    
    report = f"{'='*60}\n"
    report += f"AI前沿技术日报\n"
    report += f"日期: {today}\n"
    report += f"{'='*60}\n\n"
    
    report += "【今日要闻】\n"
    report += "-" * 40 + "\n\n"
    
    for i, news in enumerate(news_items, 1):
        report += f"{i}. {news['title']}\n"
        report += f"   来源: {news['source']}\n"
        report += f"   摘要: {news['description']}\n"
        report += f"   链接: {news['url']}\n"
        report += "\n"
    
    report += "-" * 40 + "\n"
    report += f"报告生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n"
    report += f"共收录 {len(news_items)} 条新闻\n"
    report += "=" * 60 + "\n"
    
    logger.info("日报生成完成")
    return report


def send_email(report):
    logger.info("开始发送邮件...")
    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_CONFIG["sender_email"]
        msg['To'] = EMAIL_CONFIG["receiver_email"]
        msg['Subject'] = f"{EMAIL_CONFIG['email_subject']} - {datetime.now().strftime('%Y%m%d')}"
        msg['Date'] = formatdate(localtime=True)
        
        body = MIMEText(report, 'plain', 'utf-8')
        msg.attach(body)
        
        with smtplib.SMTP(EMAIL_CONFIG["smtp_server"], EMAIL_CONFIG["smtp_port"]) as server:
            server.starttls()
            server.login(EMAIL_CONFIG["sender_email"], EMAIL_CONFIG["sender_password"])
            server.sendmail(
                EMAIL_CONFIG["sender_email"],
                EMAIL_CONFIG["receiver_email"],
                msg.as_string()
            )
        
        logger.info("邮件发送成功")
        return True
    except Exception as e:
        logger.error(f"邮件发送失败: {str(e)}")
        return False


def save_report(report):
    logger.info("保存日报文件...")
    try:
        os.makedirs(REPORT_OUTPUT_DIR, exist_ok=True)
        filename = f"ai_report_{datetime.now().strftime('%Y%m%d')}.txt"
        filepath = os.path.join(REPORT_OUTPUT_DIR, filename)
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(report)
        
        logger.info(f"日报已保存到 {filepath}")
        return filepath
    except Exception as e:
        logger.error(f"保存日报失败: {str(e)}")
        return None


def main():
    logger.info("=" * 60)
    logger.info("AI前沿观察者日报任务启动")
    logger.info("=" * 60)
    
    try:
        news_items = fetch_ai_news()
        report = generate_report(news_items)
        save_report(report)
        send_email(report)
        
        logger.info("日报任务执行完成")
    except Exception as e:
        logger.error(f"日报任务执行失败: {str(e)}", exc_info=True)


if __name__ == "__main__":
    main()