import os,sys

import PySimpleGUI as sg
from frontend.utils import get_default_location, create_literal_parser, create_logic_parser
from frontend.data import ACS, OBS, Statement, Query
from backend.base import BackendException
from backend import parse_data, run_queries

import traceback

DEFAULT_LOCATION = get_default_location()

class CheatSheet:
    def __init__(self, prefix, source_element_key, key):
        self.prefix = "Currently available " + prefix
        self.source_element_key = source_element_key
        self.key = key
        self.display = sg.Multiline(prefix + "\n", expand_x=True, size=(10, 6), key=self.key)

    @staticmethod
    def from_manager(manager, who_asked):
        return CheatSheet(
            prefix = f"{manager.content_name_lower}s:",
            source_element_key = manager.contents_display_id,
            key=f"-CS-{who_asked}{manager.contents_display_id}"
        )

    def update(self, window):
        element_contents = window[self.source_element_key].get()
        window[self.key].update(
            self.prefix + "\n" + element_contents
        )

class CollectionManager:
    def __init__(self, contents_display_id):
        self.contents_display_id = contents_display_id
        self.contents = []
        self.contents_display = sg.Multiline("", key=contents_display_id, expand_x=True, size=(10, 10), disabled=True)
    
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
    
    def popup_add(self, **_):
        raise NotImplementedError()
    
    def preprocess_element(self, element):
        return element
    
    def request_new_element(self, window, **kwargs):
        #element = self.popup_add(**kwargs)
        element = window[self.text_field_key].get()
        element = element.lower()
        if not self.validate_add(element, **kwargs):
            return
        element = self.preprocess_element(element, **kwargs)
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
    def __init__(self, content_name ):
        super().__init__(f"-{content_name}-")
        self.content_name = content_name
        self.content_name_lower = content_name.lower()
        self.content_name_title = content_name.title()
        self.add_event_key = f"-{self.content_name}-ADD-"
        self.remove_event_key = f"-{self.content_name}-REMOVE-"
        self.text_field_key = f"-{self.content_name}-INPUT-"
        self.display = [
            [sg.Text(f"{self.content_name_title}s:", key=f"-{content_name}-HEADER-")],
            [self.contents_display],
            [sg.Input("", key=self.text_field_key), sg.Button("Add", key=self.add_event_key, button_color=("white", "green"))],
            [sg.Button("Remove", key=self.remove_event_key, button_color=("white", "red"))]
        ]

    def popup_add(self, **_):
        text = sg.popup_get_text(f"Enter new {self.content_name_lower}:", title=f"{self.content_name_title} creation dialog", location=DEFAULT_LOCATION)
        if text is None:
            return text
        else:
            return text.lower()
    
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

    def update(self, window):
        return super().update(window)

class AgentManager(SimpleCollectionManager):
    def __init__(self):
        super().__init__("AGENT")
        self.display = self.display + [[sg.Text(f"To add an agent, type the name into the text field and press the 'Add' button.\nTo remove an agent, press the 'Remove' button to open the removal dialog.")]]

class ActionManager(SimpleCollectionManager):
    def __init__(self):
        super().__init__("ACTION")
        self.display = self.display + [[sg.Text(f"To add an action, type the name into the text field and press the 'Add' button.\nTo remove an action, press the 'Remove' button to open the removal dialog.")]]

class StateManager(SimpleCollectionManager):
    def __init__(self):
        super().__init__("STATE")
        self.display = self.display + [[sg.Text(f"To add a fluent, type the name into the text field and press the 'Add' button.\nTo remove a fluent, press the 'Remove' button to open the removal dialog.")]]

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
            #[sg.Text("Step:"), sg.Text(f"{self.step}{self.unit}", key=self.step_id), sg.Button("Edit", key=f"{self.step_id}BUTTON-")],
            [sg.Text("Termination:"), sg.Text(f"{self.termination}{self.unit}", key=self.termination_id), sg.Button("Edit", key=f"{self.termination_id}BUTTON-")]
        ]
    
    
    def update(self, window):
        window[self.unit_id].update(self.unit)
        #window[self.step_id].update(str(self.step) + self.unit)
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

