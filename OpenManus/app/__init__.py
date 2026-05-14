# Python version check: 3.10+
import sys


if sys.version_info < (3, 10):
    print(
        "Warning: Unsupported Python version {ver}, please use 3.10+".format(
            ver=".".join(map(str, sys.version_info))
        )
    )
