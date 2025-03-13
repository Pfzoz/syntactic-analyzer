import json
from typing import Any, Dict, Literal
import pandas as pd
from pandas.core.groupby.grouper import DataFrame
from sys import argv
from lexanalyzer import analysis, Token

if len(argv) < 2 or argv[1].startswith("-"):
    print("Expected file path input. Failed. Exitting...")
    exit()

data = pd.read_csv("grammar-data.csv")

class Terminal:

    def __init__(self, type: str, value: Any = None, line: int | None = None) -> None:
        self.type: str = type
        self.line = line
        self.value: Any = value


    def __repr__(self) -> str:
        return f"Terminal({self.type}, {self.value})"

    def __eq__(self, value: object, /) -> bool:
        if (type(value) is Terminal):
            return self.type == value.type
        return False

    def __hash__(self) -> int:
        return hash(self.type)

class NonTerminal:

    def __init__(self, type: str) -> None:
        self.type: str = type

    def __eq__(self, value: object, /) -> bool:
        if (type(value) is NonTerminal):
            return self.type == value.type
        return False

    def __repr__(self) -> str:
        return f"NonTerminal({self.type})"

    def __hash__(self) -> int:
        return hash(self.type)

def terminal_from_token(token: Token, line: int):
    terminal = Terminal(token.type, token.value, line)
    return terminal

production_rules_df = data[["NON_TERMINAL", "PRODUCTION"]]
actions_df = data["ACTION"]
non_terminals_df = data["NON_TERMINALS"].dropna()
terminals_df = data["TERMINALS"].dropna()

non_terminals: list[NonTerminal] = [NonTerminal(i) for i in non_terminals_df]
terminals: list[Terminal] = [Terminal(i) for i in terminals_df]
production_rules: Dict[str, list[list[Terminal | NonTerminal]]] = {non_terminal.type: [] for non_terminal in non_terminals}
actions_map: Dict[str, str | None] = {}

def get_action_key(non_terminal: str, production: list[Terminal | NonTerminal]) -> str:
    action_key = non_terminal + "->"
    for el in production:
        action_key += el.type
    return action_key

for i, production_rule_row in enumerate(production_rules_df.iterrows()):
    non_terminal: str | Any = production_rule_row[1]["NON_TERMINAL"]
    production: str | Any = production_rule_row[1]["PRODUCTION"]

    if not pd.notna(non_terminal) or not pd.notna(production):
        continue

    production_list = []
    if not non_terminal in production_rules.keys():
        print(f"Error: {non_terminal} doesn't exist")
        exit()

    for el in production.split():
        if (el.startswith("<") and el.endswith(">")):
            production_list.append(NonTerminal(el))
        else:
            production_list.append(Terminal(el))

    production_rules[non_terminal].append(production_list)
    actions_map[get_action_key(non_terminal, production_list)] = actions_df.loc[i] if pd.notna(actions_df.loc[i]) else None

with open("actions_map.txt", 'w+') as actions_map_file:
    for action_key, action in actions_map.items():
        actions_map_file.write(f"Action({action_key}) = {action}\n")

for action_key in production_rules.keys():
    if (len(production_rules[action_key]) == 0):
        print(f"Error: empty production for {action_key}")
        exit()

def get_first(symbol: NonTerminal | Terminal,
        production_rules: Dict[str, list[list[Terminal | NonTerminal]]]) -> set[Terminal]:

    if type(symbol) is Terminal:
        return set({symbol})

    first_set = set()
    production_rules_list = production_rules[symbol.type]
    for production_rule in production_rules_list:
        if (type(production_rule[0]) is Terminal or production_rule[0].type == 'ε'):
            first_set.add(production_rule[0])
            continue
        if (type(production_rule[0]) is NonTerminal):
            previous_first = get_first(production_rule[0], production_rules)
            first_set =  first_set.union(previous_first)
            for i, el in enumerate(production_rule[1:]):
                if not Terminal('ε') in previous_first:
                    break
                if not symbol == el:
                    previous_first = get_first(el, production_rules)
                    first_set =  first_set.union(previous_first)
                else:
                    previous_first = first_set
                if type(el) is Terminal:
                    break
                if i == (len(production_rule) - 1) and Terminal('ε') in previous_first:
                    first_set.add(Terminal('ε'))

    return first_set

