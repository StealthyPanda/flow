from lexy import lexer
from percy import parser
from nodes import *
from middle import *
from typing import Callable, Any
from codex import dblog, error, ok, warning

import argparse



#-----------------------------------------------------------------------------------------------------------------------------
#terminal logging stuff

check = '✅'
loaders = "⣾⣽⣻⢿⡿⣟⣯⣷"
index = 0
def loading(strgen : Callable[[Any], str], *args):
    global index
    strval = strgen(*args)
    print(f'\r{loaders[index]} {strval}', end='')
    index += 1
    if index >= len(loaders): index = 0
def checked(val : str) -> str: return f'{check} {val}'


#-----------------------------------------------------------------------------------------------------------------------------






def make_cli_parser() -> argparse.ArgumentParser:
    cliparser = argparse.ArgumentParser(
        prog = 'flow',
        description='A CLI toolkit for Flow and Flow based programs.',
        epilog=''
    )
    cliparser.add_argument('filename')
    return cliparser


def check_flows(program : Program):
    for flow in program.flows:
        loading(lambda fl : f'Checking flow `{fl.name}`...', flow)
        semantic_check_flow(flow, ast)







if __name__ == '__main__':
    cliargs = make_cli_parser().parse_args()
    
    file = ''
    with open(cliargs.filename, 'r') as fb:
        file = (fb.read().strip())
    
    if not file:
        print('Empty input file! Exiting...')
        exit(0)
    
    ok(checked('File read...'))
    
    lexer.input(file)
    ast = parser.parse(file, lexer = lexer)
    
    ok(checked('AST constructed...'))
    
    ast = Program(
        name = None,
        flows = list(filter(lambda x: type(x) == FlowDef, ast)),
        builds = list(filter(lambda x: type(x) == Build, ast))
    )
    
    ast = iron(ast)
    
    ok(checked('AST ironed...'))
    
    
    check_flows(ast)
    
    print()
    ok(checked('Flows semantically checked...'))
    
    
    