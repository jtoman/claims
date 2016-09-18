import sys

if len(sys.argv) != 3:
    print sys.argv
    sys.exit(1)

if int(sys.argv[1]) != 333 or int(sys.argv[2]) != 444:
    sys.exit(1)

sys.exit(0)
