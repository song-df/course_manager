# -*- coding: utf-8 -*-
"""
Course Data Generator — 配置驱动的课程数据生成器

用法:
    python generate_course_data.py

配置:
    编辑 courses_config.json 定义课程和章节，然后运行此脚本重新生成 course_data.json。

添加新课只需两步：
    1. 在 courses_config.json 的 "courses" 数组里添加一个课程条目
    2. 运行 python generate_course_data.py
"""

import os
import json
import shutil
from datetime import datetime

CONFIG_FILE = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'courses_config.json')
OUTPUT      = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'course_data.json')


def load_config():
    with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
        return json.load(f)


def scan_chapter(path):
    """扫描章节目录，返回视频文件列表（排除 ._ 前缀和小于 5KB 的文件）"""
    videos = []
    if not os.path.exists(path):
        return videos
    for f in sorted(os.listdir(path)):
        if f.startswith('._'):
            continue
        if f.endswith(('.mp4', '.m4v', '.mov')):
            full = os.path.join(path, f)
            try:
                size = os.path.getsize(full)
            except OSError:
                continue
            if size < 5000:  # macOS 资源分支文件
                continue
            videos.append({
                "name": os.path.splitext(f)[0],
                "file": full,
                "size": size,
                "size_str": f"{size / 1024 / 1024:.1f}MB"
            })
    return videos


def resolve_source(base_dir, chapter_cfg, course_source):
    """
    确定章节的源目录。
    优先级: 章节级 source > 课程级 source > base_dir
    支持绝对路径（如 E盘:\\目录名）和相对路径（相对 base_dir）
    """
    source_name = chapter_cfg.get('source') or course_source
    if source_name:
        # 绝对路径直接使用
        if os.path.isabs(source_name) and os.path.exists(source_name):
            return source_name
        # 相对路径：相对于 base_dir
        candidate = os.path.join(base_dir, source_name)
        if os.path.exists(candidate):
            return candidate
        alt = os.path.join(base_dir, source_name + '转')
        if os.path.exists(alt):
            return alt
        return candidate  # 即使不存在也返回，后续 scan_chapter 会处理
    return base_dir


def resolve_folder(source_dir, folder_name):
    """
    在 source_dir 中查找章节文件夹。
    尝试多种可能的命名变体: 原始名称、带"第N章"前缀、带"转"后缀
    """
    candidates = [
        os.path.join(source_dir, folder_name),
        os.path.join(source_dir, folder_name + '转'),
    ]
    # 如果 folder 是纯数字如 "1"、"7"，也尝试 "第1章"、"第7章"
    if folder_name.isdigit():
        candidates.insert(1, os.path.join(source_dir, f'第{folder_name}章'))

    for c in candidates:
        if os.path.exists(c):
            return c
    return candidates[0]


def safe_id(name):
    """将目录名转换为 URL 安全的 ID"""
    import re
    slug = re.sub(r'[^\w一-鿿]', '-', name)
    slug = re.sub(r'-+', '-', slug).strip('-')
    return slug or 'course'


def build_course_from_dir(course_cfg, source_dir):
    """从指定目录构建课程（跳过 source 解析，直接使用给定路径）"""
    course = {
        "id": course_cfg["id"],
        "title": course_cfg["title"],
        "subtitle": course_cfg.get("subtitle", ""),
        "description": course_cfg.get("description", ""),
        "wiki_doc": course_cfg.get("wiki_doc", ""),
        "chapters": [],
        "total_videos": 0
    }

    def add_chapter(ch_id, ch_title, videos):
        if videos:
            course["chapters"].append({
                "id": ch_id,
                "title": ch_title,
                "description": "",
                "videos": videos,
                "count": len(videos)
            })
            course["total_videos"] += len(videos)

    # 扫描顶层：子目录 + 平铺视频
    subdirs = []
    flat_videos = []
    for name in sorted(os.listdir(source_dir)):
        path = os.path.join(source_dir, name)
        if os.path.isdir(path) and not name.startswith('.') and not name.startswith('__'):
            subdirs.append((name, path))
        elif os.path.isfile(path) and (name.endswith('.mp4') or name.endswith('.m4v')) and not name.startswith('._'):
            flat_videos.append(path)

    # 检测深度：如果子目录里还有子目录（深度 2），展开为章节
    depth2_chapters = []
    for sd_name, sd_path in subdirs:
        sd_videos = scan_chapter(sd_path)  # 该子目录下的平铺视频
        sd_subdirs = [d for d in sorted(os.listdir(sd_path))
                      if os.path.isdir(os.path.join(sd_path, d))
                      and not d.startswith('.') and not d.startswith('__')]

        if sd_subdirs:
            # 深度 2：子目录的子目录作为章节
            for d2_name in sd_subdirs:
                d2_path = os.path.join(sd_path, d2_name)
                d2_videos = scan_chapter(d2_path)
                if d2_videos:
                    d2_flat = scan_chapter(os.path.join(sd_path, d2_name))
                    depth2_chapters.append((d2_name, d2_name, d2_videos))
            # 同时保留子目录本身的平铺视频
            if sd_videos:
                depth2_chapters.append((sd_name, sd_name, sd_videos))
        else:
            # 深度 1：子目录即为章节
            if sd_videos:
                depth2_chapters.append((sd_name, sd_name, sd_videos))
            elif not any(os.path.isfile(os.path.join(sd_path, f)) for f in os.listdir(sd_path) if not f.startswith('.')):
                pass  # 空目录或只有子目录（已在上面的 sd_subdirs 处理）
            else:
                pass  # 有非视频文件的目录，跳过

    # 使用深度展开的章节
    for ch_id, ch_title, ch_videos in depth2_chapters:
        add_chapter(ch_id, ch_title, ch_videos)

    # 顶层平铺视频（如素材目录）
    if flat_videos:
        flat_info = []
        for fp in sorted(flat_videos):
            fname = os.path.basename(fp)
            try:
                size = os.path.getsize(fp)
            except OSError:
                continue
            if size < 5000:
                continue
            flat_info.append({
                "name": os.path.splitext(fname)[0],
                "file": fp,
                "size": size,
                "size_str": f"{size / 1024 / 1024:.1f}MB"
            })
        if flat_info:
            course["chapters"].append({
                "id": "_root_",
                "title": "课程视频",
                "description": "",
                "videos": flat_info,
                "count": len(flat_info)
            })
            course["total_videos"] += len(flat_info)

    # 如果什么都没找到，尝试直接把 source_dir 下的平铺视频作为"全部视频"
    if not course["chapters"]:
        all_videos = scan_chapter(source_dir)
        if all_videos:
            add_chapter("_all_", "全部视频", all_videos)

    return course


