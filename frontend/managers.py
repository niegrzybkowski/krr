import os,sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__),'..')))

import PySimpleGUI as sg
from frontend.utils import get_default_location, create_literal_parser, create_logic_parser
from frontend.data import ACS, OBS, Statement, Query
from backend.base import BackendException
from backend import parse_data, run_queries

import traceback

DEFAULT_LOCATION = get_default_location()

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
    
    def popup_add(self, **_):
        raise NotImplementedError()
    
    def preprocess_element(self, element):
        return element
    
    def request_new_element(self, window, **kwargs):
        #element = self.popup_add(**kwargs)
        element = window[self.text_field_key].get()
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
    def __init__(self, content_name):
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
            [sg.Input("", key=self.text_field_key), sg.Button("Add", key=self.add_event_key), sg.Button("Remove", key=self.remove_event_key)]
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

class QueryManager(SimpleCollectionManager):
    def __init__(self, action_manager, agent_manager, state_manager, time_manager):
        super().__init__("QUERY")
        self.action_manager = action_manager
        self.agent_manager = agent_manager
        self.state_manager = state_manager
        self.time_manager = time_manager

        self.add_fluent_query_event_key = "-QUERY-ADD-FLUENT-"
        self.add_action_query_event_key = "-QUERY-ADD-ACTION-"
        self.add_agent_query_event_key = "-QUERY-ADD-AGENT-"

        self.display = [
            [sg.Text(f"Queries:")],
            self.display[1],
            [self.display[2][0]],
            [sg.Button("Add state query", key=self.add_fluent_query_event_key),
            sg.Button("Add action query", key=self.add_action_query_event_key),
            sg.Button("Add agent query", key=self.add_agent_query_event_key),
            sg.Button("Remove", key=self.remove_event_key)]
        ]

    def validate_add(self, element, query_type):
        if element is None:
            return False
        element_dataclass = Query(element, query_type, self.state_manager, self.action_manager, self.agent_manager,  self.time_manager)
        if not element_dataclass.parse():
            return False
        if not super().validate_add(element_dataclass):
            return False
        return element_dataclass

    def handle_event(self, window, event, values):
        super().handle_event(window, event, values)

        if event == self.add_fluent_query_event_key:
            self.request_new_element(window, query_type="fluent")
        if event == self.add_action_query_event_key:
            self.request_new_element(window, query_type="action")
        if event == self.add_agent_query_event_key:
            self.request_new_element(window, query_type="agent")
    
    def preprocess_element(self, element, query_type):
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
