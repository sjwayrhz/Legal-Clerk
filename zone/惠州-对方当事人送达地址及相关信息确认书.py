import os
import re
import pdfplumber

try:
    import fitz  # PyMuPDF
except ImportError:
    print("⚠️ 缺少 PyMuPDF 库，无法向确认书PDF中追加文字。请在终端运行: pip install PyMuPDF")
    exit()

# ========================================================================
# 字体路径匹配配置（优先查找 仿宋_GB2312 / 仿宋 字体）
# ========================================================================
CURRENT_DIR = os.path.dirname(os.path.abspath(__file__))

FONT_CANDIDATE_PATHS = [
    # 1. 优先搜索脚本当前目录下的字体文件（如果你手动放了字体包）
    os.path.join(CURRENT_DIR, "fangsong_GB2312.ttf"),
    os.path.join(CURRENT_DIR, "simfang.ttf"),
    os.path.join(CURRENT_DIR, "FANGSONG.TTF"),
    # 2. 搜索 Windows 系统字体目录
    r"C:\Windows\Fonts\fangsong_GB2312.ttf",
    r"C:\Windows\Fonts\FANGSONG_GB2312.TTF",
    r"C:\Windows\Fonts\simfang.ttf",
    r"C:\Windows\Fonts\SIMFANG.TTF",
    # 3. 兜底方案：宋体
    r"C:\Windows\Fonts\simsun.ttc",
]

def get_font_file():
    """获取系统中可用的仿宋字体路径"""
    for path in FONT_CANDIDATE_PATHS:
        if os.path.exists(path):
            return path
    return None

# ========================================================================
# 核心功能 1：将信息写入《送达地址及相关信息确认书》PDF（使用仿宋字体）
# ========================================================================
def fill_confirmation_pdf(template_path, output_path, name, address, phone):
    """
    通过底层坐标定位，将提取出的信息填入确认书模板（使用仿宋/仿宋_GB2312字体）。
    """
    doc = fitz.open(template_path)
    page = doc[0]

    font_path = get_font_file()
    font_alias = "CustomFangSong"
    
    if font_path:
        # 向 PDF 页面中嵌入仿宋字体
        page.insert_font(fontname=font_alias, fontfile=font_path)
    else:
        print("⚠️ 未找到仿宋字体，将使用默认字体填充。")
        font_alias = "helv"

    # 穷举PDF文本层中可能出现的冒号和括号的中英文全半角状态，确保精准定位
    search_exact = {
        "被告名称(姓名):": name,
        "被告名称（姓名）：": name,
        "工商注册地址(自然人戶籍地):": address,   # 模板中的繁体“戶”
        "工商注册地址(自然人户籍地):": address,
        "工商注册地址（自然人户籍地）：": address,
        "实际经营地址(自然人实际住所地):": address,
        "实际经营地址（自然人实际住所地）：": address,
        "电话:": phone,
        "电话：": phone,
        "电话(送达地址电话):": phone,
        "电话（送达地址电话）：": phone
    }

    filled_y_ranges = []

    for keyword, text_value in search_exact.items():
        rects = page.search_for(keyword)
        for rect in rects:
            # 容错处理：若该行（Y坐标周围）已经填过内容，则跳过
            if any(abs(rect.y1 - fy) < 10 for fy in filled_y_ranges):
                continue
            
            box_width = 540 - (rect.x1 + 5)
            
            # 对于地址等较长文本，使用 insert_textbox 支持自动换行填入
            if len(text_value) > 15:
                textbox_rect = fitz.Rect(rect.x1 + 5, rect.y0, rect.x1 + 5 + box_width, rect.y1 + 30)
                # 采用 11号 仿宋字体
                page.insert_textbox(textbox_rect, text_value, fontname=font_alias, fontsize=11, color=(0,0,0))
            else:
                # 短文本直接插入
                point = fitz.Point(rect.x1 + 5, rect.y1 - 2)
                page.insert_text(point, text_value, fontname=font_alias, fontsize=11, color=(0,0,0))
            
            filled_y_ranges.append(rect.y1)

    doc.save(output_path)

