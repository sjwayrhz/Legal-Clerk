import os
import requests
import re
import io
from PyPDF2 import PdfReader
from urllib.parse import urlparse, parse_qs

# -------------------------- 配置区 --------------------------
LINK_LIST = [
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=795124fbfdde455198face63e5bcb439&sdbh=d43a518ed37e401396ffb3f996a5462d&sdsin=eda9cf58118c074842b79e077bde0dcb",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=10a42b7ed131497aa9740de54044471b&sdbh=60d44f0f33684d4099a420f56b9b6b59&sdsin=849e07f67b282ed05892d0348299241f",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=da7ac98657a24d3f98a9e36f1609cdc3&sdbh=f782339c13094392b1cd5fdb153ad36c&sdsin=fc2565a799c1da1791d7e7e51aeed6ad",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=a98f3b265bee402cb36d6920555e2384&sdbh=3b1aed1bf51b48d39d1a351cfe36560a&sdsin=ebf3e17a45e383baba7036d9dcca0d72",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=6331e3716a44433789c396edd9e8f916&sdbh=7fedd068523342b8bfaefd91bc3e6dab&sdsin=99b0a13a13400cec78afbcdd6de3962c",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=3dc8bedf9c944885871df340c4077203&sdbh=e3902cd2cb2b4dd999d080931d237b02&sdsin=f409ce9e8383ac3d060728fd8ed8cb09",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=f2e2d238f51547fe88294c621507efc3&sdbh=f5051243da894b668f03a3cc0a7734fd&sdsin=2840d4db497bf837721ab8a9b39fdf5c",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=106e6718a4454402b277e71d65ed9388&sdbh=0833e944fd4641de99b0d079c3cf1fe0&sdsin=8d669c062d063cefd1e115e07818834f",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=fb83a8e3bf774067bffbe37c84119aa7&sdbh=9ac01535595a491bae221b9fec970cbd&sdsin=1cf24f6b126a21f2f220fba7bc2c530b",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=74e48083d9ab421c9c5e31ee7e21f327&sdbh=7974b76c580541e3aef191ab3c01958c&sdsin=44f921bbd5aa2b47ffa36355a9061537",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=da2379740a9a486bb3b5269a18168144&sdbh=871dc6f60d2a40a6812a1f20b98b1aac&sdsin=b81aeabc61ff47c857808cf08440c8bd",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=5f9d5d31f5fd4054a670618bce574f6e&sdbh=9486f07573154576bac0c1cfc4c19d3b&sdsin=debc3e7114c66288522a4363c103a370",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=ef2bd33bd149476b9cf74cefec0cb0fb&sdbh=4ae4a2648c27437186d07b1ff5f55d0b&sdsin=196b5ff1a3244cbece2a38d4f6de6382",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=cf775f86d0c94343bc96dcad63eb07ba&sdbh=403d5f214021472182690b8de1a3567c&sdsin=6029a834644548893b91c57b337c4f5a",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=3e35b3d3ba184b8797178485a07228f2&sdbh=21c92797c56a4c399be004fcd9b4a627&sdsin=93064a9a15b6e940f0dbef2e982d981a",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=b73e804e69aa4227a31e9468075ee4ed&sdbh=07b60f1db97b40aaa7014d64b97a4d42&sdsin=d0c6b8e77c67442ccd47f8fc7c42fe2c",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=ee7d5294d2cc4379aef4d400a0ef9d16&sdbh=043ab9e0e5104c15b0947a70bf9d58d8&sdsin=a5949ba99578d1f995138e8335ce29d5",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=e49ebcdfd2cf4acb87ca80da1273ba6b&sdbh=c4283bfc81b54d0ebd73be4397ae8a18&sdsin=fa64a74476e95df9932e1e573decc248",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=b0821860df78405cb12228cf7097c3ed&sdbh=4c6ade171c9e45b9bf76765d7f73a39a&sdsin=f0510e9c9e85ce7818f59bb82168eedd",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=80c6233537d44b95a9f9a628ae2ba0b1&sdbh=613e7f0561ac442b9dbb24d02dafca5e&sdsin=c031af28d530b50adcce21897a3a6344",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=1ef2697b66034f80a38555466187c691&sdbh=f4f4c2977b28419c93304c3140a3c097&sdsin=9b082d330b6079db570b5b4f68d0662a",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=c8f5adb64ed94415bbc8f0796561d0cc&sdbh=ed91ba25a0bd4d2fb89ed6c4a4ac3b92&sdsin=89ff1a10677d6dcc0ac3b8a3ee8acf3b",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=aa21006ba6964acaa878ec96c2a33a31&sdbh=0f1cd825c58842d1a131f118d03ff6e5&sdsin=5836774e75ef4d68f3e314c8210775f4",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=e6fff13d5130467084fd1df5bed2721d&sdbh=0090fecd36894878a9e5b480f6f18ae5&sdsin=75a4d8909987b46c4d7fabb145e3822b",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=839cb112b11e426c85b164962068f775&sdbh=6841df5b90f74927935c7f3619bb063b&sdsin=61f4f9b6059d43bbccbde5ffd9a76f14",
    "https://zxfw.court.gov.cn/zxfw/#/pagesAjkj/app/wssd/index?qdbh=26d1d1d9ebdb4ca8bc2b541a5c45b1d9&sdbh=512378c594d149c290c09c8e1dc49e6c&sdsin=97eee31e8830ede688c7f1acb4f6f9b5"
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