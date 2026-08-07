import os
import requests
import re
import io
from PyPDF2 import PdfReader
from urllib.parse import urlparse, parse_qs

# -------------------------- 配置区 --------------------------
LINK_LIST = [
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=795124fbfdde455198face63e5bcb439&sdbh=d43a518ed37e401396ffb3f996a5462d&sdsin=eda9cf58118c074842b79e077bde0dcb",
]

OUTPUT_FOLDER = "court_文书"
API_ENDPOINT = "https://zxfw.court.gov.cn/yzw/yzw-zxfw-sdfw/api/v1/sdfw/getWsListBySdbhNew"
# -----------------------------------------------------------

os.makedirs(OUTPUT_FOLDER, exist_ok=True)

def extract_params(url):
    """从链接提取 qdbh sdbh sdsin"""
    query = parse_qs(urlparse(url).fragment.split("?")[-1])
    return {
        "qdbh": query["qdbh"][0],
        "sdbh": query["sdbh"][0],
        "sdsin": query["sdsin"][0]
    }

def extract_name_from_memory(pdf_bytes):
    """直接在内存字节流中读取PDF内容并提取姓名"""
    try:
        # 将内存中的 bytes 转为二进制流供 PyPDF2 读取
        pdf_stream = io.BytesIO(pdf_bytes)
        reader = PdfReader(pdf_stream)
        
        full_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            if page_text:
                full_text += page_text + "\n"
                
        # 正则匹配被执行人姓名
        pattern = re.compile(r"被执行人[:：]?\s*([\u4e00-\u9fa5]{2,10})")
        match = pattern.search(full_text)
        if match:
            return match.group(1)
        return "未知姓名"
    except Exception as e:
        print(f"内存解析PDF失败：{str(e)}")
        return "读取失败"

def download_and_save_directly():
    """下载PDF并直接以最终名称保存"""
    success_count = 0
    for link in LINK_LIST:
        try:
            params = extract_params(link)
            payload = {
                "qdbh": params["qdbh"],
                "sdbh": params["sdbh"],
                "sdsin": params["sdsin"]
            }
            res = requests.post(API_ENDPOINT, json=payload, timeout=15)
            data_list = res.json().get("data", [])
            
            for item in data_list:
                pdf_url = item["wjlj"]
                raw_name = item["c_wsmc"]
                
                # 1. 下载文件内容到内存（不存盘）
                r = requests.get(pdf_url, timeout=20)
                pdf_bytes = r.content
                
                # 2. 从内存数据中提取姓名
                name = extract_name_from_memory(pdf_bytes)
                
                # 3. 清理原始文书名，去掉“执行完毕”及括号
                clean_raw_name = re.sub(r"[（\(]?执行完毕[）\)]?", "", raw_name).strip()
                
                # 4. 构建最终的目标文件名
                final_name = f"{name}-{clean_raw_name}.pdf"
                save_path = os.path.join(OUTPUT_FOLDER, final_name)
                
                # 5. 如果同一人有同名文书，自动递增序号（例如：庞朋-结案通知书_1.pdf）
                counter = 1
                while os.path.exists(save_path):
                    final_name = f"{name}-{clean_raw_name}_{counter}.pdf"
                    save_path = os.path.join(OUTPUT_FOLDER, final_name)
                    counter += 1
                
                # 6. 直接写入硬盘，一步到位
                with open(save_path, "wb") as f:
                    f.write(pdf_bytes)
                
                print(f"✅ 下载保存成功：{final_name}")
                success_count += 1
                
        except Exception as e:
            print(f"❌ 处理链接失败 {link}: {str(e)}")
            
    return success_count

if __name__ == "__main__":
    print("===== 开始一步到位下载送达文书 =====")
    count = download_and_save_directly()
    print(f"\n🎉 全部任务完成！共下载并命名了 {count} 份文件，目录：{OUTPUT_FOLDER}")