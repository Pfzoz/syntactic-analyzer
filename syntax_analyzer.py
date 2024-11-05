from typing import Any, Dict
import pandas as pd
from pandas.core.groupby.grouper import DataFrame

data = pd.read_csv("grammar-data.csv")

class Terminal:

    def __init__(self, value: str) -> None:
        self.value: str = value

    def __repr__(self) -> str:
        return f"Terminal({self.value})"

    def __eq__(self, value: object, /) -> bool:
        if (type(value) is Terminal):
            return self.value == value.value
        return False

    def __hash__(self) -> int:
        return hash(self.value)

class NonTerminal:

    def __init__(self, value: str) -> None:
        self.value: str = value

    def __eq__(self, value: object, /) -> bool:
        if (type(value) is NonTerminal):
            return self.value == value.value
        return False

    def __repr__(self) -> str:
        return f"NonTerminal({self.value})"

    def __hash__(self) -> int:
        return hash(self.value)

non_terminals_df = data["NON_TERMINALS"].dropna()
terminals_df = data["TERMINALS"].dropna()
production_rules_df = data[["NON_TERMINAL", "PRODUCTION"]].dropna()

non_terminals: list[NonTerminal] = [NonTerminal(i) for i in non_terminals_df]
terminals: list[Terminal] = [Terminal(i) for i in terminals_df]
production_rules: Dict[str, list[list[Terminal | NonTerminal]]] = {non_terminal.value: [] for non_terminal in non_terminals}

for production_rule_row in production_rules_df.iterrows():
    non_terminal: str | Any = production_rule_row[1]["NON_TERMINAL"]
    production: str | Any = production_rule_row[1]["PRODUCTION"]

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

for k in production_rules.keys():
    if (len(production_rules[k]) == 0):
        print(f"Error: empty production for {k}")
        exit()

def get_first(symbol: NonTerminal | Terminal,
        production_rules: Dict[str, list[list[Terminal | NonTerminal]]]) -> set[Terminal]:

    if type(symbol) is Terminal:
        return set({symbol})

    first_set = set()
    production_rules_list = production_rules[symbol.value]
    for production_rule in production_rules_list:
        if (type(production_rule[0]) is Terminal or production_rule[0].value == 'ε'):
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
    non_terminal.value: get_first(non_terminal, production_rules) for non_terminal in non_terminals
}

follow_dict: Dict[str, set[Terminal] | None] = {
    non_terminal.value: get_follow(non_terminal, production_rules) for non_terminal in non_terminals
}

with open("follow.txt", 'w+') as follow_file:
    for k, follow_list in follow_dict.items():
        follow_file.write(f"Follow({k}) = {follow_list}\n")

with open("first.txt", 'w+') as first_file:
    for k, first_list in first_dict.items():
        first_file.write(f"First({k}) = {first_list}\n")


# for first_key in first_dict.keys():
#     print(f"First({first_key}) = {first_dict[first_key]}")

# for follow_key in follow_dict.keys():
#     print(f"Follow({follow_key}) = {follow_dict[follow_key]}")

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
                first_start = first_dict[production_rule[0].value] if type(production_rule[0]) is NonTerminal else set({production_rule[0],})
                assert first_start is not None
                if (terminal in first_start):
                    value = ""
                    for el in production_rule:
                        value += el.value
                        value += " "
                    predictive_syntactic_table.loc[NonTerminal(k), terminal] = value.strip()
                    break
        if Terminal('ε') in first_k:
            for terminal in follow_k:
                for production_rule in production_rules_list:
                    first_start = first_dict[production_rule[0].value] if type(production_rule[0]) is NonTerminal else set({production_rule[0],})
                    assert first_start is not None
                    if terminal != Terminal('$') and (terminal in first_start):
                        value = ""
                        for el in production_rule:
                            value += el.value
                            value += " "
                        predictive_syntactic_table.loc[NonTerminal(k), terminal] = value.strip()
                        break
                    elif terminal == Terminal('$') and (Terminal('ε') in first_start):
                        value = ""
                        for el in production_rule:
                            value += el.value
                            value += " "
                        predictive_syntactic_table.loc[NonTerminal(k), terminal] = value.strip()
                        break

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

def top_down_analysis(tape: list[Terminal], ) -> bool:
    tape.append(Terminal('$'))
    heap: list[NonTerminal | Terminal] = [Terminal('$'), NonTerminal("<START>"),]

    i = 0
    x = heap[-1]
    a = tape[i]

    while x != Terminal('$'):
        print(f"Tape: {tape} (Pos: {i})")
        print(f"Heap: {heap}")
        print(x, a)
        if type(x) is Terminal:
            if x == a:
                heap.pop()
                i += 1
            else:
                print("Error 1!")
                return False
        else:
            if pd.notna(predictive_syntactic_table.loc[x, a]):
                symbols = get_symbols_from_table_string(predictive_syntactic_table.loc[x, a])
                print(f"{x} -> {symbols}")
                symbols.reverse()
                if Terminal('ε') in symbols:
                    symbols.remove(Terminal('ε'))
                heap.pop()
                heap.extend(symbols)
            else:
                print("Error 2!")
                return False
        a = tape[i]
        x = heap[-1]

    return True

example: list[Terminal] = [Terminal('reserved_type_string'), Terminal('id'), Terminal('end_of_line')]
print(f"Input: {example}")

result = top_down_analysis(example)

print(f"Analysis result: {result}")
