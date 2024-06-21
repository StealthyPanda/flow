import sys

from frontend.lexy import lexer
from frontend.percy import parser
from frontend.middle import *
from utils.nodes import *
from utils.logging import *
from cli import *

from codex import dblog, error, ok, warning






def check_flows(program : Program):
    def callback(stmt : Statement):
        loading(lambda x: f'Line no. {x.line}...', stmt)
    
    for flow in program.flows:
        loading(lambda fl : f'Checking flow `{fl.name}`...', flow)
        try : semantic_check_flow(flow, program, callback=callback)
        except Exception as e:
            show_error(f'Semantic check failed in flow `{flow.name}`!', e, program.file)
            sys.exit(-1)


def check_builds(program : Program):
    def callback(stmt : Statement):
        loading(lambda x: f'Line no. {x.line}...', stmt)
    
    for build in program.builds:
        loading(lambda fl : f'Checking build `{fl.name}`...', build)
        try : semantic_check_build(build, program, callback=callback)
        except Exception as e:
            show_error(f'Semantic check failed in build `{build.name}`!', e, program.file)
            sys.exit(-1)


def check_shapes(build : Build, context : Context):
    try:
        flowlengths_flow(build.flow, context)
        context.seed_shapes()
        flowshape_flow(build.flow, context)
        context.bake()
    except Exception as e:
        show_error(f'Shape check failed in `{build.name}`', e, context.program.file)
        sys.exit(-1)




def process_file(cliargs) -> tuple[Program, Context]:
    # cliargs = make_cli_parser().parse_args()
    
    try:
        with open(cliargs.filename, 'r') as fb:
            file = (fb.read())
        
        if not file:
            print('Empty input file! Exiting...')
            exit(0)
        
        print(('File read...'))
    except FileNotFoundError:
        error(f'Cannot find file `{cliargs.filename}`!')
        sys.exit(-1)
    
    try:
        lexer.input(file)
        ast = parser.parse(file, lexer = lexer, tracking = True)
    except Exception as e:
        show_error(f'Syntax error!', e, file)
        sys.exit(-1)
        
    
    print(('AST constructed...'))
    
    ast = Program(
        name = None,
        flows = list(filter(lambda x: type(x) == FlowDef, ast)),
        builds = list(filter(lambda x: type(x) == Build, ast)),
        file = file
    )
    ast = iron(ast)
    print(('AST ironed...'))
    
    
    check_flows(ast)
    ok(checked('Flows semantically checked...'))
    
    
    check_builds(ast)
    ok(checked('Builds semantically checked...'))
    
    build = cliargs.build
    if build is None: build = ast.builds[-1]
    else:
        for each in ast.builds:
            if each.name == build:
                build = each
    warning(f'Building from `{build.name}`...')
    context = contextfrombuild(build, ast)
    ok(checked('Context successfully built...'))
    
    check_shapes(build, context)
    
    return ast, context