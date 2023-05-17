import PySimpleGUI as sg
import pyparsing as pp
from dataclasses import dataclass
import json

sg.theme('dark grey 9')   

DEFAULT_LOCATION = (100,100)

class CollectionManager:
    def __init__(self, contents_display_id):
        self.contents_display_id = contents_display_id
        self.contents = []
        self.contents_display = sg.Text("", key=contents_display_id)
    
    def update(self, window):
        window[self.contents_display_id].update(
            "\n".join(
                [
                    f"{i+1:>3}. {element}"
                    for i, element in enumerate(self.contents)
                ]
            )
        )

    def validate_add(self, element):
        raise NotImplementedError()
    
    def popup_add(self):
        raise NotImplementedError()
    
    def preprocess_element(self, element):
        return element
    
    def request_new_element(self, window):
        element = self.popup_add()
        if not self.validate_add(element):
            return
        element = self.preprocess_element(element)
        self.contents.append(element)
        self.update(window)

    def validate_remove(self, element):
        raise NotImplementedError()
    
    def popup_remove(self):
        raise NotImplementedError()

    def request_remove_element(self, window):
        element_number = self.popup_remove()
        if not self.validate_remove(element_number):
            return
        self.contents.pop(int(element_number)-1)
        self.update(window)

class SimpleCollectionManager(CollectionManager):
    def __init__(self, content_name):
        super().__init__(f"-{content_name}-")
        self.content_name = content_name
        self.content_name_lower = content_name.lower()
        self.content_name_title = content_name.title()
        self.add_event_key = f"-{self.content_name}-ADD-"
        self.remove_event_key = f"-{self.content_name}-REMOVE-"
        self.display = [
            [sg.Text(f"{self.content_name_title}s:", key=f"-{content_name}-HEADER-")],
            [self.contents_display],
            [sg.Button("Add", key=self.add_event_key), sg.Button("Remove", key=self.remove_event_key)]
        ]

    def popup_add(self):
        return sg.popup_get_text(f"Enter new {self.content_name_lower}:", title=f"{self.content_name_title} creation dialog", location=DEFAULT_LOCATION)
    
    def popup_remove(self):
        return sg.popup_get_text(f"Enter {self.content_name_lower} number to remove:", title=f"{self.content_name_title} deletion dialog", location=DEFAULT_LOCATION)

    def validate_add(self, element):
        if element is None:
            return False
        if element == "":
            sg.popup_error(f"{self.content_name_title} name cannot be empty", location=DEFAULT_LOCATION)
            return False
        if element in self.contents:
            sg.popup_error(f"{self.content_name_title} '{element}' already exists",  location=DEFAULT_LOCATION)
            return False
        return True
    
    def validate_remove(self, element):
        if element is None:
            return False
        try:
            element = int(element)
        except ValueError:
            sg.popup_error(f"Please provide {self.content_name_lower} number to remove.", location=DEFAULT_LOCATION)
            return False
        try:
            self.contents[element-1]
        except IndexError:
            sg.popup_error(f"{self.content_name_title} with number {element} does not exist.", location=DEFAULT_LOCATION)
            return False
        return True
    
    def handle_event(self, window, event, values):
        if event == self.add_event_key:
            self.request_new_element(window)
        if event == self.remove_event_key:
            self.request_remove_element(window)

    def data(self):
        return [
            el.data() if not isinstance(el, str) else el
            for el in self.contents
        ]
    
    def set_data(self, data):
        self.contents = data

class AgentManager(SimpleCollectionManager):
    def __init__(self):
        super().__init__("AGENT")

class ActionManager(SimpleCollectionManager):
    def __init__(self):
        super().__init__("ACTION")

class StateManager(SimpleCollectionManager):
    def __init__(self):
        super().__init__("STATE")

