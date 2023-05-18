import PySimpleGUI as sg
import json
from frontend.managers import *
from frontend.utils import get_default_location

sg.theme('dark grey 9')   

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
        [sg.Text("Press serialize to dump application state")],
        [sg.Button("Serialize"), sg.Button("Deserialize")],
        [sg.Multiline("", key="-SERDE-IO-", size=(100, 30))],
    ]

    layout = [[ sg.TabGroup([[
        sg.Tab("Agents", agent_manager.display),
        sg.Tab("Actions", action_manager.display),
        sg.Tab("Fluents", state_manager.display),
        sg.Tab("Time", time_manager.display),
        sg.Tab("ACS", acs_manager.display),
        sg.Tab("OBS", obs_manager.display),
        sg.Tab("Statements", statement_manager.display),
        sg.Tab("Query", query_manager.display),
        sg.Tab("Scenario", scenario_manager.display),
        sg.Tab("Save", serdelizer_layout),
    ]]
    #, size=(600, 480)
    ) ]]

    window = sg.Window('KRR', layout, location=DEFAULT_LOCATION)

    try:
        while True:
            event, values = window.read()
            if event == sg.WIN_CLOSED:
                break
            
            print(event, values)
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

    finally:
        window.close()
