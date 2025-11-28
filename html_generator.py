"""HTML生成器 - 使用外部模板"""

from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Union
from string import Template
import pytz


def load_template() -> Template:
    """加载HTML模板"""
    template_path = Path("template.html")
    if not template_path.exists():
        raise FileNotFoundError("HTML模板文件 template.html 不存在")

    with open(template_path, "r", encoding="utf-8") as f:
        content = f.read()
        # 使用 Template 类而不是 format
        return Template(content)


def render_html_report(
    report_data: Dict,
    total_titles: int,
    hot_news_count: int,
    word_count: int,
    failed_ids: Optional[List] = None,
    new_titles: Optional[Dict] = None,
    id_to_name: Optional[Dict] = None,
    mode: str = "daily",
    is_daily_summary: bool = False,
    update_info: Optional[Dict] = None,
) -> str:
    """使用模板渲染HTML报告"""

    # 加载模板
    template = load_template()

    # 准备数据
    now = datetime.now(pytz.timezone("Asia/Shanghai"))
    update_time = now.strftime("%H:%M")
    generation_time = now.strftime("%Y年%m月%d日 %H:%M 生成")

    # 生成错误信息部分（如果有）
    error_section = ""
    if failed_ids:
        error_section = """
        <div class="error-section">
            <div class="error-title">获取失败的平台</div>
            <ul class="error-list">"""
        for failed_id in failed_ids:
            error_section += f"<li class='error-item'>{failed_id}</li>"
        error_section += """
            </ul>
        </div>"""

    # 生成热点词组HTML
    word_groups_html = ""
    for stat in report_data.get("stats", []):
        if stat["count"] > 0:
            word_groups_html += generate_word_group_html(stat, id_to_name)

    # 生成新增新闻HTML
    new_news_section = ""
    if new_titles:
        # 处理不同的数据格式
        if isinstance(new_titles, dict):
            # 字典格式
            if any(len(titles) > 0 for titles in new_titles.values()):
                new_news_section = generate_new_news_html(new_titles, id_to_name)
        elif isinstance(new_titles, list):
            # 列表格式
            if any(len(source.get("titles", [])) > 0 for source in new_titles):
                new_news_section = generate_new_news_html(new_titles, id_to_name)

    # 获取保存脚本
    save_script = get_save_script()

    # 替换模板中的占位符
    html = template.substitute(
        total_titles=total_titles,
        hot_news_count=hot_news_count,
        word_count=word_count,
        update_time=update_time,
        generation_time=generation_time,
        error_section=error_section,
        word_groups=word_groups_html,
        new_news_section=new_news_section,
        save_script=save_script
    )

    return html


def generate_word_group_html(stat: Dict, id_to_name: Optional[Dict]) -> str:
    """生成单个热点词组的HTML"""
    word = stat["word"]
    count = stat["count"]
    titles = stat["titles"]

    # 提取分类名称（只取#后面的第一部分）
    import re
    category_match = re.match(r'^(#\s*[^#\s]+)', word)
    if category_match:
        display_name = category_match.group(1).strip()
    else:
        # 如果没有#格式，尝试按空格分割
        parts = word.split()
        if parts:
            display_name = parts[0]
        else:
            display_name = word

    # 确定热度等级
    if count >= 20:
        hot_class = "hot"
        hot_text = f"🔥 {count} 条"
    elif count >= 10:
        hot_class = "warm"
        hot_text = f"{count} 条"
    else:
        hot_class = "normal"
        hot_text = f"{count} 条"

    # 确定分类（简化版，可以根据需要调整）
    category = "tech"  # 默认分类
    if any(x in word for x in ["音乐", "演唱会", "抖音", "B站", "bilibili"]):
        category = "music"
    elif any(x in word for x in ["电影", "原神", "黑神话", "游戏"]):
        category = "entertainment"
    elif any(x in word for x in ["胖东来", "996", "调休", "房价"]):
        category = "social"

    # 生成新闻项HTML
    news_items_html = ""
    for idx, title_info in enumerate(titles[:20], 1):  # 最多显示20条
        title = title_info["title"]
        # 修复source字段访问错误 - 使用source_name字段代替source
        source = title_info.get("source_name", "未知平台")
        ranks = title_info.get("ranks", [])
        times = [title_info.get("time_display", "")]
        url = title_info.get("url", "")

        # 确定排名样式
        rank_class = ""
        if ranks and min(ranks) <= 3:
            rank_class = "top"
        elif ranks and min(ranks) <= 10:
            rank_class = "high"

        # 生成排名显示
        rank_display = ""
        if ranks:
            if len(ranks) == 1:
                rank_display = f"{ranks[0]}位"
            else:
                rank_display = f"{min(ranks)}-{max(ranks)}位"

        # 生成时间显示
        time_display = ""
        if times:
            time_display = times[0] if len(times) == 1 else f"{times[0]}~{times[-1]}"

        # 检查是否是新增
        is_new = title_info.get("is_new", False)

        news_items_html += f"""
                <div class="news-item{' new' if is_new else ''}">
                    <div class="news-rank {rank_class}">{idx}</div>
                    <div class="news-content">
                        <div class="news-meta">
                            <span class="news-source">{source}</span>
                            <span>{rank_display}</span>
                            <span>{time_display}</span>
                        </div>
                        <h3 class="news-title">
                            <a href="{url}" class="news-link" target="_blank">{title}</a>
                        </h3>
                    </div>
                    {'''<span class="new-badge">NEW</span>''' if is_new else ''}
                </div>"""

    return f"""
            <div class="hot-group" data-category="{category}">
                <div class="group-header" onclick="toggleGroup(this)">
                    <div class="group-info">
                        <span class="group-name">{display_name}</span>
                        <span class="group-count {hot_class}">{hot_text}</span>
                    </div>
                    <span class="expand-icon">▼</span>
                </div>
                <div class="news-list">
                    {news_items_html}
                </div>
            </div>"""


