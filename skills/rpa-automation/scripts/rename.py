#!/usr/bin/env python3
"""
文件批量重命名工具
用法: python3 rename.py --prefix "report_" --ext .pdf
"""

import os
import sys
import argparse
import shutil
from datetime import datetime

def rename_files(folder, prefix='', suffix='', start=1, ext=None):
    folder = os.path.expanduser(folder)
    files = sorted([f for f in os.listdir(folder) if os.path.isfile(os.path.join(folder, f))])
    
    renamed = []
    for i, f in enumerate(files, start):
        old_path = os.path.join(folder, f)
        name, old_ext = os.path.splitext(f)
        
        if ext:
            new_ext = ext if ext.startswith('.') else '.' + ext
        else:
            new_ext = old_ext
            
        new_name = f"{prefix}{i:03d}{suffix}{new_ext}"
        new_path = os.path.join(folder, new_name)
        
        if old_path != new_path:
            shutil.move(old_path, new_path)
            renamed.append((f, new_name))
            print(f"✓ {f} → {new_name}")
    
    return renamed

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='批量重命名文件')
    parser.add_argument('--folder', '-f', default='.', help='文件夹路径')
    parser.add_argument('--prefix', '-p', default='', help='前缀')
    parser.add_argument('--suffix', '-s', default='', help='后缀')
    parser.add_argument('--start', '-n', type=int, default=1, help='起始编号')
    parser.add_argument('--ext', '-e', help='新扩展名')
    
    args = parser.parse_args()
    rename_files(args.folder, args.prefix, args.suffix, args.start, args.ext)
