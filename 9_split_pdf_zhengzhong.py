import os
from PyPDF2 import PdfReader, PdfWriter
import win32com.client

# =========强制锁定工作目录为脚本所在位置，根治右键运行失败==========
SCRIPT_PATH = os.path.abspath(__file__)
BASE_WORK_DIR = os.path.dirname(SCRIPT_PATH)
os.chdir(BASE_WORK_DIR)
print(f"✅ 已锁定程序根目录：{BASE_WORK_DIR}")


def create_windows_shortcut(shortcut_save_path, target_folder_path):
    """
    创建Windows文件夹快捷方式(.lnk)
    :param shortcut_save_path: 快捷方式完整保存路径
    :param target_folder_path: 快捷方式指向的目标文件夹
    """
    try:
        if not os.path.isdir(target_folder_path):
            print(f"⚠️ 目标文件夹不存在 {target_folder_path}，跳过该快捷方式")
            return False

        shell = win32com.client.Dispatch("WScript.Shell")
        shortcut = shell.CreateShortCut(shortcut_save_path)
        shortcut.TargetPath = target_folder_path
        shortcut.WorkingDirectory = target_folder_path
        shortcut.Save()
        print(f"✅ 目录内生成快捷方式：{shortcut_save_path}")
        return True
    except Exception as e:
        print(f"❌ 创建快捷方式失败 {shortcut_save_path}：{str(e)}")
        return False

def split_execution_documents(input_pdf_path):
    # 检查输入文件是否存在
    if not os.path.exists(input_pdf_path):
        print(f"❌ 未找到文件: {input_pdf_path}")
        return
    
    # 当前PDF所在目录，快捷方式将生成在此目录
    work_dir = os.path.dirname(os.path.abspath(input_pdf_path))
    output_dir = work_dir

    # 初始化 PDF 读取器
    try:
        reader = PdfReader(input_pdf_path)
        total_pages = len(reader.pages)
        print(f"📄 成功加载文档，总页数: {total_pages}")
    except Exception as e:
        print(f"❌ 读取 PDF 失败: {e}")
        return

    # 分页配置
    page_mapping = {
        "强制执行申请书.pdf": (8, 9),      
        "被执行人身份证.pdf": (14, 15),      
        "授权委托书.pdf": (13, 13),      
        "送达地址和行账户确认书.pdf": (12, 12),    
        "纳入失信申请书.pdf": (11, 11),   
        "限高申请书.pdf": (10, 10),       
    }

    # 执行PDF拆分
    for output_name, (start_idx, end_idx) in page_mapping.items():
        if start_idx >= total_pages or end_idx >= total_pages or start_idx > end_idx:
            print(f"⚠️ 跳过 {output_name}：页码越界无效")
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

    # ========== 拆分完成后，在当前PDF所在目录生成两个快捷方式 ==========
    print(f"\n🔗 在本目录 {work_dir} 创建指定快捷方式")
    # 快捷1：申请人身份材料
    lnk1 = os.path.join(work_dir, "申请人身份材料.lnk")
    target1 = r"D:\sync\申请人身份材料"
    create_windows_shortcut(lnk1, target1)

    # 快捷2：授权委托书
    lnk2 = os.path.join(work_dir, "授权委托书.lnk")
    target2 = r"D:\sync\授权委托书"
    create_windows_shortcut(lnk2, target2)
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
        print(f"🎉 全部任务完成！共处理 {processed} 个PDF文件，每个处理目录均生成对应快捷方式")
    else:
        print(f"⚠️ 未找到任何名为 '{target_filename}' 的PDF文件")


if __name__ == "__main__":
    try:
        print("🚀 开始扫描当前目录及一级子目录中的强制执行申请材料.pdf")
        find_and_split_all()
    except Exception as err:
        print(f"程序异常：{err}")
    # 阻止控制台双击之后直接闪退
    input("\n按下回车键关闭窗口")