from typing import Callable, Any

#-----------------------------------------------------------------------------------------------------------------------------
#terminal logging stuff

check = '✅'
loaders = "⣾⣽⣻⢿⡿⣟⣯⣷"
index = 0

def loading(strgen : Callable[[Any], str], *args):
    global index
    strval = strgen(*args)
    print(f'{loaders[index]} {strval}', end='\r')
    index += 1
    if index >= len(loaders): index = 0


def checked(val : str) -> str: return f'{check} {val}'

def ntabs(val : str) -> int:
    return len(list(filter(lambda x:x=='\t', val)))

def removetabs(val : str) -> str:
    new = []
    for each in val:
        if each == '\t': new.append('    ')
        else: new.append(each)
    return ''.join(new)


tr = '╮'
bl = '╰'
tl = '╭'
br = '╯'
def excerpt(file : str, lineno : int, cols : int = 60) -> str:
    lineno -= 1
    
    rows = 3
    
    start = lineno - (rows // 2) if lineno >= (rows // 2) else 0
    region = file.splitlines()[ start : lineno + (rows // 2) + 1]
    
    for i, each in enumerate(region):
        each = removetabs(each)[:cols]
        each = each + (' ' * (cols - len(each)))
        region[i] = f'{">" if (i + start) == lineno else " "}|{each[:cols]}|'
    
    region.insert(0, ' ' + tl + ('-' * cols) + tr)
    region.append(' ' + bl + ('-' * cols) + br)
    
    return '\n'.join(region)


#-----------------------------------------------------------------------------------------------------------------------------
