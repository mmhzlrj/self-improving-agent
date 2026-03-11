#!/usr/bin/env python3
"""
文件夹清理工具 - 按时间删除旧文件
用法: python3 cleanup.py --folder ~/Downloads --days 30 --ext .log
"""

import os
import argparse
import time
from datetime import datetime

def cleanup_folder(folder, days=30, ext=None, dry_run=False):
    folder = os.path.expanduser(folder)
    now = time.time()
    age_seconds = days * 86400
    
    deleted = []
    kept = []
    
    for f in os.listdir(folder):
        path = os.path.join(folder, f)
        
        if not os.path.isfile(path):
            continue
            
        # 检查扩展名
        if ext and not f.endswith(ext):
            continue
        
        # 检查时间
        mtime = os.stat(path).st_mtime
        age = now - mtime
        
        if age > age_seconds:
            if dry_run:
                deleted.append((f, f"{days - int(age/86400)} 天前"))
            else:
                os.remove(path)
                deleted.append((f, "已删除"))
        else:
            kept.append(f)
    
    print(f"\n📁 文件夹: {folder}")
    print(f"🗑️  将删除 ({len(deleted)}):")
    for f, reason in deleted:
        print(f"   - {f} ({reason})")
    
    if dry_run:
        print(f"\n⚠️  这是预览模式，使用 --confirm 确认删除")
    else:
        print(f"\n✅ 已删除 {len(deleted)} 个文件，保留 {len(kept)} 个")
    
    return deleted

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='清理旧文件')
    parser.add_argument('--folder', '-f', default='.', help='文件夹路径')
    parser.add_argument('--days', '-d', type=int, default=30, help='保留天数')
    parser.add_argument('--ext', '-e', help='仅处理此扩展名')
    parser.add_argument('--confirm', action='store_true', help='确认删除')
    
    args = parser.parse_args()
    
    if not args.confirm:
        print("⚠️  预览模式，加 --confirm 确认删除")
        cleanup_folder(args.folder, args.days, args.ext, dry_run=True)
    else:
        cleanup_folder(args.folder, args.days, args.ext, dry_run=False)