def generate_new_news_html(new_titles: Union[List, Dict], id_to_name: Optional[Dict]) -> str:
    """生成新增新闻的HTML"""
    # 处理不同的数据格式
    if not new_titles:
        return ""

    # 添加调试信息
    print(f"DEBUG: new_titles type: {type(new_titles)}")
    if isinstance(new_titles, dict):
        print(f"DEBUG: new_titles keys: {list(new_titles.keys())[:5]}...")  # 只显示前5个键

    if isinstance(new_titles, dict):
        # 如果是字典格式（原始数据）
        total_count = sum(len(titles) for titles in new_titles.values())

        new_items_html = ""
        for source_id, titles in new_titles.items():
            if titles:
                source_name = id_to_name.get(source_id, source_id)

                source_items_html = ""
                for idx, (title, title_data) in enumerate(list(titles.items())[:10], 1):  # 每个平台最多显示10条
                    rank = title_data.get("rank", 0)
                    url = title_data.get("url", "")

                    rank_class = ""
                    if rank <= 3:
                        rank_class = "top"
                    elif rank <= 10:
                        rank_class = "high"

                    source_items_html += f"""
                        <div class="new-item">
                            <div class="new-item-rank {rank_class}">{idx}</div>
                            <div class="new-item-rank {rank_class}">{rank}</div>
                            <div class="new-item-content">
                                <div class="new-item-title">
                                    <a href="{url}" class="news-link" target="_blank">{title}</a>
                                </div>
                            </div>
                        </div>"""

                new_items_html += f"""
                <div class="new-source-group">
                    <div class="new-source-title">{source_name} · {len(titles)}条</div>
                    {source_items_html}
                </div>"""
    else:
        # 如果是列表格式（处理过的数据）
        total_count = sum(len(source.get("titles", [])) for source in new_titles)

        new_items_html = ""
        for source_data in new_titles:
            source_name = source_data.get("source_name", "未知平台")
            titles = source_data.get("titles", [])

            if titles:
                source_items_html = ""
                for idx, title_info in enumerate(titles[:10], 1):  # 每个平台最多显示10条
                    title = title_info.get("title", "")
                    rank = title_info.get("ranks", [0])[0] if title_info.get("ranks") else 0
                    url = title_info.get("url", "")

                    rank_class = ""
                    if rank <= 3:
                        rank_class = "top"
                    elif rank <= 10:
                        rank_class = "high"

                    source_items_html += f"""
                        <div class="new-item">
                            <div class="new-item-rank {rank_class}">{idx}</div>
                            <div class="new-item-rank {rank_class}">{rank}</div>
                            <div class="new-item-content">
                                <div class="new-item-title">
                                    <a href="{url}" class="news-link" target="_blank">{title}</a>
                                </div>
                            </div>
                        </div>"""

                new_items_html += f"""
                <div class="new-source-group">
                    <div class="new-source-title">{source_name} · {len(titles)}条</div>
                    {source_items_html}
                </div>"""

    return f"""
            <div class="new-section">
                <div class="new-section-title">本次新增热点 (共 {total_count} 条)</div>
                {new_items_html}
            </div>"""


def get_save_script() -> str:
    """获取保存图片的JavaScript代码"""
    return """async function saveAsImage() {
        const button = event.target;
        const originalText = button.textContent;

        try {
            button.textContent = '生成中...';
            button.disabled = true;
            window.scrollTo(0, 0);

            await new Promise(resolve => setTimeout(resolve, 200));

            const buttons = document.querySelector('.save-buttons');
            buttons.style.visibility = 'hidden';

            await new Promise(resolve => setTimeout(resolve, 100));

            const container = document.querySelector('.container');

            const canvas = await html2canvas(container, {
                backgroundColor: '#ffffff',
                scale: 1.5,
                useCORS: true,
                allowTaint: false,
                imageTimeout: 10000,
                logging: false
            });

            buttons.style.visibility = 'visible';

            const link = document.createElement('a');
            const now = new Date();
            const filename = `NewsForDaxZhu_${now.getFullYear()}${String(now.getMonth() + 1).padStart(2, '0')}${String(now.getDate()).padStart(2, '0')}_${String(now.getHours()).padStart(2, '0')}${String(now.getMinutes()).padStart(2, '0')}.png`;

            link.download = filename;
            link.href = canvas.toDataURL('image/png', 1.0);

            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);

            button.textContent = '保存成功!';
            setTimeout(() => {
                button.textContent = originalText;
                button.disabled = false;
            }, 2000);

        } catch (error) {
            const buttons = document.querySelector('.save-buttons');
            buttons.style.visibility = 'visible';
            button.textContent = '保存失败';
            setTimeout(() => {
                button.textContent = originalText;
                button.disabled = false;
            }, 2000);
        }
    }

    async function saveAsMultipleImages() {
        alert('分段保存功能开发中...');
    }

    // 页面加载完成后默认展开第一个分组
    document.addEventListener('DOMContentLoaded', function() {
        const firstGroup = document.querySelector('.hot-group');
        if (firstGroup) {
            firstGroup.classList.add('expanded');
        }
    });"""