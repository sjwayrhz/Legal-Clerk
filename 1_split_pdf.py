import os
import re
from PyPDF2 import PdfReader, PdfWriter

# =========强制锁定工作目录为脚本所在位置，根治右键运行失败==========
SCRIPT_PATH = os.path.abspath(__file__)
BASE_WORK_DIR = os.path.dirname(SCRIPT_PATH)
os.chdir(BASE_WORK_DIR)
print(f"✅ 已锁定程序根目录：{BASE_WORK_DIR}")

def split_execution_documents(input_pdf_path):
    if not os.path.exists(input_pdf_path):
        print(f"❌ 未找到文件: {input_pdf_path}")
        return

    work_dir = os.path.dirname(os.path.abspath(input_pdf_path))
    folder_name = os.path.basename(work_dir)
    output_dir = work_dir
    
    try:
        reader = PdfReader(input_pdf_path)
        total_pages = len(reader.pages)
        print(f"📄 成功加载文档，总页数: {total_pages}")
    except Exception as e:
        print(f"❌ 读取 PDF 失败: {e}")
        return

    # 根据文件夹名称判断使用的拆分映射配置
    if "衢仲字" in folder_name:
        print(f"💡 关键字中含有“衢仲字” (文件夹: {folder_name})")
        page_mapping = {
            "_强制执行申请书.pdf": (5, 5),
            "_授权委托书.pdf": (13, 13),
            "借款合同.pdf": (1, 4), # ✅ 保持不动，不加下划线
            "被执行人身份证.pdf": (14, 14),
            "送达地址确认书.pdf": (11, 11),
            "银行账户确认书.pdf": (10, 10),
            "纳入失信申请书.pdf": (9, 9),
            "限高申请书.pdf": (8, 8),
        }
    # 匹配纯数字且以 201x 或 202x 年份开头的文件夹名称（如 20238501）
    elif folder_name.isdigit() and re.match(r'^(201|202)\d+', folder_name):
        print(f"💡 检测到纯数字年份案号文件夹: {folder_name}")
        page_mapping = {
            "_强制执行申请书.pdf": (8, 9),
            "被执行人身份证.pdf": (14, 15),
            "_授权委托书.pdf": (13, 13),
            "送达地址和行账户确认书.pdf": (12, 12),
            "纳入失信申请书.pdf": (11, 11),
            "限高申请书.pdf": (10, 10),
        }
    else:
        print(f"⚠️ 文件夹名称 [{folder_name}] 不符合已定义的识别规则，跳过拆分。")
        return

    # 1. 执行PDF拆分生成
    for output_name, (start_idx, end_idx) in page_mapping.items():
        if start_idx >= total_pages or end_idx >= total_pages or start_idx > end_idx:
            print(f"⚠️ 跳过 {output_name}: 配置页码范围 ({start_idx}, {end_idx}) 超出实际页数 ({total_pages})")
            continue
        writer = PdfWriter()
        for i in range(start_idx, end_idx + 1):
            writer.add_page(reader.pages[i])
        
        output_path = os.path.join(output_dir, output_name)
        try:
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            print(f"✅ 成功生成: {output_name}")
        except Exception as e:
            print(f"❌ 写入 {output_name} 失败: {e}")

    # 2. 处理遗留文件的重命名：移除了借款合同，仅对申请书和委托书补全下划线
    rename_targets = ["裁决书及送达.pdf", "强制执行申请书.pdf", "授权委托书.pdf"]
    for old_name in rename_targets:
        old_path = os.path.join(work_dir, old_name)
        new_path = os.path.join(work_dir, "_" + old_name)
        if os.path.exists(old_path) and not os.path.exists(new_path):
            try:
                os.rename(old_path, new_path)
                print(f"✅ 已重命名补全下划线: {old_name} -> _{old_name}")
            except Exception as e:
                print(f"❌ 重命名 {old_name} 失败: {e}")

    # 3. 删除源文件
    try:
        os.remove(input_pdf_path)
        print(f"🗑️ 已清理源文件: {os.path.basename(input_pdf_path)}")
    except Exception as e:
        print(f"❌ 删除源文件失败: {e}")
    print("-" * 40)

def find_and_split_all(target_filename="强制执行申请材料.pdf"):
    current_dir = os.getcwd()
    processed = 0
    
    # 1. 当前目录查找
    current_file = os.path.join(current_dir, target_filename)
    if os.path.exists(current_file):
        print(f"\n{'='*50}")
        print(f"🔍 当前目录发现目标文件: {current_file}")
        split_execution_documents(current_file)
        processed += 1
        
    # 2. 一级子目录遍历
    for entry in os.listdir(current_dir):
        entry_path = os.path.join(current_dir, entry)
        if os.path.isdir(entry_path):
            sub_file = os.path.join(entry_path, target_filename)
            if os.path.exists(sub_file):
                print(f"\n{'='*50}")
                print(f"🔍 子目录发现目标文件: {sub_file}")
                split_execution_documents(sub_file)
                processed += 1
                
    print(f"\n{'='*50}")
    if processed > 0:
        print(f"🎉 全部任务完成！共处理 {processed} 个PDF文件")
    else:
        print(f"⚠️ 未找到任何名为 '{target_filename}' 的PDF文件")

if __name__ == "__main__":
    try:
        print(f"🚀 开始扫描当前目录及一级子目录...")
        find_and_split_all()
    except Exception as err:
        print(f"程序异常：{err}")
    input("\n按下回车键关闭窗口")