def build_course(course_cfg, base_dir):
    """根据配置构建单个课程数据"""
    course = {
        "id": course_cfg["id"],
        "title": course_cfg["title"],
        "subtitle": course_cfg.get("subtitle", ""),
        "description": course_cfg.get("description", ""),
        "wiki_doc": course_cfg.get("wiki_doc", ""),
        "chapters": [],
        "total_videos": 0
    }

    course_source = course_cfg.get("source")
    chapters_cfg = course_cfg.get("chapters", [])

    # ---- 自动探测模式：未配置 chapters 则自动扫描子目录 ----
    if not chapters_cfg:
        source_dir = resolve_source(base_dir, {}, course_source)
        if os.path.exists(source_dir):
            # 扫描子目录作为章节
            for folder_name in sorted(os.listdir(source_dir)):
                folder_path = os.path.join(source_dir, folder_name)
                if not os.path.isdir(folder_path):
                    continue
                # Skip macOS resource forks and hidden dirs
                if folder_name.startswith('.') or folder_name.startswith('__'):
                    continue
                videos = scan_chapter(folder_path)
                if videos:
                    course["chapters"].append({
                        "id": folder_name,
                        "title": folder_name,
                        "description": "",
                        "videos": videos,
                        "count": len(videos)
                    })
                    course["total_videos"] += len(videos)

            # 如果没找到子目录章节，检查课程目录下是否有平铺的视频文件
            if not course["chapters"]:
                flat_videos = scan_chapter(source_dir)
                if flat_videos:
                    course["chapters"].append({
                        "id": "_all_",
                        "title": "全部视频",
                        "description": "",
                        "videos": flat_videos,
                        "count": len(flat_videos)
                    })
                    course["total_videos"] += len(flat_videos)

    # ---- 手动配置模式：按配置的章节列表扫描 ----
    else:
        for ch_cfg in chapters_cfg:
            source_dir = resolve_source(base_dir, ch_cfg, course_source)
            folder_path = resolve_folder(source_dir, ch_cfg["folder"])
            videos = scan_chapter(folder_path)

            if videos:
                course["chapters"].append({
                    "id": ch_cfg["folder"],
                    "title": ch_cfg.get("title", ch_cfg["folder"]),
                    "description": ch_cfg.get("description", ""),
                    "videos": videos,
                    "count": len(videos)
                })
                course["total_videos"] += len(videos)

    return course


def main():
    # ---- 自动备份现有数据 ----
    if os.path.exists(OUTPUT):
        backup_dir = os.path.join(os.path.dirname(OUTPUT), 'backups')
        os.makedirs(backup_dir, exist_ok=True)
        ts = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(backup_dir, f'course_data_{ts}.json')
        shutil.copy2(OUTPUT, backup_path)
        print(f"[备份] {OUTPUT} -> {backup_path}")

    config = load_config()
    base_dir = config["base_dir"]

    courses = []
    for cc in config.get("courses", []):
        # ---- 自动发现模式：source 下每个子目录变成一门课 ----
        if cc.get("auto_discover"):
            source_name = cc.get("source", "")
            # 支持绝对路径
            if os.path.isabs(source_name):
                source_dir = source_name
            else:
                source_dir = os.path.join(base_dir, source_name)
            if os.path.exists(source_dir):
                for folder_name in sorted(os.listdir(source_dir)):
                    folder_path = os.path.join(source_dir, folder_name)
                    if not os.path.isdir(folder_path):
                        continue
                    if folder_name.startswith('.') or folder_name.startswith('__'):
                        continue
                    # 为每个子目录生成课程配置，加源前缀避免 ID 冲突
                    src_prefix = safe_id(os.path.basename(source_dir.rstrip('\\/')))[:8]
                    auto_cfg = {
                        "id": f"{src_prefix}-{safe_id(folder_name)}",
                        "title": folder_name,
                        "subtitle": f"来自 {source_name}",
                        "description": "",
                        "chapters": [],  # 触发自动探测
                    }
                    # 直接在这里构建，传入 folder_path 作为 source_dir
                    c = build_course_from_dir(auto_cfg, folder_path)
                    if c["total_videos"] > 0:
                        courses.append(c)
            continue

        c = build_course(cc, base_dir)
        if c["total_videos"] > 0:
            courses.append(c)

    with open(OUTPUT, 'w', encoding='utf-8') as f:
        json.dump(courses, f, ensure_ascii=False, indent=2)

    print(f"[OK] {OUTPUT}")
    print(f"     {len(courses)} 门课程")
    for c in courses:
        print(f"     {c['title']}: {c['total_videos']} 个视频, {len(c['chapters'])} 个章节")


if __name__ == '__main__':
    main()
