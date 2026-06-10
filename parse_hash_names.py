# -*- coding: utf-8 -*-
"""
解析 source-data/ 下的所有 xlsx，建立 hash filename → content_name 映射
输出: hash_name_map.json
"""

import os, json, sys, re

SOURCE_DATA = r'E:\kkb-course\source-data'
MEDIA_DIR   = r'E:\kkb-course\media'
OUTPUT      = r'D:\workspace\course_resource\hash_name_map.json'

def parse_all_xlsx():
    import openpyxl

    # media 下的实际文件
    media_files = set()
    for f in os.listdir(MEDIA_DIR):
        if f.endswith(('.mp4', '.m4v')):
            # 去掉扩展名，匹配时忽略
            name_no_ext = os.path.splitext(f)[0]
            media_files.add(name_no_ext)

    print(f"media/ 下视频文件: {len(media_files)}")

    # 解析所有 xlsx
    xlsx_files = [f for f in os.listdir(SOURCE_DATA) if f.endswith('.xlsx')]
    print(f"source-data/ 下 xlsx: {len(xlsx_files)}")

    hash_map = {}      # hash -> {title, course_name, course_id, content_id}
    course_map = {}    # course_id -> course_name (from filename)
    matched = 0
    unmatched = 0

    for i, xf in enumerate(xlsx_files):
        # 从文件名解析 course_id 和 course_name
        # 格式: 210069-百度飞桨联合设计双证资深ai实战工程师-nlp方向.xlsx
        basename = os.path.splitext(xf)[0]
        parts = basename.split('-', 1)
        course_id = parts[0]
        course_name = parts[1] if len(parts) > 1 else course_id
        course_map[course_id] = course_name

        filepath = os.path.join(SOURCE_DATA, xf)
        try:
            wb = openpyxl.load_workbook(filepath, data_only=True)
            ws = wb.active
        except Exception:
            continue

        for row in ws.iter_rows(min_row=2, values_only=True):
            if not row[4]:  # 视频文件名称列
                continue
            content_id   = str(row[0]) if row[0] else ''
            content_name = str(row[1]) if row[1] else ''
            hash_path    = str(row[4])  # e.g., source/media-842888865873922//EEE00B0F...

            # 提取 hash 部分
            hash_name = re.sub(r'^.*//', '', hash_path)
            hash_name = os.path.splitext(hash_name)[0]  # 去扩展名

            if hash_name and content_name:
                hash_map[hash_name] = {
                    'title': content_name,
                    'course_name': course_name,
                    'course_id': course_id,
                    'content_id': content_id,
                }

        if (i + 1) % 200 == 0:
            print(f"  进度: {i+1}/{len(xlsx_files)}  (已映射 {len(hash_map)} 条)")

    # 统计匹配
    for h in hash_map:
        if h in media_files:
            matched += 1
        else:
            unmatched += 1

    print(f"\n映射条目: {len(hash_map)}")
    print(f"  在 media/ 中找到: {matched}")
    print(f"  不在 media/ 中: {unmatched} (可能未下载)")
    print(f"课程数: {len(course_map)}")

    # 保存
    result = {
        'hash_map': hash_map,
        'course_map': course_map,
    }
    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False)
    print(f"\n已保存: {OUTPUT}")

if __name__ == '__main__':
    parse_all_xlsx()
