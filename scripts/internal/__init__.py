import sys

# Catch wrong python version
if (sys.version_info < (3, 0)):
    print("ERROR: This script has to be run with python3. Please try the following command-line:\npython3 {}".format(" ".join(sys.argv)))
    exit(1)
