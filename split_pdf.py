import os
from PyPDF2 import PdfReader, PdfWriter

def split_execution_documents(input_pdf_path):
    # 检查输入文件是否存在
    if not os.path.exists(input_pdf_path):
        print(f"❌ 未找到文件: {input_pdf_path}")
        return

    # 获取输入文件所在的目录，确保生成的文件在同级目录下
    output_dir = os.path.dirname(os.path.abspath(input_pdf_path))
    
    # 初始化 PDF 读取器
    try:
        reader = PdfReader(input_pdf_path)
        total_pages = len(reader.pages)
        print(f"📄 成功加载文档，总页数: {total_pages}")
    except Exception as e:
        print(f"❌ 读取 PDF 失败: {e}")
        return

    # ==========================================
    # 📌 核心配置区：定义每个文件对应的起止页码
    # 注意：Python 的索引是从 0 开始的。
    # 例如：PDF的第1页索引是 0，第2页索引是 1。
    # (起始索引, 结束索引) - 包含结束索引所在页
    # ==========================================
    page_mapping = {
        "强制执行申请书.pdf": (5, 5),      
        "被执行人身份证.pdf": (14, 14),      
        "授权委托书.pdf": (13, 13),      
        "送达地址确认书.pdf": (11, 11),    
        "银行账户确认书.pdf": (10, 10),   
        "纳入失信申请书.pdf": (9, 9),   
        "限高申请书.pdf": (8, 8),       
    }

    # 开始执行拆解
    for output_name, (start_idx, end_idx) in page_mapping.items():
        # 边界检查，防止页码配置超出实际文件总页数
        if start_idx >= total_pages or end_idx >= total_pages or start_idx > end_idx:
            print(f"⚠️ 跳过 {output_name}：配置的页码 ({start_idx}-{end_idx}) 越界或无效。")
            continue

        writer = PdfWriter()
        
        # 将指定范围内的页面加入到 Writer 中
        for i in range(start_idx, end_idx + 1):
            writer.add_page(reader.pages[i])

        # 拼接输出路径并保存文件
        output_path = os.path.join(output_dir, output_name)
        try:
            with open(output_path, "wb") as output_file:
                writer.write(output_file)
            print(f"✅ 成功生成: {output_name}")
        except Exception as e:
            print(f"❌ 写入 {output_name} 失败: {e}")


def find_and_split_all(target_filename="强制执行申请材料.pdf"):
    """
    在当前目录及一级子目录中查找目标PDF文件并拆分。
    拆分后的文件会生成在各自PDF所在的同级目录下。
    """
    current_dir = os.getcwd()
    processed = 0
    
    # 1. 检查当前目录
    current_file = os.path.join(current_dir, target_filename)
    if os.path.exists(current_file):
        print(f"\n{'='*50}")
        print(f"🔍 在当前目录发现目标文件: {current_file}")
        split_execution_documents(current_file)
        processed += 1
    
    # 2. 遍历一级子目录
    for entry in os.listdir(current_dir):
        entry_path = os.path.join(current_dir, entry)
        # 只处理文件夹，跳过文件
        if os.path.isdir(entry_path):
            sub_file = os.path.join(entry_path, target_filename)
            if os.path.exists(sub_file):
                print(f"\n{'='*50}")
                print(f"🔍 在子目录发现目标文件: {sub_file}")
                split_execution_documents(sub_file)
                processed += 1
    
    print(f"\n{'='*50}")
    if processed > 0:
        print(f"🎉 任务完成！共处理 {processed} 个文件。")
    else:
        print(f"⚠️ 未找到任何名为 '{target_filename}' 的文件。")


if __name__ == "__main__":
    print("🚀 开始扫描当前目录及一级子目录中的 PDF...")
    find_and_split_all()