class TimeManager:
    def __init__(self):
        self.content_name = "TIME"
        self.unit_id = "-UNIT-"
        self.step_id = "-STEP-"
        self.termination_id = "-TERMINATION-"

        self.unit = "h"
        self.step = 1
        self.termination = 24

        self.display = [
            [sg.Text("Time settings:")],
            [sg.Text("Unit:"), sg.Text(self.unit, key=self.unit_id), sg.Button("Edit", key=f"{self.unit_id}BUTTON-")],
            [sg.Text("Step:"), sg.Text(f"{self.step}{self.unit}", key=self.step_id), sg.Button("Edit", key=f"{self.step_id}BUTTON-")],
            [sg.Text("Termination:"), sg.Text(f"{self.termination}{self.unit}", key=self.termination_id), sg.Button("Edit", key=f"{self.termination_id}BUTTON-")]
        ]
    
    
    def update(self, window):
        window[self.unit_id].update(self.unit)
        window[self.step_id].update(str(self.step) + self.unit)
        window[self.termination_id].update(str(self.termination) + self.unit)
    

    def edit_unit(self):
        unit = sg.popup_get_text(f"Enter new time unit", title="Edit time unit", location=DEFAULT_LOCATION)
        if unit is None:
            return
        if unit == "":
            sg.PopupError(f"Please provide new time unit", title="Edit time unit", location=DEFAULT_LOCATION)
            return
        self.unit = unit

    def edit_step(self):
        step = sg.popup_get_text(f"Enter new time step", title="Edit time step", location=DEFAULT_LOCATION)
        if step is None:
            return
        if step == "":
            sg.PopupError(f"Please provide new time step", title="Edit time step", location=DEFAULT_LOCATION)
            return
        try:
            step = int(step)
        except ValueError:
            sg.PopupError(f"Time step must be an integer", title="Edit time step", location=DEFAULT_LOCATION)
            return
        self.step = step

    def edit_termination(self):
        termination = sg.popup_get_text(f"Enter new time termination", title="Edit time termination", location=DEFAULT_LOCATION)
        if termination is None:
            return
        if termination == "":
            sg.PopupError(f"Please provide new time termination", title="Edit time termination", location=DEFAULT_LOCATION)
            return
        try:
            termination = int(termination)
        except ValueError:
            sg.PopupError(f"Time termination must be an integer", title="Edit time termination", location=DEFAULT_LOCATION)
            return
        self.termination = termination

    def handle_event(self, window, event, values):
        button_event = event.replace("BUTTON-", "")
        if button_event == self.unit_id:
            self.edit_unit()
        if button_event == self.step_id:
            self.edit_step()
        if button_event == self.termination_id:
            self.edit_termination()
        self.update(window)

    def data(self):
        return {
            "unit": self.unit,
            "step": self.step,
            "termination": self.termination,
        }

    def set_data(self, data):
        self.unit = data["unit"]
        self.step = data["step"]
        self.termination = data["termination"]

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


class ACSManager(SimpleCollectionManager):
    def __init__(self, actions_manager, agent_manager, time_manager):
        super().__init__("ACS")
        self.actions_manager = actions_manager
        self.agent_manager = agent_manager
        self.time_manager = time_manager
        self.content_name_lower = "ACS"
        self.content_name_title = "ACS"
        self.display[0] = [sg.Text(f"{self.content_name_title}s:")]
        self.display = self.display + [[sg.Text(f"ACS are comma separated 3-tuples. Outer brackets and quotation marks are optional.")]]
    
    def remove_fluff(self, element):
        element = element.replace("(" , "")
        element = element.replace(")" , "")
        element = element.replace("\"", "")
        element = element.replace("'" , "")
        return element

    def validate_add(self, element):
        if element is None:
            return False
        element = self.remove_fluff(element)
        try:
            action, agent, time = element.split(",")
            agent = agent.strip()
            action = action.strip()
        except ValueError:
            sg.popup_error("Please provide a tuple of 3 values separated by commas", location=DEFAULT_LOCATION)
            return False
        
        if action not in self.actions_manager.contents:
            sg.popup_error(f"Action '{action}' does not exist.", location=DEFAULT_LOCATION)
            return False
        if agent not in self.agent_manager.contents:
            sg.popup_error(f"Agent '{agent}' does not exist.", location=DEFAULT_LOCATION)
            return False
        try:
            time = time.replace(self.time_manager.unit, "")
            time = int(time)
        except ValueError:
            sg.popup_error("Time needs to be an integer", location=DEFAULT_LOCATION)
            return False
        if time % self.time_manager.step != 0:
            sg.popup_error("Time needs to be a multiple of the time step", location=DEFAULT_LOCATION)
            return False
        if time > self.time_manager.termination:
            sg.popup_error("Time needs to be before termination", location=DEFAULT_LOCATION)
            return False
        element_dataclass = ACS(action, agent, time, self.time_manager)
        if not super().validate_add(element_dataclass):
            return False
        return element_dataclass

    def preprocess_element(self, element):
        return self.validate_add(element) # jank
    
    def handle_event(self, window, event, values):
        if "TIME" in event:
            self.update(window)
        return super().handle_event(window, event, values)
    
    def set_data(self, data):
        self.contents = [ACS(time_manager=self.time_manager, **data_item) for data_item in data]

