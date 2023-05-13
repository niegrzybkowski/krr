import PySimpleGUI as sg


sg.theme('dark grey 9')   

DEFAULT_LOCATION = (100,100)

class CollectionManager:
    def __init__(self, contents_display_id):
        self.contents_display_id = contents_display_id
        self.contents = []
        self.contents_display = sg.Text("", key=contents_display_id)
    
    def update(self, window):
        window[self.contents_display_id].update("\n".join(self.contents))

    def validate_add(self, element):
        raise NotImplementedError()
    
    def popup_add(self):
        raise NotImplementedError()

    def request_new_element(self, window):
        element = self.popup_add()
        if not self.validate_add(element):
            return
        self.contents.append(element)
        self.update(window)

    def validate_remove(self, element):
        raise NotImplementedError()
    
    def popup_remove(self):
        raise NotImplementedError()

    def request_remove_element(self, window):
        element = self.popup_remove()
        if not self.validate_remove(element):
            return
        self.contents.remove(element)
        self.update(window)

class SimpleCollectionManager(CollectionManager):
    def __init__(self, content_name):
        super().__init__(f"-{content_name}-")
        self.content_name = content_name
        self.add_event_key = f"-{self.content_name}-ADD-"
        self.remove_event_key = f"-{self.content_name}-REMOVE-"
        self.display = [
            [sg.Text(f"{self.content_name.title()}s:")],
            [self.contents_display],
            [sg.Button("Add", key=self.add_event_key), sg.Button("Remove", key=self.remove_event_key)]
        ]

    def popup_add(self):
        return sg.popup_get_text(f"Enter new {self.content_name.lower()} name:", title=f"{self.content_name.title()} creation dialog", location=DEFAULT_LOCATION)
    
    def popup_remove(self):
        return sg.popup_get_text(f"Enter {self.content_name.lower()} name to remove:", title=f"{self.content_name.title()} deletion dialog", location=DEFAULT_LOCATION)

    def validate_add(self, element):
        if element is None:
            return False
        if element == "":
            sg.popup_error(f"{self.content_name.title()} name cannot be empty", location=DEFAULT_LOCATION)
            return False
        if element in self.contents:
            sg.popup_error(f"{self.content_name.title()} with name '" + element +"' already exists",  location=DEFAULT_LOCATION)
            return False
        return True
    
    def validate_remove(self, element):
        if element is None:
            return False
        if element == "":
            sg.popup_error(f"{self.content_name.title()} name cannot be empty", location=DEFAULT_LOCATION)
            return False
        if element not in self.contents:
            sg.popup_error(f"{self.content_name.title()} with name '" + element +"' doesn't exist",  location=DEFAULT_LOCATION)
            return False
        return True
    
    def handle_event(self, window, event, values):
        if event == self.add_event_key:
            self.request_new_element(window)
        if event == self.remove_event_key:
            self.request_remove_element(window)

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
        self.unit_id = "-UNIT-"
        self.step_id = "-STEP-"
        self.termination_id = "-TERMINATION-"

        self.unit = "h"
        self.step = "1"
        self.termination = "24"

        self.display = [
            [sg.Text("Time settings:")],
            [sg.Text("Unit:"), sg.Text("h", key=self.unit_id), sg.Button("Edit", key=f"{self.unit_id}BUTTON-")],
            [sg.Text("Step:"), sg.Text("1h", key=self.step_id), sg.Button("Edit", key=f"{self.step_id}BUTTON-")],
            [sg.Text("Termination:"), sg.Text("24h", key=self.termination_id), sg.Button("Edit", key=f"{self.termination_id}BUTTON-")]
        ]
    
    
    def update(self, window):
        window[self.unit_id].update(self.unit)
        window[self.step_id].update(self.step + self.unit)
        window[self.termination_id].update(self.termination + self.unit)
    

    def edit_unit(self):
        unit = sg.popup_get_text(f"Enter new time unit", title="Edit time unit", location=DEFAULT_LOCATION)
        if unit is None:
            return
        if unit == "":
            sg.PopupError(f"Please provide new time unit", title="Edit time unit", location=DEFAULT_LOCATION)
        self.unit = unit

    def edit_step(self):
        step = sg.popup_get_text(f"Enter new time step", title="Edit time step", location=DEFAULT_LOCATION)
        if step is None:
            return
        if step == "":
            sg.PopupError(f"Please provide new time step", title="Edit time step", location=DEFAULT_LOCATION)
        try:
            int(step)
        except ValueError:
            sg.PopupError(f"Time step must be an integer", title="Edit time step", location=DEFAULT_LOCATION)
        self.step = step

    def edit_termination(self):
        termination = sg.popup_get_text(f"Enter new time termination", title="Edit time termination", location=DEFAULT_LOCATION)
        if termination is None:
            return
        if termination == "":
            sg.PopupError(f"Please provide new time termination", title="Edit time termination", location=DEFAULT_LOCATION)
        try:
            int(termination)
        except ValueError:
            sg.PopupError(f"Time termination must be an integer", title="Edit time termination", location=DEFAULT_LOCATION)
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

class ManagerManager():
    def __init__(self, *managers):
        self.managers = managers

    def handle_event(self, window, event, values):
        for manager in self.managers:
            manager.handle_event(window, event, values)


agent_manager = AgentManager()
action_manager = ActionManager()
state_manager = StateManager()
time_manager = TimeManager()

manager_manager = ManagerManager(
    agent_manager,
    action_manager,
    state_manager,
    time_manager
)

layout = sg.TabGroup([[
    sg.Tab("Agents", agent_manager.display),
    sg.Tab("Actions", action_manager.display),
    sg.Tab("States", state_manager.display),
    sg.Tab("Time", time_manager.display),
]])

window = sg.Window('KRR', [[layout]], location=DEFAULT_LOCATION)


try:
    while True:
        event, values = window.read()
        if event == sg.WIN_CLOSED:
            break
        
        print(event, values)
        manager_manager.handle_event(window, event, values)
            
finally:
    window.close()