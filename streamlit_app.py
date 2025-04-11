import streamlit as st
from io import BytesIO
import pypandoc
from num2words import num2words  # 用于将数字转换为英文大写
from datetime import datetime
import pandoc  # PyMuPDF
import os
from PyPDF2 import PdfReader, PdfWriter

def fill_pdf(data,text_parts):
    pdf = fitz.open("Late Notice.pdf")

    for page_num in range(len(pdf)):
        page = pdf[page_num]
        for key, value in data.items():
            value = str(value)  # 确保值是字符串
            search_term = f"{{{{{key}}}}}"  # 占位符格式

            # 查找占位符位置
            matches = page.search_for(search_term)
            for match in matches:
                rect = match  # 获取占位符的矩形区域
                # 用白色矩形覆盖占位符区域
                page.draw_rect(rect, color=(1, 1, 1), fill=(1, 1, 1))
                is_bold = False
                is_underlined = False

                for part in text_parts:
                    if part[0] == key:
                        is_bold = part[1]
                        is_underlined = part[2]
                fontname = "Times-Bold" if is_bold else "Times-Roman"

                # 插入新的文本，确保字体大小适应
                page.insert_text(
                    (rect.x0,rect.y1-2.5),  # 插入文本的位置是占位符的左上角
                    value,
                    fontsize=12,  # 自动计算的字体大小
                    fontname=fontname,  # 字体名称
                    color=(0, 0, 0)  # 黑色文本
                )
                if is_underlined:
                    text_width = fitz.get_text_length(value, fontsize=12, fontname=fontname)
                    underline_y = rect.y1   # 下划线稍微低于文本基线
                    page.draw_line(
                        (rect.x0, underline_y),  # 起点
                        (rect.x0 + text_width, underline_y),  # 终点
                        color=(0, 0, 0),  # 黑色线条
                        width=1.5  # 下划线宽度
                    )

    # 保存修改后的 PDF
    buffer = BytesIO()
    pdf.save(buffer)
    buffer.seek(0)  # 重置缓冲区指针
    pdf.close()
    return buffer

# Function to merge PDFs
def merge_pdfs(generated_pdf, uploaded_pdf):
    writer = PdfWriter()

    # Add pages from the generated PDF
    generated_reader = PdfReader(generated_pdf)
    for page in generated_reader.pages:
        writer.add_page(page)

    # Add pages from the uploaded PDF
    uploaded_reader = PdfReader(uploaded_pdf)
    for page in uploaded_reader.pages:
        writer.add_page(page)

    # Save the merged PDF to a BytesIO buffer
    output_buffer = BytesIO()
    writer.write(output_buffer)
    output_buffer.seek(0)
    return output_buffer



# Streamlit 界面
st.title("Late Notice Generator")
last_name = st.text_input("Last Name")
full_name = st.text_input("Full Name")
st.caption("Format:Last Name,First Name(Ex:Di,Zhongyue)")
address = st.text_area("Address")
st.caption("1138 W 38th St - Rm 3 (Do not include city,state or post code)")
postal = st.text_input("Postal Code")
title = st.selectbox("Title", ["Mr.", "Ms."])
amount = st.number_input("Amount", min_value=0.0, format="%.2f")
formatted_amount = "{:,.2f}".format(amount)
uploaded_file = st.file_uploader("Upload Tenant Ledger", type="pdf")

import inflect

def format_amount_in_words(amount):
    """
    将金额格式化为英文形式，并转换为单词形式。 
    例如 1234.56 转换为 'One Thousand Two Hundred Thirty-Four Dollars and 56/100 Cents'
    
    :param amount: float, 输入的金额
    :return: str, 格式化后的金额字符串
    """
    p = inflect.engine()

    # 拆分整数部分和小数部分
    dollars = int(amount)
    cents = int(round((amount - dollars) * 100))

    # 将整数部分转化为英文单词
    dollar_words = p.number_to_words(dollars).replace(",", "")  # 移除逗号
    
    # 将金额转换为每个单词首字母大写
    dollar_words = dollar_words.title()  # 移除逗号
    
    # 创建最终格式化字符串
    if cents == 0:
        return f"{dollar_words} Dollars"
    else:
        return f"{dollar_words} Dollars and {cents}/100 Cents"
amount_word = format_amount_in_words(amount)        
def amount_to_words(amount):
    return num2words(amount, to='currency', lang='en', currency ='USD').title()
amount_words = amount_to_words(amount)

def get_current_date():
    now = datetime.now()
    return now.strftime("%B %d, %Y")
current_date = get_current_date()
    
data = {
    "Full Name": full_name,
    "Last Name": last_name,
    "Address": address,
    "Postal": postal,
    "gen": title,
    "Amount Words":f"{current_date} is {amount_word} (${str(formatted_amount)}).",
    "Date":current_date,
    "DateB":f"{current_date} for your reference.",
    "Full Address":f"{address}, Los Angeles, CA, {postal}",
    "gender": f"{title}{last_name},"
}

text_parts = [
    ("Full Name", False, False),
    ("Last Name", False, False),
    ("Address", False, False),
    ("Postal", False, False),
    ("Amount Words", True, True),
    ("Date", False, False),
    ("DateB", False, False),
    ("Full Address", True, False),
    ("gender", False, False),
]

# 生成 PDF
if st.button("生成 PDF"):
    if not uploaded_file:
        st.warning("Please upload a PDF to merge.")
    else:
        # Generate filled PDF
        generated_pdf = fill_pdf(data, text_parts)
        merged_pdf = merge_pdfs(generated_pdf, uploaded_file)
        st.success("PDF 生成成功！")
        st.download_button(
            label="Download Merged PDF",
            data=merged_pdf,
            file_name=f"Late Notice - {full_name}.pdf",
            mime="application/pdf",
        )
