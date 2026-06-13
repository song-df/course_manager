#!/usr/bin/env python3
"""
Course Resource Web Server - 智联学习云
Serves courses from the resource library with video streaming support.
"""

import json
import os
import mimetypes
import re
import sys
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import unquote

# Detect WSL
IN_WSL = 'WSL_DISTRO_NAME' in os.environ or os.path.exists('/proc/sys/fs/binfmt_misc/WSLInterop')

if IN_WSL:
    COURSE_DATA = '/mnt/d/workspace/course_resource/course_data.json'
    SERIES_CONFIG = '/mnt/d/workspace/course_resource/series_config.json'
    ROOT = '/mnt/d/workspace/course_resource'
else:
    COURSE_DATA = r'D:\workspace\course_resource\course_data.json'
    SERIES_CONFIG = r'D:\workspace\course_resource\series_config.json'
    ROOT = 'D:\\workspace\\course_resource'


def normalize_path(raw_path):
    """Convert any path format to the platform-native absolute path."""
    # Replace backslashes with forward slashes
    path = raw_path.replace('\\', '/')

    if IN_WSL:
        # Convert Windows drive letters to WSL /mnt/ paths
        # e.g., E:/kkb-course/... -> /mnt/e/kkb-course/...
        path = re.sub(r'^([A-Za-z]):/', lambda m: f'/mnt/{m.group(1).lower()}/', path)
    else:
        # On Windows, ensure backslashes
        path = path.replace('/', '\\')
    return path


class CourseHandler(SimpleHTTPRequestHandler):
    """Custom handler that serves course data API and video files."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=ROOT, **kwargs)

    def do_GET(self):
        # ---- API: course metadata ----
        if self.path == '/api/courses':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                with open(COURSE_DATA, 'r', encoding='utf-8') as f:
                    self.wfile.write(f.read().encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}).encode('utf-8'))
            return

        # ---- API: series metadata ----
        if self.path.startswith('/api/series'):
            self.send_response(200)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Access-Control-Allow-Origin', '*')
            self.end_headers()
            try:
                with open(SERIES_CONFIG, 'r', encoding='utf-8') as f:
                    series_config = json.load(f)
                with open(COURSE_DATA, 'r', encoding='utf-8') as f:
                    courses = json.load(f)

                from urllib.parse import urlparse, parse_qs
                qs = parse_qs(urlparse(self.path).query)
                series_id = qs.get('id', [None])[0]

                if series_id:
                    # 返回单个系列，填充课程详情
                    target = None
                    for s in series_config.get('series', []):
                        if s['id'] == series_id:
                            target = dict(s)
                            break
                    if target:
                        populated = []
                        for cid in target.get('courses', []):
                            for c in courses:
                                if c['id'] == cid:
                                    populated.append(c)
                                    break
                        target['courses'] = populated
                        # articles 字段原样透传（文章型内容）
                        self.wfile.write(json.dumps(target, ensure_ascii=False).encode('utf-8'))
                    else:
                        self.wfile.write(json.dumps({"error": "series not found"}, ensure_ascii=False).encode('utf-8'))
                else:
                    # 返回所有系列（不填充课程详情，只带统计）
                    result = []
                    for s in series_config.get('series', []):
                        item = dict(s)
                        course_list = []
                        total_videos = 0
                        for cid in s.get('courses', []):
                            for c in courses:
                                if c['id'] == cid:
                                    course_list.append(c)
                                    total_videos += c.get('total_videos', 0)
                                    break
                        # articles（文章型内容）也计入课程数
                        article_count = len(s.get('articles', []))
                        item['total_courses'] = len(course_list) + article_count
                        item['total_videos'] = total_videos
                        if 'courses' in item:
                            del item['courses']
                        result.append(item)
                    self.wfile.write(json.dumps(result, ensure_ascii=False).encode('utf-8'))
            except Exception as e:
                self.wfile.write(json.dumps({"error": str(e)}, ensure_ascii=False).encode('utf-8'))
            return

        # ---- API: video streaming ----
        if self.path.startswith('/api/video/'):
            raw = unquote(self.path[len('/api/video/'):])
            file_path = normalize_path(raw)

            if not os.path.exists(file_path):
                self.send_error(404, f"File not found")
                return

            file_size = os.path.getsize(file_path)
            content_type, _ = mimetypes.guess_type(file_path)
            if content_type is None:
                content_type = 'video/mp4'

            range_header = self.headers.get('Range')

            if range_header:
                # Parse Range header
                parts = range_header.strip().split('=')[-1].split('-')
                start = int(parts[0]) if parts[0] else 0
                end = int(parts[1]) if len(parts) > 1 and parts[1] else file_size - 1
                end = min(end, file_size - 1)
                length = end - start + 1

                self.send_response(206)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Range', f'bytes {start}-{end}/{file_size}')
                self.send_header('Content-Length', str(length))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()

                with open(file_path, 'rb') as f:
                    f.seek(start)
                    remaining = length
                    chunk = 524288  # 512KB — 视频流大块传输
                    while remaining > 0:
                        data = f.read(min(chunk, remaining))
                        if not data:
                            break
                        try:
                            self.wfile.write(data)
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            # Client disconnected (e.g., user clicked another video)
                            return
                        remaining -= len(data)
                return
            else:
                self.send_response(200)
                self.send_header('Content-Type', content_type)
                self.send_header('Content-Length', str(file_size))
                self.send_header('Accept-Ranges', 'bytes')
                self.send_header('Access-Control-Allow-Origin', '*')
                self.end_headers()
                with open(file_path, 'rb') as f:
                    chunk = 524288  # 512KB — 视频流大块传输
                    while True:
                        data = f.read(chunk)
                        if not data:
                            break
                        try:
                            self.wfile.write(data)
                        except (BrokenPipeError, ConnectionResetError, OSError):
                            # Client disconnected gracefully
                            return
                return

        # ---- Static files ----
        super().do_GET()

    def log_message(self, format, *args):
        import datetime
        now = datetime.datetime.now().strftime('%H:%M:%S')
        print(f"[{now}] {format % args}")


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8080, help='Port to listen on')
    args, _ = parser.parse_known_args()
    port = args.port

    mimetypes.add_type('video/mp4', '.mp4')
    mimetypes.add_type('video/mp4', '.m4v')

    server = HTTPServer(('0.0.0.0', port), CourseHandler)

    print(f'\n{"="*60}')
    print(f'  智联学习云 - 课程资源服务器已启动')
    print(f'  浏览器访问: http://localhost:{port}')
    print(f'  视频总数: {sum_course_videos()}')
    print(f'{"="*60}\n')

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print('\n正在关闭服务器...')
        server.server_close()


def sum_course_videos():
    try:
        with open(COURSE_DATA, 'r', encoding='utf-8') as f:
            courses = json.load(f)
        total = sum(c.get('total_videos', 0) for c in courses)
        return f'{len(courses)} 门课程, {total} 个视频'
    except:
        return '加载中...'


if __name__ == '__main__':
    main()
