from typing import List
import unittest
from backend.base import scenario

from backend.base.exception import LogicException
from backend.base.scenario import Scenario
from backend.base.action import Action
from backend.base.agent import Agent
from backend.base.formula import Formula
from backend.base.query import Query, ActionQuery, AgentQuery, FormulaQuery
from backend.base.state import State
# from backend.master import parse_data

from backend.base.statement import EffectStatement, ReleaseStatement, Statement
from backend.base.timepoint import Obs, TimePoint

class ParsingTestCase(unittest.TestCase):
  
    def setUp(self) -> None:
        self.data_multiple = {
          "OBS": [
            {
              "original_expression": "john alive",
              "parsed_expression": [
                [
                  "john alive"
                ]
              ],
              "time": 0
            },
            {
              "original_expression": "julia alive",
              "parsed_expression": [
                [
                  "julia alive"
                ]
              ],
              "time": 0
            }
          ],
          "ACS": []
        }
        
        self.data_single = {
          "OBS": [
            {
              "original_expression": "john alive",
              "parsed_expression": [
                [
                  "john alive"
                ]
              ],
              "time": 0
            }
          ],
          "ACS": []
        }

    def test_multiple_obs_with_same_time_length(self):
        # given
        scenario = Scenario.from_timepoints(timepoints=TimePoint.from_ui(
                self.data_multiple), statements=[])
        # when
        result = scenario.timepoints
        # then
        self.assertEqual(len(result), 1)
  
    def test_multiple_obs_with_same_time_possibilities_lengths(self):
        # given
        scenario = Scenario.from_timepoints(timepoints=TimePoint.from_ui(
                self.data_multiple), statements=[])
        # when
        result = scenario.timepoints[0].obs.get_all_possibilities()[0].states
        # then
        self.assertEqual(len(result), 2)

    def test_single_obs_with_same_time_length(self):
        # given
        scenario = Scenario.from_timepoints(timepoints=TimePoint.from_ui(
                self.data_single), statements=[])
        # when
        result = scenario.timepoints
        # then
        self.assertEqual(len(result), 1)
  
    def test_single_obs_with_same_time_possibilities_lengths(self):
        # given
        scenario = Scenario.from_timepoints(timepoints=TimePoint.from_ui(
                self.data_single), statements=[])
        # when
        result = scenario.timepoints[0].obs.get_all_possibilities()[0].states
        # then
        self.assertEqual(len(result), 1)