def create_literal_parser(literals):
    quoted_literal = (pp.Suppress("'") | pp.Suppress("\"")) + pp.Literal(literals[0]) + (pp.Suppress("'") | pp.Suppress("\""))
    literal_parser = pp.Literal(literals[0]) | quoted_literal
    for state in literals[1:]:
        quoted_literal = (pp.Suppress("'") | pp.Suppress("\"")) + pp.Literal(literals[0]) + (pp.Suppress("'") | pp.Suppress("\""))
        literal_parser |= pp.Literal(state) | quoted_literal
    return literal_parser

def create_logic_parser(states):
    quoted_literal = (pp.Suppress("'") | pp.Suppress("\"")) + pp.Literal(states[0]) + (pp.Suppress("'") | pp.Suppress("\""))
    states_parser = pp.Literal(states[0]) | quoted_literal
    for state in states[1:]:
        quoted_literal = (pp.Suppress("'") | pp.Suppress("\"")) + pp.Literal(states[0]) + (pp.Suppress("'") | pp.Suppress("\""))
        states_parser |= pp.Literal(state) | quoted_literal
    
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

def parse_logic(expression, states):
    if len(states) == 0:
        sg.popup_error("At least one fluent is required to create a logic expression", location=DEFAULT_LOCATION)
        return False
    logic_expr = create_logic_parser(states)
    try:
        # print(states, logic_expr, expression)
        parsed_expression = logic_expr.parse_string(expression, parse_all=True).as_list()
    except pp.exceptions.ParseException as e:
        sg.popup_error(f"Unable to parse expression.\nParser message: {e}", location=DEFAULT_LOCATION)
        return False
    # print(parsed_expression)
    return parsed_expression

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

class OBSManager(SimpleCollectionManager):
    def __init__(self, state_manager, time_manager):
        super().__init__("OBS")
        self.state_manager = state_manager
        self.time_manager = time_manager
        self.content_name_lower = "OBS"
        self.content_name_title = "OBS"
        self.display[0] = [sg.Text(f"{self.content_name_title}s:")]
        self.display = self.display + [[sg.Text(f"OBS are comma separated 2-tuples. Outer brackets and quotation marks are optional.\n" +
                                                 "Parsing of logic expressions require fluents to be defined beforehand.")]]
    
    def remove_fluff(self, element):
        if element[-1] == ")":
            element = element[1:]
            element = element[:-1]
        return element

    def validate_add(self, element):
        if element is None:
            return False
        element = self.remove_fluff(element)
        try:
            expression, time = element.split(",")
        except ValueError:
            sg.popup_error("Please provide a tuple of 2 values separated by commas", location=DEFAULT_LOCATION)
            return False
        try:
            time = time.replace(self.time_manager.unit, "")
            time = int(time)
        except ValueError:
            sg.popup_error("Time needs to be an integer", location=DEFAULT_LOCATION)
            return False
        if time % self.time_manager.step != 0:
            sg.popup_error("Time needs to be a multiple of the time step", location=DEFAULT_LOCATION)
            return False
        if time > self.time_manager.termination:
            sg.popup_error("Time needs to be before termination", location=DEFAULT_LOCATION)
            return False
        element_dataclass = OBS(expression, time, self.state_manager, self.time_manager)
        if not element_dataclass.parse():
            return False
        if not super().validate_add(element_dataclass):
            return False
        return element_dataclass

    def preprocess_element(self, element):
        return self.validate_add(element) # jank
    
    def handle_event(self, window, event, values):
        if "TIME" in event:
            self.update(window)
        return super().handle_event(window, event, values)

    def set_data(self, data):
        self.contents = [OBS(state_manager=self.state_manager, time_manager=self.time_manager, **data_item) for data_item in data]

