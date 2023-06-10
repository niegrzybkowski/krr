import pyparsing as pp
import PySimpleGUI as sg

def get_default_location():
    return (100,100)

def parse_logic(expression, states):
    if len(states) == 0:
        sg.popup_error("At least one fluent is required to create a logic expression", location=get_default_location())
        return False
    logic_expr = create_logic_parser(states)
    try:
        parsed_expression = logic_expr.parse_string(expression, parse_all=True).as_list()
    except pp.exceptions.ParseException as e:
        sg.popup_error(f"Unable to parse expression.\nParser message: {e}", location=get_default_location())
        return False
    return parsed_expression

def create_literal_parser(literals):
    quoted_literal = (pp.Suppress("'") | pp.Suppress("\"")) + pp.Keyword(literals[0]) + (pp.Suppress("'") | pp.Suppress("\""))
    literal_parser = pp.Keyword(literals[0]) | quoted_literal
    for state in literals[1:]:
        quoted_literal = (pp.Suppress("'") | pp.Suppress("\"")) + pp.Keyword(literals[0]) + (pp.Suppress("'") | pp.Suppress("\""))
        literal_parser |= pp.Keyword(state) | quoted_literal
    return literal_parser

def create_logic_parser(states):
    quoted_literal = (pp.Suppress("'") | pp.Suppress("\"")) + pp.Keyword(states[0]) + (pp.Suppress("'") | pp.Suppress("\""))
    states_parser = pp.Keyword(states[0]) | quoted_literal
    for state in states[1:]:
        quoted_literal = (pp.Suppress("'") | pp.Suppress("\"")) + pp.Keyword(states[0]) + (pp.Suppress("'") | pp.Suppress("\""))
        states_parser |= pp.Keyword(state) | quoted_literal
    
    states_parser = states_parser.set_name("state")

    logic_expr = pp.infix_notation(
        states_parser,
        [
            ("not", 1, pp.OpAssoc.RIGHT),
            ("and", 2, pp.OpAssoc.LEFT),
            ("or", 2, pp.OpAssoc.LEFT),
            ("implies", 2, pp.OpAssoc.LEFT),
            ("if and only if", 2, pp.OpAssoc.LEFT),
        ]
    )
    return logic_expr