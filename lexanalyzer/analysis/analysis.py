import re
from typing import List, Tuple
from lexanalyzer.analysis.regexes import COMMENTARY_REGEX, NUMBERS_REGEX, STRING_REGEX, WORD_REGEX
from lexanalyzer.token import Token

def obtain_token_from_word(word: str) -> Token:
    if word == "if":
        return Token(type="reserved_directive_if", value="if")
    elif word == "else":
        return Token(type="reserved_directive_else", value="else")
    elif word == "loop":
        return Token(type="reserved_directive_loop", value="loop")
    elif word == "number":
        return Token(type="reserved_type_number", value="number")
    elif word == "string":
        return Token(type="reserved_type_string", value="string")
    elif word == "void":
        return Token(type="reserved_type_void", value="void")
    elif word == "char":
        return Token(type="reserved_type_char", value="string")
    elif word == "return":
        return Token(type="reserved_directive_return", value="return")
    elif word == "read":
        return Token(type="reserved_func_read", value="read")
    elif word == "write":
        return Token(type="reserved_func_write", value="write")
    elif word == "input":
        return Token(type="reserved_func_input", value="input")
    elif word == "print":
        return Token(type="reserved_func_print", value="print")
    else:
        return Token(type="id", value=word)

def analyze_file(file_path: str) -> List[Tuple[Token, int, int]]:
    tokens: List[Tuple[Token, int, int]] = []
    with open(file_path) as file_stream:
        file_content = file_stream.read()
        tokens = analyze_text(file_content)
    return tokens

def analyze_text(text: str) -> List[Tuple[Token, int, int]]:
    tokens: List[Tuple[Token, int, int]] = []
    c_index = 0
    line_count = 0
    while c_index != len(text):
        if (text[c_index] == '\n'):
            line_count += 1
        numbers_match = re.search(NUMBERS_REGEX, text[c_index:])
        word_match = re.search(WORD_REGEX, text[c_index:])
        commentary_match = re.search(COMMENTARY_REGEX, text[c_index:])
        string_match = re.search(STRING_REGEX, text[c_index:])
        if (numbers_match):
            tokens.append((Token(type="number", value=numbers_match[0]), c_index, line_count))
            c_index += numbers_match.span()[1]
            continue
        elif (word_match):
            tokens.append((obtain_token_from_word(word_match[0]), c_index, line_count))
            c_index += word_match.span()[1]
            continue
        elif (commentary_match):
            tokens.append((Token(type="comment", value=commentary_match[0]), c_index, line_count))
            c_index += commentary_match.span()[1]
            continue
        elif (string_match):
            tokens.append((Token(type="string", value=string_match[0]), c_index, line_count))
            c_index += string_match.span()[1]
            continue
        elif text[c_index] == '☕':
            tokens.append((Token(type='end_of_line', value='☕'), c_index, line_count))
        elif text[c_index] == ' ' or text[c_index] == '\t' or text[c_index] == '\n':
            tokens.append((Token(type="spacing", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '=':
            tokens.append((Token(type="op_attr", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '(':
            tokens.append((Token(type="initial_parenthesis", value=text[c_index]), c_index, line_count))
        elif text[c_index] == ')':
            tokens.append((Token(type="final_parenthesis", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '🏳':
            tokens.append((Token(type="initial_block", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '🏁':
            tokens.append((Token(type="final_block", value=text[c_index]), c_index, line_count))
        elif text[c_index] and len(text) >= c_index and text[c_index] + text[c_index + 1] == '<=':
            tokens.append((Token(type="op_logic_smaller_equal", value=text[c_index]), c_index, line_count))
            c_index += 1
        elif text[c_index] and len(text) >= c_index and text[c_index] + text[c_index + 1] == '>=':
            tokens.append((Token(type="op_logic_greater_equal", value=text[c_index]), c_index, line_count))
            c_index += 1
        elif text[c_index] == '>':
            tokens.append((Token(type="op_logic_greater", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '<':
            tokens.append((Token(type="op_logic_smaller", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '➖':
            tokens.append((Token(type="op_arit_sub", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '➕':
            tokens.append((Token(type="op_arit_sum", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '/':
            tokens.append((Token(type="op_arit_div", value=text[c_index]), c_index, line_count))
        elif text[c_index] == '*':
            tokens.append((Token(type="op_arit_mult", value=text[c_index]), c_index, line_count))
        else:
            tokens.append((Token(type='error', value=text[c_index]), c_index, line_count))
        c_index += 1

    return tokens
