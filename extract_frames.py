# -*- coding: utf-8 -*-
"""
视频帧提取工具 — 分批对不规范命名的视频提取关键帧

用法:
  python extract_frames.py --dry-run         预览全部
  python extract_frames.py --batch 1          处理第1批（共10批）
  python extract_frames.py --batch 1 --dry-run 预览第1批
  python extract_frames.py --status           查看各批次完成状态
"""

import os, json, subprocess, sys, re, math

FFMPEG     = r'D:\workspace\ffmpeg\bin\ffmpeg.exe'
COURSE_DATA = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'course_data.json')
FRAME_DIR   = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frames')
BATCHES     = 10

HASH_PATTERN  = re.compile(r'^[0-9A-Fa-f]{20,}')
NUM_PATTERN   = re.compile(r'^[0-9_]+$')
SHORT_PATTERN = re.compile(r'^.{0,5}$')

def is_bad_name(name):
    return bool(HASH_PATTERN.match(name) or NUM_PATTERN.match(name) or SHORT_PATTERN.match(name))

def extract_frame(video_path, output_path, position='00:01:00'):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if os.path.exists(output_path) and os.path.getsize(output_path) > 500:
        return 'skip'
    try:
        subprocess.run([
            FFMPEG, '-y', '-ss', position, '-i', video_path,
            '-vframes', '1', '-q:v', '3', '-loglevel', 'error',
            output_path
        ], timeout=30, check=True)
        return 'ok'
    except Exception:
        return 'fail'

def load_bad_videos():
    with open(COURSE_DATA, 'r', encoding='utf-8') as f:
        courses = json.load(f)
    bad = []
    for c in courses:
        for ch in c.get('chapters', []):
            for v in ch.get('videos', []):
                if is_bad_name(v['name']):
                    bad.append({
                        'course': c['title'][:50],
                        'course_id': c['id'],
                        'chapter': ch['title'][:50],
                        'name': v['name'],
                        'file': v['file'],
                        'size_mb': v.get('size', 0) / 1024 / 1024
                    })
    return bad

def get_batch(videos, n):
    """返回第 n 批（1-based）的视频列表"""
    per_batch = math.ceil(len(videos) / BATCHES)
    start = (n - 1) * per_batch
    end = min(start + per_batch, len(videos))
    return videos[start:end]

def count_existing(videos):
    """统计某批已提取的帧数"""
    n = 0
    for v in videos:
        safe_name = re.sub(r'[<>:"/\\|?*]', '_', v['name'])[:60]
        frame_path = os.path.join(FRAME_DIR, v['course_id'], v['chapter'][:30], safe_name + '.jpg')
        if os.path.exists(frame_path) and os.path.getsize(frame_path) > 500:
            n += 1
    return n

def print_batch_info(batch_num, videos):
    batch = get_batch(videos, batch_num)
    done = count_existing(batch)
    total_gb = sum(v['size_mb'] for v in batch) / 1024
    print(f"--- Batch {batch_num}/{BATCHES} ---")
    print(f"  Videos: {len(batch)}  ({done} done)")
    print(f"  Size:   {total_gb:.1f} GB")
    from collections import Counter
    cnt = Counter(v['course'] for v in batch)
    for course, n in cnt.most_common():
        print(f"    {n:4d}  {course}")
    print()

def main():
    videos = load_bad_videos()

    # --status: 查看各批次状态
    if '--status' in sys.argv:
        print(f"Total: {len(videos)} videos  Batches: {BATCHES}")
        total_gb = sum(v['size_mb'] for v in videos) / 1024
        total_done = count_existing(videos)
        print(f"Size: {total_gb:.1f} GB  Done: {total_done}/{len(videos)}")
        print()
        for n in range(1, BATCHES + 1):
            batch = get_batch(videos, n)
            done = count_existing(batch)
            pct = done * 100 // len(batch) if batch else 0
            bar = '█' * (pct // 10) + '░' * (10 - pct // 10)
            print(f"  Batch {n:2d}: {done:4d}/{len(batch):4d}  {pct:3d}%")
        return

    # 解析参数
    dry_run = '--dry-run' in sys.argv
    batch_arg = None
    for i, a in enumerate(sys.argv):
        if a == '--batch' and i + 1 < len(sys.argv):
            batch_arg = int(sys.argv[i + 1])

    if batch_arg is None:
        print("用法: python extract_frames.py --batch N  (N=1..10)")
        print("      python extract_frames.py --batch N --dry-run")
        print("      python extract_frames.py --status")
        sys.exit(1)

    batch = get_batch(videos, batch_arg)
    print_batch_info(batch_arg, videos)

    if dry_run:
        print("[dry-run] skip extraction")
        return

    success, skip, fail = 0, 0, 0
    for i, v in enumerate(batch):
        video_file = v['file']
        if not os.path.exists(video_file):
            fail += 1
            continue

        safe_name = re.sub(r'[<>:"/\\|?*]', '_', v['name'])[:60]
        frame_path = os.path.join(FRAME_DIR, v['course_id'], v['chapter'][:30], safe_name + '.jpg')

        result = extract_frame(video_file, frame_path, '00:01:00')
        if result == 'ok':
            success += 1
        elif result == 'skip':
            skip += 1
        else:
            fail += 1

        if (i + 1) % 50 == 0:
            print(f"  [{i+1}/{len(batch)}] ok={success} skip={skip} fail={fail}")

    print(f"Done: ok={success} skip={skip} fail={fail}")
    print(f"Frames: {FRAME_DIR}")

if __name__ == '__main__':
    main()