class ACSManager(SimpleCollectionManager):
    def __init__(self, actions_manager, agent_manager, time_manager):
        super().__init__("ACS")
        self.actions_manager = actions_manager
        self.agent_manager = agent_manager
        self.time_manager = time_manager
        self.content_name_lower = "ACS"
        self.content_name_title = "ACS"

        self.action_cs = CheatSheet.from_manager(actions_manager, self.content_name)
        self.agent_cs = CheatSheet.from_manager(agent_manager, self.content_name)

        self.display[0] = [sg.Text(f"{self.content_name_title}s:")]
        self.display = self.display + [
            [sg.Button("Insert Template", key=f"-{self.content_name}-TEMPLATE-")],

            [sg.Text(f"ACS are comma separated triples of Action, Agent, Time.\n"+
                     "Type these 3 elements into the text field, separated by commas, then press the 'Add' button.\n"+
                     "To remove an element press the 'Remove' button to open the deletion dialog.\n"+
                     "Press the 'Insert Template' button to insert a template.")],
            [self.action_cs.display, self.agent_cs.display]
            ]
    
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
        return self.validate_split(action, agent, time)

    def validate_split(self, action, agent, time):
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
        if time in [item.time for item in self.contents]:
            sg.popup_error(f'Only one ACS can exist for given time step')
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
        if event == f"-{self.content_name}-TEMPLATE-":
            window[self.text_field_key].update("(ACTION, AGENT, TIME)")
        if "TIME" in event:
            self.update(window)
        return super().handle_event(window, event, values)
    
    def set_data(self, data):
        self.contents = [ACS(time_manager=self.time_manager, **data_item) for data_item in data]

    def update(self, window):
        self.action_cs.update(window)
        self.agent_cs.update(window)
        return super().update(window)

class OBSManager(SimpleCollectionManager):
    def __init__(self, state_manager, time_manager):
        super().__init__("OBS")
        self.state_manager = state_manager
        self.time_manager = time_manager
        self.content_name_lower = "OBS"
        self.content_name_title = "OBS"
        self.state_cs = CheatSheet.from_manager(state_manager, "OBS")

        self.display[0] = [sg.Text(f"{self.content_name_title}s:")]
        self.display = self.display + [
            [sg.Button("Insert Template", key=f"-{self.content_name}-TEMPLATE-")],
            [sg.Text(f"OBS are comma separated pairs of a logic expression and time.\n" +
                     "Logic expressions are a text representation using English equivalents of symbols ('not' (unary negation), 'and', 'or', 'implies', 'if and only if').\n" +
                     "Leaves of the expression are fluents. Brackets denote precedence: '(State1 or not State2) and State3'.\n" +
                     "Enter the logic expression and time, separated by a comma, into the text field, which will then be parsed. Confirm with 'Add' button.\n" +
                     "Press the 'Insert Template' button to insert a template.")],
            [self.state_cs.display]
        ]
    
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
        if event == f"-{self.content_name}-TEMPLATE-":
            window[self.text_field_key].update("(FORMULA, TIME)")
        if "TIME" in event:
            self.update(window)
        return super().handle_event(window, event, values)

    def set_data(self, data):
        self.contents = [OBS(state_manager=self.state_manager, time_manager=self.time_manager, **data_item) for data_item in data]
        for statement in self.contents:
            if not statement.parse():
                raise ValueError()
            
    def update(self, window):
        self.state_cs.update(window)
        return super().update(window)


