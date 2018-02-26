import sys
import getopt


# cmd_params = sys.argv[1:]
# print(cmd_params)
# opts, args = getopt.getopt(cmd_params, "c:h", ['help', 'config='])
# print(opts)
# for option, parameter in opts:
#     if option == '-h' or option == '--help':
#         print("help information")
#     if option in ('-c', '--config'):
#          print("Using configeration file %s" % parameter)
# print(args)

import ConfigParser

conf = ConfigParser.ConfigParser()
conf.read('bak.cnf')

print conf.get('MySQL','mysql_password')