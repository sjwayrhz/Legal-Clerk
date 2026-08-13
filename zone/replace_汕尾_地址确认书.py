import os
import re
import fitz  # PyMuPDF

def process_pdfs():
    # 模板文件名称
    template_filename = "汕尾_被执行人送达地址及相关信息确认书.pdf"
    
    if not os.path.exists(template_filename):
        print(f"错误: 找不到模板文件 '{template_filename}'，请确保将其放在脚本同级目录。")
        return

    # 遍历当前目录下的所有文件夹
    for root, dirs, files in os.walk("."):
        for file in files:
            if file == "强制执行申请书.pdf":
                apply_pdf_path = os.path.join(root, file)
                print(f"\n正在处理: {apply_pdf_path}")
                
                try:
                    # 1. 读取强制执行申请书并提取文本
                    text = ""
                    with fitz.open(apply_pdf_path) as doc:
                        for page in doc:
                            text += page.get_text()
                    
                    # 去除换行符，方便正则表达式匹配
                    text_no_newlines = text.replace('\n', '').replace('\r', '')
                    
                    # 2. 正则提取被执行人信息
                    name_match = re.search(r"被执行人[:：]\s*(.*?)[,，]", text_no_newlines)
                    id_match = re.search(r"身份证号[:：]\s*([0-9Xx]{18})", text_no_newlines)
                    address_match = re.search(r"住\s*(.*?)[,，]身份证号", text_no_newlines)
                    phone_match = re.search(r"联系电话[:：]\s*(\d{11})", text_no_newlines)
                    
                    if name_match:
                        name = name_match.group(1).strip()
                        id_card = id_match.group(1).strip() if id_match else ""
                        address = address_match.group(1).strip() if address_match else ""
                        phone = phone_match.group(1).strip() if phone_match else ""
                        
                        print(f"提取成功 -> 姓名: {name}, 身份证: {id_card}")
                        
                        # 3. 打开确认书模板，动态填写信息
                        out_doc = fitz.open(template_filename)
                        page = out_doc[0]
                        
                        # 加载系统自带字体解决数字间距问题
                        fontname = "myfont"
                        fontsize = 12
                        color = (0, 0, 0)
                        
                        font_paths = [
                            "C:/Windows/Fonts/simfang.ttf", # 仿宋 (首选)
                            "C:/Windows/Fonts/simsun.ttc",  # 宋体 (备用)
                            "C:/Windows/Fonts/msyh.ttf",    # 微软雅黑 (备用)
                        ]
                        
                        font_loaded = False
                        for fp in font_paths:
                            if os.path.exists(fp):
                                page.insert_font(fontname=fontname, fontfile=fp)
                                font_loaded = True
                                break
                                
                        if not font_loaded:
                            print("  [警告] 未找到系统本地字体，将使用内置字体。")
                            fontname = "china-ss"

                        # 动态定位写入函数 (修复错位漏填)
                        def insert_text_next_to(keyword, text_to_insert, x_offset=30):
                            rects = page.search_for(keyword)
                            
                            # 【核心修复】：过滤掉顶部大标题 (y0 > 150)
                            # 并放宽横坐标限制 (x0 < 250)，确保能扫到右侧的表单标签
                            valid_rects = [r for r in rects if r.y0 > 150 and r.x0 < 250]
                            
                            if valid_rects:
                                # 按 Y 坐标从上到下排序，取第一个
                                valid_rects.sort(key=lambda r: r.y0)
                                rect = valid_rects[0] 
                                
                                insert_x = rect.x1 + x_offset
                                insert_y = rect.y1 - 2 
                                page.insert_text((insert_x, insert_y), text_to_insert, fontsize=fontsize, fontname=fontname, color=color)
                            else:
                                print(f"  [提示] 模板表单区未找到锚点词: {keyword}")

                        # 开始填入数据
                        insert_text_next_to("被执行人", name, x_offset=30)
                        insert_text_next_to("身份证号码", id_card, x_offset=30)
                        insert_text_next_to("户籍地", address, x_offset=30)
                        insert_text_next_to("电话", phone, x_offset=30)
                        insert_text_next_to("送达地址", address, x_offset=30)
                        
                        # 最后一个电话（增加偏移量，避免和冒号重叠）
                        insert_text_next_to("送达地址电话", phone, x_offset=35)
                        
                        # 4. 保存文件
                        out_filename = f"{name}_被执行人送达地址及相关信息确认书.pdf"
                        out_filepath = os.path.join(root, out_filename)
                        
                        out_doc.save(out_filepath)
                        out_doc.close()
                        print(f"已生成: {out_filepath}")
                    else:
                        print(f"警告: 在 {apply_pdf_path} 中未能匹配到被执行人信息。")
                        
                except Exception as e:
                    print(f"处理 {apply_pdf_path} 时发生错误: {e}")

if __name__ == "__main__":
    process_pdfs()
    print("\n全部处理完毕！")