class StatementManager(SimpleCollectionManager):
    def __init__(self, action_manager, agent_manager, state_manager):
        super().__init__("STATEMENT")
        self.action_manager = action_manager
        self.agent_manager = agent_manager
        self.state_manager = state_manager

        self.action_cs = CheatSheet.from_manager(action_manager, self.content_name)
        self.agent_cs = CheatSheet.from_manager(agent_manager, self.content_name)
        self.state_cs = CheatSheet.from_manager(state_manager, self.content_name)

        self.display = self.display + [
            [
                sg.Button("Insert 'Causes' Template", key=f"-{self.content_name}-TEMPLATE-CAUSES-"), 
                sg.Button("Insert 'Releases' Template", key=f"-{self.content_name}-TEMPLATE-RELEASES-"), 
            ],
            [sg.Text(f"Statement syntax is split between two types: causes statements and releases statements\n"+
                     "Causes statements have the following syntax: ACTION by AGENT causes FORMULA [if FORMULA]\n" +
                     "Releases statements have the following syntax: ACTION by AGENT releases FLUENT [if FORMULA]\n" +
                     "Capital letters denote appropriate objects within the scenario, parts of the syntax in brackets [] are optional\n"+
                     "Enter the statement into the text field, which will then be parsed. Confirm with 'Add' button.\n" +
                     "Press one of the 'Insert Template' buttons to insert a template.")],
            [self.action_cs.display, self.agent_cs.display, self.state_cs.display]
        ]

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
        for statement in self.contents:
            if not statement.parse():
                raise ValueError()

    def handle_event(self, window, event, values):
        if event == f"-{self.content_name}-TEMPLATE-CAUSES-":
            window[self.text_field_key].update("ACTION by AGENT causes FORMULA if FORMULA")
        if event == f"-{self.content_name}-TEMPLATE-RELEASES-":
            window[self.text_field_key].update("ACTION by AGENT releases FLUENT if FORMULA")
        return super().handle_event(window, event, values)
    
    def update(self, window):
        self.action_cs.update(window)
        self.agent_cs.update(window)
        self.state_cs.update(window)
        return super().update(window)

class QueryManager(SimpleCollectionManager):
    def __init__(self, action_manager, agent_manager, state_manager, time_manager):
        super().__init__("QUERY")
        self.action_manager = action_manager
        self.agent_manager = agent_manager
        self.state_manager = state_manager
        self.time_manager = time_manager

        self.action_cs = CheatSheet.from_manager(action_manager, self.content_name)
        self.agent_cs = CheatSheet.from_manager(agent_manager, self.content_name)
        self.state_cs = CheatSheet.from_manager(state_manager, self.content_name)

        self.add_fluent_query_event_key = "-QUERY-ADD-FLUENT-"
        self.add_action_query_event_key = "-QUERY-ADD-ACTION-"
        self.add_agent_query_event_key = "-QUERY-ADD-AGENT-"

        self.display = self.display + [
            # [sg.Text(f"Queries:")],
            # self.display[1],
            # [self.display[2][0]],
            # [sg.Button("Add state query", key=self.add_fluent_query_event_key),
            # sg.Button("Add action query", key=self.add_action_query_event_key),
            # sg.Button("Add agent query", key=self.add_agent_query_event_key),
            # sg.Button("Remove", key=self.remove_event_key)],
            [
                sg.Button("Insert 'Neccessary State' Template", key=f"-{self.content_name}-TEMPLATE-NECESSARY-"), 
                sg.Button("Insert 'Possibly State' Template", key=f"-{self.content_name}-TEMPLATE-POSSIBLY-"), 
                sg.Button("Insert 'Action' Template", key=f"-{self.content_name}-TEMPLATE-ACTION-"), 
                sg.Button("Insert 'Agent' Template", key=f"-{self.content_name}-TEMPLATE-AGENT-"), 
            ],
            [sg.Text(f"Query syntax is split between 4 types: necessary state, possible state, action, and agent queries.\n"+
                     "Necessary state queries have the following syntax: Necessary FORMULA at TIME [when Sc]\n" +
                     "Possible state queries have the following syntax: Possibly FORMULA at TIME [when Sc]\n" +
                     "Action queries have the following syntax: Necessary ACTION by AGENT at TIME [when Sc]\n" +
                     "Agent queries have the following syntax: Agent AGENT is active [when Sc]\n" +
                     "Capital letters denote appropriate objects within the scenario, parts of the syntax in brackets [] are optional\n"+
                     "Enter the query into the text field, which will then be parsed. Confirm with the appropriate 'Add' button.\n" +
                     "Press one of the 'Insert Template' buttons to insert a template.")],
            [self.action_cs.display, self.agent_cs.display, self.state_cs.display]
        ]

    def infer_query_type(self, element):
        for query_type in ["fluent", "action", "agent"]:
            element_dataclass = Query(element, query_type, self.state_manager, self.action_manager, self.agent_manager,  self.time_manager, quiet=True)
            if element_dataclass.parse():
                return element_dataclass
        sg.popup_error("Could not infer query type.") # parser messages are bad but this is worse
        return False

    def validate_add(self, element, query_type="infer"):
        if element is None:
            return False
        if query_type == "infer":
            element_dataclass = self.infer_query_type(element)
            if not element_dataclass:
                return False
        else:
            element_dataclass = Query(element, query_type, self.state_manager, self.action_manager, self.agent_manager,  self.time_manager)
            if not element_dataclass.parse():
                return False
        if not super().validate_add(element_dataclass):
            return False
        return element_dataclass

    def handle_event(self, window, event, values):
        super().handle_event(window, event, values)
        if event == f"-{self.content_name}-TEMPLATE-NECESSARY-":
            window[self.text_field_key].update("Necessary FORMULA at TIME when Sc")
        if event == f"-{self.content_name}-TEMPLATE-POSSIBLY-":
            window[self.text_field_key].update("Possibly FORMULA at TIME when Sc")
        if event == f"-{self.content_name}-TEMPLATE-ACTION-":
            window[self.text_field_key].update("Necessary ACTION by AGENT at TIME when Sc")
        if event == f"-{self.content_name}-TEMPLATE-AGENT-":
            window[self.text_field_key].update("Agent AGENT is active when Sc")

        if event == self.add_fluent_query_event_key:
            self.request_new_element(window, query_type="fluent")
        if event == self.add_action_query_event_key:
            self.request_new_element(window, query_type="action")
        if event == self.add_agent_query_event_key:
            self.request_new_element(window, query_type="agent")
    
    def preprocess_element(self, element, query_type="infer"):
        return self.validate_add(element, query_type) # jank
    
    def set_data(self, data):
        self.contents = [
            Query(
                action_manager=self.action_manager,
                agent_manager=self.agent_manager,
                state_manager=self.state_manager,
                time_manager=self.time_manager,
                **data_item
            ) 
            for data_item in data
        ]
        for statement in self.contents:
            if not statement.parse():
                raise ValueError()
            
    def update(self, window):
        self.action_cs.update(window)
        self.agent_cs.update(window)
        self.state_cs.update(window)
        return super().update(window)
    
