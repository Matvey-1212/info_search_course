import re
import sys
import json

def error(line_n, e_text):
    print(f'{line_n}:{e_text}')
    sys.exit(1)

def check_val_name(var_name, scope):
    if not re.match(scope['var_name'], var_name):
        return False
    return True

class ExprParser:
    def __init__(self, text, env, scope, line_i):
        self.text = text
        self.env = env
        self.pos = 0
        self.len = len(text)
        self.scope = scope
        self.line_i = line_i

    def peek(self):
        while self.pos < self.len and self.text[self.pos] == self.scope[' ']:
            self.pos += 1
        return self.text[self.pos] if self.pos < self.len else None

    def get_char(self):
        if self.pos >= self.len:
            return None
        c = self.text[self.pos]
        self.pos += 1
        return c

    def parse_number(self):
        start = self.pos
        
        while self.pos < self.len and (self.text[self.pos].isdigit() or self.text[self.pos] == self.scope['.']):
            self.pos += 1
            
        num_str = self.text[start:self.pos]
        
        if self.scope['.'] in num_str:
            try:
                return float('.'.join(num_str.split(self.scope['.'])))
            except Exception as e:
                error(self.line_i, f' error while type casting: "{num_str}" to float')
        else:   
            try:
                return int(num_str)
            except Exception as e:
                error(self.line_i, f' error while type casting: "{num_str}" to int')

    def parse_var(self):
        start = self.pos
        self.pos += 1
        
        while self.pos < self.len and self.text[self.pos] != self.scope[' ']:
            self.pos += 1
        name = self.text[start:self.pos]
        
        if not check_val_name(name, self.scope):
            error(self.line_i, f'Invalid var name "{name}"')
            
        if name in self.env:
            return self.env[name]
        else:
            error(self.line_i, f'Unknown variable "{name}"')

    def parse_string(self):
        flag_mir = False
        s = ''
        while True:
            c = self.get_char()
            if c is None:
                ends = self.scope['""']
                error(self.line_i, f"Can't parse ends '{ends}';")
            if c == '\\':
                if not flag_mir:
                    flag_mir = True
                else:
                    flag_mir = False
                    s += c
                continue
            
            if c in self.scope['""'] and not flag_mir:
                break

            flag_mir = False
            s += c
                    
        return s

    def parse_factor(self):
        ch = self.peek()

        if ch in self.scope['""']:
            self.pos += 1
            return self.parse_string()

        if ch.isdigit():
            return self.parse_number()

        if re.match(self.scope['var_name'], ch):
            return self.parse_var()

        if ch == self.scope['()'][0]:
            self.pos += 1
            val = self.parse_expr()
            if self.peek() != self.scope['()'][1]:
                ends = self.scope['()']
                error(self.line_i, f"Can't parse ends '{ends}';")
            self.pos += 1
            return val
        
        error(self.line_i, f'Unexpected character: {ch}')

    def parse_term(self):
        left = self.parse_factor()
        while True:
            ch = self.peek()
            if ch in (self.scope['*'], self.scope['/']):
                op = ch
                self.pos += 1
                right = self.parse_factor()

                if op == self.scope['*']:
                    try:
                        left *= right
                    except:
                        error(self.line_i, f'Error while multiplying "{left}"({type(left)}) and "{right}"({type(right)})')
                elif op == self.scope['/']:
                    try:
                        left /= right
                    except:
                        error(self.line_i, f'Error while dividing "{left}"({type(left)}) and "{right}"({type(right)})')
            else:
                break
        return left

    def parse_expr(self):
        left = self.parse_term()
        while True:
            ch = self.peek()
            if ch in (self.scope['+'], self.scope['-']):
                op = ch
                self.pos += 1
                right = self.parse_term()
  
                if op == self.scope['+']:
                    try:
                        left += right
                    except:
                        error(self.line_i, f'Error while adding "{left}"({type(left)}) and "{right}"({type(right)})')
                elif op == self.scope['-']:
                    try:
                        left -= right
                    except:
                        error(self.line_i, f'Error while subtracting "{left}"({type(left)}) and "{right}"({type(right)})')
            else:
                break
        return left

def eval_expr(text, env, scope, line_i):
    parser = ExprParser(text, env, scope, line_i)
    val = parser.parse_expr()
    return val

def run(code, scope):
    lines = code.split('\n')
    env = {}
    
    for i, line in enumerate(lines, start=1):
        line = line.rstrip(scope[' '])
        if len(line) == 0 or line.startswith(scope['#']) or line == '\n':
            continue
        
        if scope['#'] in line:
            line = line.split(scope['#'])[0].rstrip(scope[' '])
        
        if line.startswith(scope['read']):
            var = line[len(scope['read']):].strip(scope[' '])
            if not check_val_name(var, scope):
                error(i, f' invalid variable name: {var}')
                
            val = input().strip(scope[' '])
            if scope['.'] in val and len(val.split(scope['.'])) == 2 and val.split(scope['.'])[0].isnumeric() and val.split(scope['.'])[1].isnumeric():
                try:
                    val = '.'.join(val.split(scope['.']))
                    val = float(val)
                except Exception as e:
                    error(i, f' error while type casting: "{val}" to float')
            elif val.isnumeric():
                try:
                    val = int(val)
                except Exception as e:
                    error(i, f' error while type casting: "{val}" to int')

            env[var] = val    
                    
        elif line.startswith(scope['print']):
            val = line[len(scope['print']):].strip(scope[' '])
            print(eval_expr(val, env, scope, i))
            
        elif scope['='] in line:
            var, val = line.split(scope['='])
            var, val = var.strip(scope[' ']), val.strip(scope[' '])
            if not check_val_name(var,scope):
                error(i, f' invalid variable name: {var}')
                
            env[var] = eval_expr(val, env, scope, i)
        
        else:
            error(i, f'Unknown operation in {line};')
            

if __name__ == "__main__":
    scope_path = sys.argv[1]
    code_path = sys.argv[2]
    with open(code_path, 'r') as f:
        code = f.read()
    with open(scope_path, 'r') as f:
        scope = json.load(f)
    
    run(code, scope)