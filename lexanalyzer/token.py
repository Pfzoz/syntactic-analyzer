from dataclasses import dataclass
from typing import Any, Literal, Optional

TokenType = Literal[
    "op_arit_mult",
    "op_logic_equal",
    "op_arit_div",
    "op_logic_greater",
    "op_logic_smaller",
    "op_logic_greater_equal",
    "op_logic_smaller_equal",
    "op_arit_sum",
    "op_arit_sub",
    "comma",
    "final_parenthesis",
    "initial_parenthesis",
    "op_attr",
    "spacing",
    "end_of_line",
    "initial_block",
    "final_block",
    "char",
    "reserved_type_char",
    "number",
    "reserved_type_number",
    "string",
    "reserved_type_string",
    "error",
    "id",
    "reserved_directive_if",
    "reserved_directive_else",
    "reserved_directive_loop",
    "reserved_directive_return",
    "reserved_type_void",
    "reserved_func_read",
    "reserved_func_write",
    "reserved_func_input",
    "reserved_func_print",
    "comment"
]

@dataclass
class Token:
    type: TokenType
    value: Optional[Any] = None