def get_follow(symbol: NonTerminal,
    production_rules: Dict[str, list[list[Terminal | NonTerminal]]], computed_follows: list[NonTerminal] | None = None) -> set[Terminal]:

    if computed_follows is None:
        computed_follows = [symbol,]

    follow_set = set({Terminal('$'),}) if symbol == NonTerminal('<START>') else set()

    for k in production_rules.keys():
        production_rule_list = production_rules[k]
        for production_rule in production_rule_list:
            for i, el in enumerate(production_rule):
                if el == symbol:
                    if i < (len(production_rule) - 1):
                        follow_set = follow_set.union(get_first(production_rule[i + 1], production_rules).difference({Terminal('ε'),}))
            for i in range(len(production_rule) - 1, -1, -1):
                if production_rule[i] == symbol:
                    if i == (len(production_rule) - 1):
                        if (NonTerminal(k) in computed_follows):
                            break
                        computed_follows.append(NonTerminal(k))
                        follow_set = follow_set.union(get_follow(NonTerminal(k), production_rules, computed_follows))
                        break
                    all_symbols = True
                    for j in range(i + 1, len(production_rule)):
                        if not Terminal('ε') in get_first(production_rule[j], production_rules):
                            all_symbols = False
                    if all_symbols:
                        if (NonTerminal(k) in computed_follows):
                            break
                        computed_follows.append(NonTerminal(k))
                        follow_set = follow_set.union(get_follow(NonTerminal(k), production_rules, computed_follows))
                    break

    return follow_set

first_dict: Dict[str, set[Terminal] | None] = {
    non_terminal.type: get_first(non_terminal, production_rules) for non_terminal in non_terminals
}

follow_dict: Dict[str, set[Terminal] | None] = {
    non_terminal.type: get_follow(non_terminal, production_rules) for non_terminal in non_terminals
}

with open("follow.txt", 'w+') as actions_map_file:
    for action_key, action in follow_dict.items():
        actions_map_file.write(f"Follow({action_key}) = {action}\n")

with open("first.txt", 'w+') as first_file:
    for action_key, first_list in first_dict.items():
        first_file.write(f"First({action_key}) = {first_list}\n")

