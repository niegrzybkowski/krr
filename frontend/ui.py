import PySimpleGUI as sg
import json
from frontend.managers import *
from frontend.utils import get_default_location

sg.theme('dark grey 9')   

ZERO_DATA = {
  "AGENT": [],
  "ACTION": [],
  "STATE": [],
  "TIME": {
    "unit": "h",
    "step": 1,
    "termination": 24
  },
  "ACS": [],
  "OBS": [],
  "STATEMENT": [],
  "QUERY": []
}

DEFAULT_LOCATION = get_default_location()

def main():
    agent_manager = AgentManager()
    action_manager = ActionManager()
    state_manager = StateManager()
    time_manager = TimeManager()
    acs_manager = ACSManager(action_manager, agent_manager, time_manager)
    obs_manager = OBSManager(state_manager, time_manager)
    statement_manager = StatementManager(action_manager, agent_manager, state_manager)
    query_manager = QueryManager(action_manager, agent_manager, state_manager, time_manager=time_manager)

    manager_manager = ManagerManager(
        agent_manager,
        action_manager,
        state_manager,
        time_manager,
        acs_manager,
        obs_manager,
        statement_manager,
        query_manager,
    )

    scenario_manager = ScenarioManager(manager_manager)

    serdelizer_layout = [
        [sg.Text("Press serialize to dump application state. You can then copy the contents of the below text field into a file to save the scenario.\n" + 
                 "Press deserialize to load application state. Similarly, you can copy contents into the text field below.")],
        [sg.Button("Serialize"), sg.Button("Deserialize")],
        [sg.Multiline("", key="-SERDE-IO-", size=(100, 30))],
        [sg.Button("-SUBMIT-", bind_return_key=True, visible=False)]
    ]

    layout = [
        [sg.Button("Enter new domain", key="-RESET-", button_color=("white", "green"))],
        [ sg.TabGroup([[
        sg.Tab("Agents", agent_manager.display, key=agent_manager.content_name),
        sg.Tab("Actions", action_manager.display, key=action_manager.content_name),
        sg.Tab("Fluents", state_manager.display, key=state_manager.content_name),
        sg.Tab("Time", time_manager.display),
        sg.Tab("ACS", acs_manager.display, key=acs_manager.content_name),
        sg.Tab("OBS", obs_manager.display, key=obs_manager.content_name),
        sg.Tab("Statements", statement_manager.display, key=statement_manager.content_name),
        sg.Tab("Query", query_manager.display, key=query_manager.content_name),
        sg.Tab("Query Results", scenario_manager.display),
        sg.Tab("Save", serdelizer_layout),
    ]]
    , key="-TAB-"
    , expand_x=True
    , expand_y=True
    ) ]]

    window = sg.Window('KRR', layout, location=DEFAULT_LOCATION, resizable =True, finalize=True)
    window.set_min_size((500, 350))

    try:
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                break

            print(event, values)

            if event == "-SUBMIT-":
                window.write_event_value(f"-{values['-TAB-']}-ADD-", values)
            
            manager_manager.handle_event(window, event, values)
            scenario_manager.handle_event(window, event)

            if event == "Serialize":
                data = manager_manager.data()
                window["-SERDE-IO-"].update(json.dumps(data, indent=2))
            if event == "Deserialize":
                data = values["-SERDE-IO-"]
                try:
                    data = json.loads(data)
                except json.JSONDecodeError as e:
                    sg.popup_error("Unable to parse JSON application data.\nParser message: "+str(e), location=DEFAULT_LOCATION)
                    continue
                backup = manager_manager.data()
                try:
                    manager_manager.set_data(data)
                    manager_manager.update_all(window)
                except:
                    import traceback
                    sg.popup_error("Unable to load application data.", location=DEFAULT_LOCATION)
                    print(traceback.format_exc())
                    manager_manager.set_data(backup)
            
            if event == "-RESET-":
                answer = sg.popup_yes_no("Are you sure you want to enter a new domain? Any unsaved data will be lost.")
                if answer == "Yes":
                    manager_manager.set_data(ZERO_DATA)

            manager_manager.update_all(window)

    finally:
        window.close()