# ========================================================================
# 核心功能 2：从《强制执行申请书》提取无缝拼接的文本数据
# ========================================================================
def extract_info(pdf_path):
    """
    提取姓名、地址和电话。提取前擦除换行符，完美解决跨行导致地址断裂问题。
    """
    try:
        with pdfplumber.open(pdf_path) as pdf:
            text = "".join(page.extract_text() for page in pdf.pages if page.extract_text())
            
        info_text = text.replace("\n", "").replace(" ", "").replace("\u3000", "")

        respondent_match = re.search(r"被执行人[:：](.*?)请求事项", info_text)
        if not respondent_match:
            return None, None, None
            
        respondent_text = respondent_match.group(1)

        name_match = re.search(r"^([^，。、,]+)", respondent_text)
        phone_match = re.search(r"(?:联系)?电话[:：](\d+)", respondent_text)
        address_match = re.search(r"住(.*?)(?:，|,|。|身份证)", respondent_text)

        name = name_match.group(1) if name_match else ""
        phone = phone_match.group(1) if phone_match else ""
        address = address_match.group(1) if address_match else ""

        return name, address, phone

    except Exception as e:
        print(f"❌ 处理 {pdf_path} 时出错: {e}")
        return None, None, None

# ========================================================================
# 流程控制
# ========================================================================
def process_folders(base_dir):
    template_name = "对方当事人送达地址及相关信息确认书.pdf"
    template_path = os.path.join(base_dir, template_name)
    
    if not os.path.exists(template_path):
        print(f"❌ 严重错误：未在当前目录找到模板文件 '{template_name}'！")
        print("   👉 请将空白的确认书模板放在与本 Python 脚本同一目录下，然后再运行。")
        return

    # 打印当前生效的字体文件路径
    used_font = get_font_file()
    if used_font:
        print(f"🔤 当前调用的字体文件: {os.path.basename(used_font)}")
    else:
        print("⚠️ 警告：未在系统或本地找到仿宋字体文件！")

    print(f"当前锁定扫描路径: {base_dir}\n")

    # 1. 尝试处理根目录本身存在的PDF
    root_pdf_path = os.path.join(base_dir, "强制执行申请书.pdf")
    if os.path.exists(root_pdf_path) and os.path.isfile(root_pdf_path):
        print("发现当前目录存在案卷，正在处理...")
        name, addr, phone = extract_info(root_pdf_path)
        if name:
            output_path = os.path.join(base_dir, f"已填写_{template_name}")
            fill_confirmation_pdf(template_path, output_path, name, addr, phone)
            print(f"   ✅ 数据提取成功，生成：{os.path.basename(output_path)}")

    # 2. 遍历所有子文件夹进行批量处理
    for item in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, item)

        if os.path.isdir(folder_path):
            pdf_path = os.path.join(folder_path, "强制执行申请书.pdf")
            
            if not os.path.exists(pdf_path) or not os.path.isfile(pdf_path):
                continue

            print(f"发现子文件夹 [{item}] 存在案卷，正在处理...")
            name, addr, phone = extract_info(pdf_path)
            
            if name:
                output_path = os.path.join(folder_path, template_name)
                fill_confirmation_pdf(template_path, output_path, name, addr, phone)
                print(f"   ✅ 数据提取成功，生成：{template_name}")
            else:
                print(f"   ⚠️ 未能从 [{item}] 中提取到有效的被执行人信息，已跳过。")

if __name__ == "__main__":
    current_directory = os.path.dirname(os.path.abspath(__file__))
    
    print("="*50)
    print(" 确认书自动化填字脚本启动 (已支持 仿宋/仿宋_GB2312 字体)")
    print("="*50)
    
    process_folders(current_directory)
    
    print("\n" + "="*50)
    input("所有任务已执行完毕。按回车键(Enter)退出...")