@dataclass
class Statement:
    original_expression: str
    action_manager: ActionManager
    agent_manager: AgentManager
    state_manager: StateManager
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

        action_parser = create_literal_parser(self.action_manager.contents)

        if len(self.agent_manager.contents) == 0: 
            # agent count CAN be 0, statements like "shoot causes not gun loaded"
            agent_parser = pp.Empty()
            agent_parser.set_parse_action(lambda: [None])
        else:
            agent_parser = create_literal_parser(self.agent_manager.contents)
            agent_parser = pp.Opt(pp.Suppress("by") + agent_parser, default=None)

        statement_type_parser = pp.Literal("releases") | pp.Literal("causes")

        state_parser = create_literal_parser(self.state_manager.contents)
        
        effect_parser = pp.delimitedList(pp.Opt("not") + state_parser, delim="and")
        effect_parser.set_parse_action(lambda toks: [toks])

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

class StatementManager(SimpleCollectionManager):
    def __init__(self, action_manager, agent_manager, state_manager):
        super().__init__("STATEMENT")
        self.action_manager = action_manager
        self.agent_manager = agent_manager
        self.state_manager = state_manager
        self.display = self.display + [[sg.Text(f"Parsing of statements expressions requires at least one action and fluent to be defined beforehand.")]]

    def validate_add(self, element):
        if element is None:
            return False
        element_dataclass = Statement(element, self.action_manager, self.agent_manager, self.state_manager)
        if not element_dataclass.parse():
            return False
        if not super().validate_add(element_dataclass):
            return False
        return element_dataclass

    def preprocess_element(self, element):
        return self.validate_add(element) # jank
    
    def set_data(self, data):
        self.contents = [
            Statement(
                action_manager=self.action_manager,
                agent_manager=self.agent_manager,
                state_manager=self.state_manager,
                **data_item
            ) 
            for data_item in data
        ]

class ManagerManager():
    def __init__(self, *managers):
        self.managers = managers

    def handle_event(self, window, event, values):
        for manager in self.managers:
            manager.handle_event(window, event, values)

    def data(self):
        return {
            manager.content_name: manager.data()
            for manager in self.managers
        }

    def set_data(self, data):
        for key, value in data.items():
            for manager in self.managers:
                if key == manager.content_name:
                    manager.set_data(value)

    def update_all(self, window):
        for manager in self.managers:
            manager.update(window)

def main():
    agent_manager = AgentManager()
    action_manager = ActionManager()
    state_manager = StateManager()
    time_manager = TimeManager()
    acs_manager = ACSManager(action_manager, agent_manager, time_manager)
    obs_manager = OBSManager(state_manager, time_manager)
    statement_manager = StatementManager(action_manager, agent_manager, state_manager)

    manager_manager = ManagerManager(
        agent_manager,
        action_manager,
        state_manager,
        time_manager,
        acs_manager,
        obs_manager,
        statement_manager,
    )

    serdelizer_layout = [
        [sg.Multiline("", key="-SERDE-IO-", size=(100, 30))],
        [sg.Text("Press serialize to dump application state")],
        [sg.Button("Serialize"), sg.Button("Deserialize")]
    ]

    layout = [[ sg.TabGroup([[
        sg.Tab("Agents", agent_manager.display),
        sg.Tab("Actions", action_manager.display),
        sg.Tab("Fluents", state_manager.display),
        sg.Tab("Time", time_manager.display),
        sg.Tab("ACS", acs_manager.display),
        sg.Tab("OBS", obs_manager.display),
        sg.Tab("Statements", statement_manager.display),
        sg.Tab("Save", serdelizer_layout)
    ]], size=(600, 480)) ]]

    window = sg.Window('KRR', layout, location=DEFAULT_LOCATION)

    restart = False
    try:
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                break
            
            print(event, values)
            manager_manager.handle_event(window, event, values)

            if event == "Serialize":
                data = manager_manager.data()
                window["-SERDE-IO-"].update(json.dumps(data, indent=2))
            if event == "Deserialize":
                data = values["-SERDE-IO-"]
                try:
                    data = json.loads(data)
                except Exception:
                    sg.popup_error("Unable to parse serialized application data.", location=DEFAULT_LOCATION)
                    continue
                manager_manager.set_data(data)
                manager_manager.update_all(window)

    finally:
        window.close()
    if restart:
        main()

if __name__ == "__main__":
    main()