class ScenarioManager:
    def __init__(self, manager_manager):
        # self.scenario_compile_status_key = "-SCENARIO-COMPILE-STATUS-"
        # self.compile_button_key = "-SCENARIO-COMPILE-SCENARIO-BUTTON-"
        self.run_query_button_key = "-SCENARIO-RUN-QUERY-BUTTON-"
        self.run_query_results = "-SCENARIO-RESULTS-"
        self.manager_manager = manager_manager
        # self.scenario_compile_status = "not compiled"
        self.display = [
            [
                sg.Text("Scenario status: "), 
                # sg.Text(self.scenario_compile_status, key=self.scenario_compile_status_key), 
                # sg.Button("Compile", key=self.compile_button_key), 
                sg.Button("Run queries", key=self.run_query_button_key, disabled=False),
            ],
                [sg.Multiline("", key=self.run_query_results, size=(100, 30), disabled=True)],
            
        ]
    
    def handle_event(self, window, event):
        print(event)
        # if event == self.compile_button_key:
        #     self.compile_button_func(window)
        if event == self.run_query_button_key:
            self.run_query_button_func(window)
    
    # def compile_button_func(self, window):
        # try:
        #     data: dict = parse_data(data=self.manager_manager.data())
        #     results: dict = run_queries(data)
        #     msg = "\n".join(f'{k:>3}. {v}' for k,v in results.items())
        # except BackendException as e:
        #     msg = getattr(e, 'message', repr(e))
        # except Exception as e:
        #     print(traceback.format_exc())
        #     msg = 'Something went wrong'
        # window[self.scenario_compile_status_key] = 'Compiled'

    def run_query_button_func(self, window):
        try:
            data: dict = parse_data(data=self.manager_manager.data())
            results: dict = run_queries(data)
            msg = "\n".join(f'{k:>3}. {v}' for k,v in results.items())
        except BackendException as e:
            msg = getattr(e, 'message', repr(e))
        except Exception as e:
            print(traceback.format_exc())
            msg = 'Something went wrong'
        window[self.run_query_results].update(msg)

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
