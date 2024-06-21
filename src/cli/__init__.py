import argparse

from utils.nodes import *
from utils.logging import *
from frontend.middle import followdim, Context

from codex import dblog, ok, warning, error


def make_cli_parser() -> argparse.ArgumentParser:
    cliparser = argparse.ArgumentParser(
        prog = 'flow',
        description='A CLI toolkit for Flow and Flow based programs.',
        epilog=''
    )
    # cliparser.add_argument('command', help='', choices=['install'])
    cliparser.add_argument('-f', '--filename', help='File name or path for the input code.')
    cliparser.add_argument('-b', '--build', metavar='B', help='Name of the build to process from the file. Defaults to the last defined build in the file.')
    cliparser.add_argument('-o', '--output', metavar='O', help='Name / path of the output file.')
    cliparser.add_argument('-i', '--install', metavar='I', help='Install a plugin from GitHub.')
    cliparser.add_argument('-s', '--sync', action='store_true', help='Install all plugins from json.')
    cliparser.add_argument('-d', '--debug', action='store_true', help='Print debug information.')
    return cliparser




def show_chain(file : str, ic : InferenceChain, context : Context, cols : int = 50):
    chain = list(filter(lambda x:x[0] is not None, ic.chain))
    
    for i, (line, shape) in enumerate(chain[::-1]):
        # shape = [followdim(x, context) for x in shape]
        print(f'Inferred shape {shape} from line {line}:')
        print(excerpt(file, line, cols=cols))
        if i != (len(chain) - 1):
            print((' ' * ((cols // 2) - 1)) + '⬆️' + (' ' * ((cols // 2) - 1)))
    



def show_error(msg : str, e : CodeError, file : str):
    error(msg)
    if e.line is not None: print(excerpt(file, e.line))
    print(e)
    if e.ichain is not None:
        print('Inference chain:')
        print(e.ichain)



