from cli import *
from frontend.main import process_file
from frontend.middle import extract_shapes

from codex import dblog, warning, error, ok
from dulwich import porcelain
from urllib.parse import urlparse

import importlib


import os, sys, json, pickle


cwd = os.getcwd()
flowinfopath = os.path.join(cwd, 'plugins.flow.json')
installspath = os.path.join(cwd, 'flow_plugins')


def get_repo_name_from_url(url : str):
    parsed_url = urlparse(url)
    path = parsed_url.path
    repo_name = os.path.basename(path)
    if repo_name.endswith('.git'):
        repo_name = repo_name[:-4]
    return repo_name


def install_plugin(link : str):
    pluginname = get_repo_name_from_url(link)
    if not os.path.exists(installspath): os.mkdir(installspath)
    porcelain.clone(link, os.path.join(installspath, pluginname))
    ok(f'Installed `{pluginname}` successfully!')

def read_flow_info() -> dict:
    with open(flowinfopath, 'r') as file:
        obj = json.load(file)
    return obj


def main():
    cliargs = make_cli_parser().parse_args()
    
    
    #TODO: Put CLI logic here...
    
    if cliargs.install is not None:
        plugin_name = get_repo_name_from_url(cliargs.install)
        
        warning(f'Installing `{plugin_name}`...')
        
        try:
            if os.path.exists(flowinfopath):
                with open(flowinfopath, 'r') as file:
                    original = json.load(file)
                original['plugins'][plugin_name] = cliargs.install
                original['use-plugin'] = plugin_name
            
            else:
                original = {
                    'plugins' : {
                        plugin_name : cliargs.install
                    },
                    'use-plugin' : plugin_name
                }
            
            with open(flowinfopath, 'w') as file:
                json.dump(original, file, indent='\t')
        except PermissionError:
            error('Cannot create plugins.flow.json, likely caused by not enough privilege!')
            sys.exit(-1)
        
        try : install_plugin(cliargs.install)
        except Exception as e:
            print(e)
            error('Plugin install failed! Exiting...')
            sys.exit(-1)
        
        return
    
    if cliargs.sync:
        if os.path.exists(flowinfopath):
            with open(flowinfopath, 'r') as file:
                original = json.load(file)
            
            for each in original['plugins']:
                try: install_plugin(original['plugins'][each])
                except Exception as e:
                    print(e)
                    error('Plugin install failed! Exiting...')
                    sys.exit(-1)
            
        else:
            error('No plugins.flow.json found! Sync failed, Exiting...')
            sys.exit(-1)
    
    if cliargs.filename is not None:
        ast, context = process_file(cliargs)
        
        if cliargs.debug:
            with open(cliargs.filename, 'r') as fb:
                file = fb.read()
            for each in context.ichains:
                print(f'Inference chain for {each}:')
                show_chain(file, context.ichains[each], context)
                print()
        
        info = read_flow_info()
        
        # plugin = info['plugins'][info['use-plugin']]
        plugin = info['use-plugin']
        
        sys.path.append(os.path.join(installspath, plugin))
        plugin = importlib.import_module(f'plugin')
        
        # print(context)
        output, ast, context = plugin.main(ast, context)
        
        _, filename = os.path.split(cliargs.filename)
        filename = filename.split('.')[0]
        
        outfile = cliargs.output
        if cliargs.output is None: outfile = f'{filename}_flow.py'
        with open(os.path.join(cwd, outfile), 'w') as file:
            file.write(output)
        
        ok(checked(f'Output sucessfully written to `{outfile}`!'))
        
    
    