def create_table(production_rules: Dict[str, list[list[Terminal | NonTerminal]]]) -> DataFrame:
    terminals_with_start_symbol = terminals.copy()
    terminals_with_start_symbol.append(Terminal('$'))
    predictive_syntactic_table = DataFrame(columns=pd.Index(terminals_with_start_symbol), index=pd.Index(non_terminals))

    for k, production_rules_list in production_rules.items():
        first_k = first_dict[k]
        follow_k = follow_dict[k]
        assert first_k is not None
        assert follow_k is not None
        for terminal in first_k:
            for production_rule in production_rules_list:
                first_set = set()
                for symbol in production_rule:
                    if isinstance(symbol, Terminal):
                        first_set.add(symbol)
                        if symbol.type != 'ε':  # Stop if non-nullable terminal found
                            break
                    else:
                        first_non_terminal_first = first_dict.get(symbol.type, set())
                        assert first_non_terminal_first is not None
                        first_set |= (first_non_terminal_first - {Terminal('ε')})
                        if Terminal('ε') not in first_non_terminal_first:
                            break

                if terminal in first_set:
                    value = " ".join(el.type for el in production_rule)
                    predictive_syntactic_table.loc[NonTerminal(k), terminal] = value.strip()

        #### FOLLOW

        if Terminal('ε') in first_k:
            for terminal in follow_k:
                added = False
                for production_rule in production_rules_list:
                    first_set = set()
                    for symbol in production_rule:
                        if isinstance(symbol, Terminal):
                            first_set.add(symbol)
                            if symbol.type != 'ε':  # Stop if non-nullable terminal found
                                break
                        else:
                            first_non_terminal_first = first_dict.get(symbol.type, set())
                            assert first_non_terminal_first is not None
                            first_set |= (first_non_terminal_first - {Terminal('ε')})
                            if Terminal('ε') not in first_non_terminal_first:
                                break

                    if terminal in first_set:
                        value = " ".join(el.type for el in production_rule)
                        predictive_syntactic_table.loc[NonTerminal(k), terminal] = value.strip()
                        added = True
                        break

                    elif terminal == Terminal('$') and Terminal('ε') in first_set:
                        value = " ".join(el.type for el in production_rule)
                        predictive_syntactic_table.loc[NonTerminal(k), terminal] = value.strip()
                        added = True
                        break

                if not added:
                    predictive_syntactic_table.loc[NonTerminal(k), terminal] = "ε"

        for production_rule in production_rules_list:

            for terminal in follow_k:
                if predictive_syntactic_table.loc[NonTerminal(k), terminal] is None:
                    predictive_syntactic_table.loc[NonTerminal(k), terminal] = 'ε'

    return predictive_syntactic_table

predictive_syntactic_table = create_table(production_rules)

predictive_syntactic_table.to_csv("pst.csv")

def get_symbols_from_table_string(s: str) -> list[Terminal | NonTerminal]:
    symbols: list[Terminal | NonTerminal] = []
    for el in s.split():
        if el.startswith("<") and el.endswith(">"):
            symbols.append(NonTerminal(el))
        else:
            symbols.append(Terminal(el))
    return symbols

## SEMANTIC

symbol_table: list[Dict[str, Dict[Literal["var_type", "value"], Any]]] = [{}]
scopes_attributes: list[Dict[str, Any]] = [{"type": "global_scope", "value": None}]
semantic_error_count = 0
scope_opener_attributes: dict = {}

def open_scope():
    symbol_table.append({})
    scopes_attributes.append(scope_opener_attributes)

def close_scope():
    if len(symbol_table) > 1:
        symbol_table.pop()
        scopes_attributes.pop()
    else:
        print("Error: Cannot close global scope!")

def declare_variable(identifier: str, var_type: str, value: Any = None):
    global semantic_error_count
    for var in symbol_table[-1].keys():
        if var == identifier:
            print(f"Error: Duplicate variable '{identifier}' in the same scope.")
            semantic_error_count += 1
            return
    else:
        symbol_table[-1][identifier] = {"var_type": var_type, "value": value}

def execute_semantic_action(action: str | None, symbols: list[Terminal | NonTerminal], tape: list[Terminal], tape_pos: int, x: NonTerminal | Terminal):
    if action is None:
        return
    elif action == "open_scope":
        open_scope()
    elif action == "close_scope":
        close_scope()
    elif action == "set_scope_opener":
        action_non_terminal_str = get_action_key(x.type, symbols).split("->")[0]
        scope_types = {
            "SENTENCE_BODY": "generic",
            "<FUNCTION_DECLARATION>": "function",
            "<LOOP'>": "loop",
            "<DECLARED_LOOP>": "loop",
            "<CONDITION_SEQUENCE>": "if",
            "<ALTERNATIVE_CONDITIONS'>": "else if"
        }
        scope_type = scope_types[action_non_terminal_str]
        if action == "<ALTERNATIVE_CONDITIONS'>-><BLOCK>": scope_type = "else"
        global scope_opener_attributes
        value = None
        if action_non_terminal_str == "<FUNCTION_DECLARATION>":
            last_scope = symbol_table[-1]
            last_symbol = list(last_scope.keys())[-1]
            value = last_symbol
        scope_opener_attributes = {
            "type": scope_type,
            "value": value,
        }
    elif action == "declare":
        var_type = tape[tape_pos].type if tape[tape_pos + 2] == Terminal("op_attr") or tape[tape_pos + 2] == Terminal("end_of_line") else "function"
        identifier_terminal = tape[tape_pos + 1]
        value = tape[tape_pos + 3].value if tape[tape_pos + 2] == Terminal("op_attr") else None
        assert type(identifier_terminal) is Terminal
        declare_variable(str(identifier_terminal.value), var_type, value)

