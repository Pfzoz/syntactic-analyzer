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
        if (type(production_rule[0]) is NonTerminal):
            previous_first = get_first(production_rule[0], production_rules)
            first_set =  first_set.union(previous_first)
            for i, el in enumerate(production_rule[1:]):
                if (not type(el) is NonTerminal):
                    break
                if not Terminal('ε') in previous_first:
                    break
                if not symbol == el:
                    previous_first = get_first(production_rule[0], production_rules)
                    first_set =  first_set.union(previous_first)
                else:
                    previous_first = first_set
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
            if type(production_rule[-1]) is NonTerminal and production_rule[-1] == symbol and NonTerminal(k) != symbol:
                if (NonTerminal(k) in computed_follows):
                    return follow_set
                computed_follows.append(NonTerminal(k))
                follow_set = follow_set.union(get_follow(NonTerminal(k), production_rules, computed_follows))
            for i, el in enumerate(production_rule):
                if type(el) is NonTerminal and el == symbol and i < (len(production_rule) - 1):

                    follow_set = follow_set.union(get_first(production_rule[i + 1], production_rules).difference({Terminal('ε'),}))

    return follow_set

first_dict: Dict[str, set[Terminal] | None] = {
    non_terminal.value: get_first(non_terminal, production_rules) for non_terminal in non_terminals
}

follow_dict: Dict[str, set[Terminal] | None] = {
    non_terminal.value: get_follow(non_terminal, production_rules) for non_terminal in non_terminals
}

for first_key in first_dict.keys():
    print(f"First({first_key}) = {first_dict[first_key]}")

for follow_key in follow_dict.keys():
    print(f"Follow({follow_key}) = {follow_dict[follow_key]}")

def create_table(production_rules: Dict[str, list[list[Terminal | NonTerminal]]]) -> DataFrame:
    terminals_with_start_symbol = terminals.copy()
    terminals_with_start_symbol.append(Terminal('$'))
    predictive_syntactic_table = DataFrame(columns=pd.Index(terminals_with_start_symbol), index=pd.Index(non_terminals))

    # for k, production_rules_list in production_rules.items():
    #     first_k = get_first(NonTerminal(k), production_rules)
    #     for terminal in first_k:
    #         predictive_syntactic_table.loc[]

    return predictive_syntactic_table
