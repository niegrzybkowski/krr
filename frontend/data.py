from dataclasses import dataclass
import PySimpleGUI as sg
import pyparsing as pp
from frontend.utils import get_default_location, parse_logic, create_logic_parser, create_literal_parser

DEFAULT_LOCATION = get_default_location()

@dataclass
class ACS:
    action: str
    agent: str
    time: int
    time_manager: any

    def __str__(self):
        return f"({self.action}, {self.agent}, {self.time}{self.time_manager.unit})"
    
    def data(self):
        return {
            "action": self.action,
            "agent": self.agent,
            "time": self.time,
        }

@dataclass
class LogicExpression:
    expression: str
    parsed_expression: any = None

    def parse(self, state_manager):
        states = state_manager.contents
        parse_result = parse_logic(self.expression, states)
        if parse_result:
            self.parsed_expression = parse_result
            return True
        else:
            return False

@dataclass
class OBS:
    original_expression: str
    time: int
    state_manager: any
    time_manager: any
    logic_expression: LogicExpression = None
    parsed_expression: any = None

    def __post_init__(self):
        if self.parsed_expression is not None:
            self.logic_expression = LogicExpression(self.original_expression)
            self.logic_expression.parsed_expression = self.parsed_expression
    
    def parse(self):
        self.logic_expression = LogicExpression(self.original_expression)
        return self.logic_expression.parse(self.state_manager)

    def data(self):
        return {
            "original_expression": self.logic_expression.expression,
            "parsed_expression": self.logic_expression.parsed_expression,
            "time": self.time
        }

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, OBS):
            return False
        if self is __value:
            return True
        if self.state_manager != __value.state_manager:
            return False
        if str(self.logic_expression.parsed_expression) != str(__value.logic_expression.parsed_expression):
            return False
        return True
    
    def __str__(self):
        return f"({self.original_expression}, {self.time}{self.time_manager.unit})"
    
@dataclass
class Statement:
    original_expression: str
    action_manager: any
    agent_manager: any
    state_manager: any
    action: str = None
    agent: str = None
    statement_type: str = None
    effects: any = None # [["state1"], ["not", "state2"]]
    condition: any = None # infix representation
    
    def validate_at_least_one_of_each(self):
        if len(self.action_manager.contents) == 0:
            sg.popup_error("At least one action is required to create a statement", location=DEFAULT_LOCATION)
            return False
        if len(self.state_manager.contents) == 0:
            sg.popup_error("At least one fluent is required to create a statement", location=DEFAULT_LOCATION)
            return False
        return True


    def parse(self):
        if not self.validate_at_least_one_of_each():
            return False

        action_parser = create_literal_parser(self.action_manager.contents).set_name("action")

        if len(self.agent_manager.contents) == 0: 
            # agent count CAN be 0, statements like "shoot causes not gun loaded"
            agent_parser = pp.Empty()
            agent_parser.set_parse_action(lambda: [None])
        else:
            agent_parser = create_literal_parser(self.agent_manager.contents).set_name("agent")
            agent_parser = pp.Opt(pp.Suppress("by") + agent_parser, default=None)

        statement_type_parser = (pp.Literal("releases") | pp.Literal("causes")).set_name("statement type (one of 'releases' or 'causes')")

        state_parser = create_literal_parser(self.state_manager.contents).set_name("state")
        
        effect_parser = pp.delimitedList(pp.Opt("not") + state_parser, delim="and")
        effect_parser.set_parse_action(lambda toks: [toks]).set_name("effect list")

        logic_condition = create_logic_parser(self.state_manager.contents)
        logic_parser = pp.Opt(pp.Suppress("if") + logic_condition, default=None)

        parser = action_parser + agent_parser + statement_type_parser + effect_parser + logic_parser
        try:
            parsed_expression = parser.parse_string(self.original_expression, parse_all=True).as_list()
        except pp.exceptions.ParseException as e:
            sg.popup_error(f"Unable to parse expression.\nParser message: {e}", location=DEFAULT_LOCATION)
            return False
        self.action, self.agent, self.statement_type, self.effects, self.condition = parsed_expression
        return parsed_expression
    
    def data(self):
        return {
            "original_expression": self.original_expression,
            "action": self.action,
            "agent": self.agent,
            "statement_type": self.statement_type,
            "effects": self.effects,
            "condition": self.condition,
        }

    def __eq__(self, __value: object) -> bool:
        if not isinstance(__value, Statement):
            return False
        if self is __value:
            return True
        self_data = self.data()
        self_data["original_expression"] = None
        o_data = __value.data()
        o_data["original_expression"] = None
        if self_data != o_data:
            return False
        return True
    
    def __str__(self):
        return self.original_expression

# @dataclass
# class Query:
#     original_expression: str
#     query_type: str
#     state_manager: any
#     action_manager: any
#     agent_manager: any
#     time_manager: any
#     parsed_expression: any = None
    

#     def parse_as_fluent(self):
        

#     def parse(self):
#         pass
