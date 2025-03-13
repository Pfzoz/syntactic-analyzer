import re

class Variable:
    def __init__(self, var_type, var_name):
        self.type = var_type
        self.name = var_name

    def __repr__(self) -> str:
        return f"{self.name}: {self.type}"

def create__operation(file, value1 : Variable, value2 : Variable, target : Variable, op):
    file.write(f"{target} = {value1.name} {op} {value2.name}\n")

def create_attr(file, terminal : Variable, value : Variable):
    file.write(f"{terminal} = {value.name}")

def read_numeric(file, target):
    file.write(f"{target}: i32 = call read_int()\n")

def write_numeric(file, source):
    file.write(f"call write_string({source})\n")

def read_string(file, target):
    file.write(f"{target}: str = call read_string(100u32)\n")

def write_string(file, source):
    file.write(f"call write_string({source})\n")

def create_label(file, label):
    file.write(f"{label}:\n")

def create_if(file, value1, value2, op, target):
    file.write(f"if {value1} {op} {value2} goto {target}\n")

def create_goto(file, target):
    file.write(f"goto {target}:\n")

def is_variable(terminal : Variable):
    if terminal.type == "string" or terminal.type == "number":
        print(f"1:{terminal}")
        return True
    if terminal.type == "str" or terminal.type == "f32":
        print(f"2:{terminal}")
        return True
    return False

def is_numeric(terminal : Variable):
    if terminal.type == "numeric":
        if re.match(r'^\d+$', terminal.name):
            terminal.name += 'f32';
        return True
    return False

def fix_type(terminal : Variable):
    if terminal.type == "string":
        terminal.type = "str"
        return;
    if terminal.type == "number":
        terminal.type = "f32"
        return

with open("newfile.tac", "w+") as file:
    example = list[Variable]

    # a = b + c * d + e * 32
    example = [ Variable("number", "b"),
                Variable("number", "c"),
                Variable("number", "d"),
                Variable("operation","*"),
                Variable("number", "e"),
                Variable("numeric", "32"),
                Variable("operation","*"),
                Variable("operation","+"),
                Variable("operation","+"),
                Variable("number", "a"),
                Variable("attribuition","=")]

    temp_used = 0

    variables : list[Variable] = []

    for i in range(example.__len__()):
        if is_variable(example[i]) or is_numeric(example[i]):
            print(example[i])
            fix_type(example[i])
            variables.append(example[i])
        if example[i].type == "operation":
            temp_used += 1
            # print(variables)
            temp = Variable(variables[-1].type, ("t"+str(temp_used)))
            create__operation(file, variables.pop(), variables.pop(), temp, example[i].name)
            variables.append(temp)
        if example[i].type == "attribuition":
            create_attr(file, variables.pop(), variables.pop())