## TOP DOWN

def print_symbol_table():
    for i, scope in enumerate(symbol_table):
        print(f"SCOPE {i}; ATTRIBUTES {scopes_attributes[i]}")
        print(json.dumps(scope, indent=4))

def top_down_analysis(tape: list[Terminal], ) -> bool:
    tape.append(Terminal('$'))
    heap: list[NonTerminal | Terminal] = [Terminal('$'), NonTerminal("<START>"),]

    i = 0
    x = heap[-1]
    a = tape[i]

    show_symbols = "-ss" in argv
    show_grammar_results = "-sg" in argv
    show_symbol_table = "-st" in argv

    while x != Terminal('$'):
        if show_symbols:
            print(f"\nTape: {tape} (Pos: {i})")
            print(f"Heap: {heap}")
            print(f"[{x}, {a}]")
        if show_symbol_table:
            print("==SYMBOL TABLE==")
            print_symbol_table()
        if type(x) is Terminal:
            if x == a:
                if a == Terminal("final_block"):
                    execute_semantic_action("close_scope", [], tape, i, x)
                heap.pop()
                i += 1
            else:
                print(f"Token doesn't match! Token {i}, line {a.line}, {a} against {x}. Token discarded.")
                if a == Terminal('$'):
                    print("Could not recognize end of grammar.")
                    return False
                tape.pop(0)
        else:
            if pd.notna(predictive_syntactic_table.loc[x, a]):
                if predictive_syntactic_table.loc[x, a] != "sinc":
                    symbols = get_symbols_from_table_string(predictive_syntactic_table.loc[x, a])
                    action_key = get_action_key(x.type, symbols)
                    action = actions_map.get(action_key, None)
                    execute_semantic_action(action, symbols, tape, i, x)
                    if show_grammar_results:
                        print(f"{x} -> {symbols} (Action: {action})")
                    symbols.reverse()
                    if Terminal('ε') in symbols:
                        symbols.remove(Terminal('ε'))
                    heap.pop()
                    heap.extend(symbols)
                else:
                    print(f"Sinc encountered! Token {i}, line {a.line}: {a}. Token: {a.value}")
                    heap.pop()
            else:
                print(f"Error found at token {i}, line {a.line}: {a} (No entry on PST). Token {a.value} discarded.")
                if a == Terminal('$'):
                    print("Could not recognize end of grammar.")
                    return False
                tape.pop(0)
        a = tape[i]
        x = heap[-1]

    return True

# example: list[Terminal] = [Terminal('id'), Terminal('id'), Terminal('op_attr'), Terminal('string'), Terminal('end_of_line')]

EXAMPLE_CODE_PATH = argv[1]

tokens = analysis.analyze_file(EXAMPLE_CODE_PATH)

example_terminals: list[Terminal] = []

for token in tokens:
    if token[0].type != "spacing" and token[0].type != "error" and token[0].type != "comment":
        example_terminals.append(terminal_from_token(token[0], token[2]))

print(f"Input: {example_terminals}\n")

result = top_down_analysis(example_terminals)

print(f"\nSyntax Analysis result: {'Success!' if result else 'Fail.'}")
print(f"Semantic Analysis result: {'Success!' if semantic_error_count == 0 else 'Fail.'}")
