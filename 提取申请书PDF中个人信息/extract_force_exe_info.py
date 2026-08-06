import os
import re
import pdfplumber

def pad_key(key):
    # 使用全角空格（\u3000）将所有键名对齐到4个中文字符宽度
    # 这样可以确保后面拼接的 -> 能够完全垂直对齐
    return key + '\u3000' * (4 - len(key))

def process_folders(base_dir):
    # 遍历当前目录下的所有项
    for item in os.listdir(base_dir):
        folder_path = os.path.join(base_dir, item)
        
        # 判断是否为文件夹
        if os.path.isdir(folder_path):
            case_number = item
            pdf_path = os.path.join(folder_path, "强制执行申请书.pdf")
            txt_path = os.path.join(folder_path, "强制执行申请书.txt")
            
            # 如果文件夹内没有目标PDF，则跳过
            if not os.path.exists(pdf_path):
                continue
                
            print(f"正在处理文件夹: {item}")
            
            try:
                # 提取 PDF 文本
                with pdfplumber.open(pdf_path) as pdf:
                    text = ""
                    for page in pdf.pages:
                        page_text = page.extract_text()
                        if page_text:
                            text += page_text + "\n"
                        
                # 1. 基础信息提取（消除文本中的换行和空格）
                info_text = text.replace("\n", "").replace(" ", "").replace("\u3000", "")
                
                # 【关键修复1】圈定“被执行人”区域，避免提取到申请执行人的电话和信息
                respondent_match = re.search(r"被执行人：(.*?)(?=请求事项|事实与理由|1、|$)", info_text)
                # 如果匹配成功则只在截取的内容里找，否则兜底用全文
                respondent_text = respondent_match.group(1) if respondent_match else info_text
                
                name_match = re.search(r"^([^，。、]+)", respondent_text)
                gender_match = re.search(r"性别：([^，。、]+)", respondent_text)
                
                # 兼容“电话：”或“联系电话：”
                phone_match = re.search(r"(?:联系)?电话：(\d+)", respondent_text)
                id_match = re.search(r"身份证号：([0-9xX]+)", respondent_text)
                address_match = re.search(r"住(.*?)(?:，|。|身份证)", respondent_text)
                
                name = name_match.group(1) if name_match else "未找到"
                gender = gender_match.group(1) if gender_match else "未找到"
                phone = phone_match.group(1) if phone_match else "未找到"
                id_card = id_match.group(1) if id_match else "未找到"
                address = address_match.group(1) if address_match else "未找到"
                
                # 2. 提取“执行请求”明细部分
                # 【关键修复3】遇到"事实与理由"或落款时停止抓取，摒弃不需要的内容
                request_match = re.search(r"(1、.*?)(?=事实与理由|申请执行人|此致|\Z)", text, re.DOTALL)
                
                if request_match:
                    raw_request = request_match.group(1).strip()
                    # 【关键修复3】去除不该换行的换行符。逻辑：如果换行符后面紧接着的不是“数字+、”，则直接删除换行将其与上一行拼接
                    request_text = re.sub(r'\s*\n\s*(?!\d+、)', '', raw_request)
                else:
                    request_text = "未找到执行请求明细内容"
                    
                # 3. 按照要求格式化输出
                sep = "     ->     " # 左右保留5个空格
                output_lines = [
                    # 【关键修复2】使用 pad_key 动态添加全角空格，保证 -> 绝对对齐
                    f"{pad_key('案号')}{sep}{case_number}",
                    f"{pad_key('姓名')}{sep}{name}",
                    f"{pad_key('性别')}{sep}{gender}",
                    f"{pad_key('电话')}{sep}{phone}",
                    f"{pad_key('身份证号')}{sep}{id_card}",
                    f"{pad_key('住址')}{sep}{address}",
                    "", "", "", # 【关键修复3】执行请求上方空 3 行
                    "执行请求",
                    "",
                    request_text
                ]
                
                # 4. 写入 txt 文件
                with open(txt_path, "w", encoding="utf-8") as f:
                    f.write("\n".join(output_lines))
                    
                print(f"成功生成: {txt_path}")
                
            except Exception as e:
                print(f"处理 {item} 时出错: {e}")

if __name__ == "__main__":
    current_directory = os.getcwd()
    process_folders(current_directory)