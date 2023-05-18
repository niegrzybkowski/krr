from backend.base import *
import traceback

def parse_data(data: dict):
    try:
        termination = data['TIME']['termination']
    except KeyError:
        raise ParsingException('Failed to parse time')

    agents = Agent.from_ui(data)
    actions = Action.from_ui(data)
    states = State.from_ui(data)
    scenario = Scenario.from_ui(data)
    statements = Statement.from_ui(data)

    queries = Query.from_ui(scenario=scenario, termination=termination, data=data)

    return {
        "termination": termination,
        "agents": agents,
        "actions": actions,
        "states": states,
        "scenario": scenario,
        "statements": statements,
        "queries": queries,
    }

def run_queries(data: dict):
    out = {}
    for i, query in enumerate(data['queries']):
        try:
            msg = query.run()
        except BackendExpection as e:
            msg = getattr(e, 'message', repr(e))
        except Exception as e:
            print(traceback.format_exc())
            msg = 'Something went wrong'
        finally:
            out[i+1] = msg
    return out
