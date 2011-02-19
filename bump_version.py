#!/usr/bin/env python
from __future__ import print_function
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: ./bump_version.py VERSION")
        sys.exit(0)
    with open('VERSION', 'w') as f:
        f.write(sys.argv[1])
    content = []
    with open('po/zh_CN.po', 'r') as f:
        for line in f.readlines():
            if line.startswith('"Project-Id-Version'):
                content.append('"Project-Id-Version: yaner %s\\n"\n' % sys.argv[1])
            else:
                content.append(line)
    with open('po/zh_CN.po', 'w') as f:
        f.writelines(content)

