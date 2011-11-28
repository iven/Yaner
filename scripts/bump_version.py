#!/usr/bin/env python
import sys

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("Usage: ./bump_version.py VERSION")
        sys.exit(0)

    content = []
    with open('yaner/__init__.py', 'r') as f:
        for line in f:
            if line.startswith('__version__'):
                line = "__version__ = '{}'\n".format(sys.argv[1])
            content.append(line)
    with open('yaner/__init__.py', 'w') as f:
        f.writelines(content)

    content = []
    with open('po/zh_CN.po', 'r') as f:
        for line in f:
            if line.startswith('"Project-Id-Version'):
                line = '"Project-Id-Version: yaner {}\\n"\n'.format(sys.argv[1])
            content.append(line)
    with open('po/zh_CN.po', 'w') as f:
        f.writelines(content)

