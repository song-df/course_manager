# -*- coding: utf-8 -*-
"""
给不规范命名的视频生成可读名称
用法: python normalize_names.py [--apply]

基于课程名 + 章节名 + 序号，替换 hash/数字 文件名
  --dry-run  只预览，不实际修改
  --apply    写入 course_data.json
"""

import os, json, sys, re

COURSE_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'course_data.json')
BACKUP      = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'course_data.backup.json')

HASH_PATTERN  = re.compile(r'^[0-9A-Fa-f]{20,}')
NUM_PATTERN   = re.compile(r'^[0-9_]+$')
SHORT_PATTERN = re.compile(r'^.{0,5}$')

def is_bad(name):
    return bool(HASH_PATTERN.match(name) or NUM_PATTERN.match(name) or SHORT_PATTERN.match(name))

def main():
    with open(COURSE_DATA, 'r', encoding='utf-8') as f:
        courses = json.load(f)

    # 统计
    changes = []
    total_bad = 0
    for c in courses:
        for ch in c.get('chapters', []):
            bad_in_chapter = [(i, v) for i, v in enumerate(ch['videos']) if is_bad(v['name'])]
            if not bad_in_chapter:
                continue
            total_bad += len(bad_in_chapter)
            course_title = c['title']
            chapter_title = ch['title']

            for idx, (vi, v) in enumerate(bad_in_chapter):
                old_name = v['name']
                # 生成新名：课程名截取 + 章节名截取 + 序号
                short_course = re.sub(r'[^\w一-鿿]', '', course_title)[:20]
                short_chapter = re.sub(r'[^\w一-鿿]', '', chapter_title)[:15]
                new_name = f"{short_course} - {short_chapter} - {idx+1:03d}"

                changes.append({
                    'course_id': c['id'],
                    'course': course_title[:50],
                    'chapter': chapter_title[:40],
                    'old': old_name,
                    'new': new_name,
                    'video_index': vi,
                })

    print(f"不规范视频: {total_bad} -> 将改为 \"课程名 - 章节 - 编号\" 格式")
    print()

    if '--dry-run' in sys.argv or '--apply' not in sys.argv:
        print("[预览] 前 20 条:")
        for chg in changes[:20]:
            print(f"  [{chg['course']}] {chg['chapter']}")
            print(f"    {chg['old'][:50]}")
            print(f" -> {chg['new']}")
        if len(changes) > 20:
            print(f"  ... 共 {len(changes)} 条")
        print()
        print("确认后执行: python normalize_names.py --apply")
        return

    # --apply: 写入
    # 备份
    with open(BACKUP, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    print(f"已备份: {BACKUP}")

    # 应用改名
    for chg in changes:
        cid = chg['course_id']
        vi = chg['video_index']
        for c in courses:
            if c['id'] == cid:
                for ch in c['chapters']:
                    if vi < len(ch['videos']) and ch['videos'][vi]['name'] == chg['old']:
                        ch['videos'][vi]['name'] = chg['new']
                        break

    with open(COURSE_DATA, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)
    print(f"已更新: {COURSE_DATA}")
    print(f"共改名 {len(changes)} 个视频")

if __name__ == '__main__':
    main()
