"""
Unit tests for the graph-based flow solver.
"""

import unittest
from datetime import datetime
from unittest.mock import Mock, patch

import pandas as pd

from opennem.core.flow_solver_graph import GraphFlowSolver, InterconnectorConfig


class TestGraphFlowSolver(unittest.TestCase):
    """Test the GraphFlowSolver class."""

    def setUp(self):
        """Set up test fixtures."""
        # Create test interconnector configuration
        self.interconnectors = [
            InterconnectorConfig(code="VIC1-NSW1", capacity_mw=1500),
            InterconnectorConfig(code="NSW1-QLD1", capacity_mw=1000),
            InterconnectorConfig(code="VIC1-SA1", capacity_mw=800),
            InterconnectorConfig(code="VIC1-TAS1", capacity_mw=500),
        ]

        # Mock Memgraph connection
        self.mock_memgraph = Mock()

        # Test interval
        self.test_interval = datetime(2025, 1, 1, 12, 0, 0)

    def create_test_flows_data(self) -> pd.DataFrame:
        """Create test interconnector flows data."""
        data = [
            # VIC exports to NSW
            {
                "interval": self.test_interval,
                "interconnector_code": "VIC1-NSW1",
                "network_region_from": "VIC1",
                "network_region_to": "NSW1",
                "flow_mw": 500,  # Positive = VIC to NSW
                "flow_mwh": 500 / 12,
            },
            # NSW exports to QLD
            {
                "interval": self.test_interval,
                "interconnector_code": "NSW1-QLD1",
                "network_region_from": "NSW1",
                "network_region_to": "QLD1",
                "flow_mw": 300,
                "flow_mwh": 300 / 12,
            },
            # VIC exports to SA
            {
                "interval": self.test_interval,
                "interconnector_code": "VIC1-SA1",
                "network_region_from": "VIC1",
                "network_region_to": "SA1",
                "flow_mw": 200,
                "flow_mwh": 200 / 12,
            },
            # TAS exports to VIC (reverse flow)
            {
                "interval": self.test_interval,
                "interconnector_code": "VIC1-TAS1",
                "network_region_from": "VIC1",
                "network_region_to": "TAS1",
                "flow_mw": -100,  # Negative = TAS to VIC
                "flow_mwh": -100 / 12,
            },
        ]
        return pd.DataFrame(data)

    def create_test_generation_data(self) -> pd.DataFrame:
        """Create test regional generation data."""
        data = [
            {
                "interval": self.test_interval,
                "network_region": "VIC1",
                "generation_mwh": 3000,
                "emissions_t": 2400,  # 0.8 tCO2/MWh
                "emission_intensity": 0.8,
            },
            {
                "interval": self.test_interval,
                "network_region": "NSW1",
                "generation_mwh": 4000,
                "emissions_t": 2800,  # 0.7 tCO2/MWh
                "emission_intensity": 0.7,
            },
            {
                "interval": self.test_interval,
                "network_region": "QLD1",
                "generation_mwh": 3500,
                "emissions_t": 2800,  # 0.8 tCO2/MWh
                "emission_intensity": 0.8,
            },
            {
                "interval": self.test_interval,
                "network_region": "SA1",
                "generation_mwh": 1000,
                "emissions_t": 300,  # 0.3 tCO2/MWh (more renewables)
                "emission_intensity": 0.3,
            },
            {
                "interval": self.test_interval,
                "network_region": "TAS1",
                "generation_mwh": 800,
                "emissions_t": 80,  # 0.1 tCO2/MWh (mostly hydro)
                "emission_intensity": 0.1,
            },
        ]
        return pd.DataFrame(data)

    @patch("opennem.core.flow_solver_graph.get_memgraph_connection")
    def test_solver_initialization(self, mock_get_connection):
        """Test solver initialization."""
        mock_get_connection.return_value = self.mock_memgraph

        solver = GraphFlowSolver(self.interconnectors)

        self.assertEqual(len(solver.interconnectors), 4)
        self.assertIn("VIC1-NSW1", solver.interconnectors)
        self.assertEqual(solver.interconnectors["VIC1-NSW1"].capacity_mw, 1500)

    @patch("opennem.core.flow_solver_graph.get_memgraph_connection")
    def test_flow_direction_handling(self, mock_get_connection):
        """Test that flow direction is correctly handled."""
        mock_get_connection.return_value = self.mock_memgraph
        self.mock_memgraph.execute_and_commit.return_value = None
        self.mock_memgraph.execute.return_value = []

        solver = GraphFlowSolver(self.interconnectors)

        flows = self.create_test_flows_data()
        generation = self.create_test_generation_data()

        # Verify solver and data are initialized
        self.assertIsNotNone(solver)
        self.assertIsNotNone(generation)

        # Test with positive flow (VIC to NSW)
        vic_nsw_flow = flows[flows["interconnector_code"] == "VIC1-NSW1"].iloc[0]
        self.assertTrue(vic_nsw_flow["flow_mw"] > 0)

        # Test with negative flow (TAS to VIC, reverse of VIC1-TAS1)
        vic_tas_flow = flows[flows["interconnector_code"] == "VIC1-TAS1"].iloc[0]
        self.assertTrue(vic_tas_flow["flow_mw"] < 0)

    @patch("opennem.core.flow_solver_graph.get_memgraph_connection")
    def test_emission_calculation(self, mock_get_connection):
        """Test that emissions are calculated from actual data."""
        mock_get_connection.return_value = self.mock_memgraph
        self.mock_memgraph.execute_and_commit.return_value = None

        solver = GraphFlowSolver(self.interconnectors)
        self.assertIsNotNone(solver)

        # Test that emissions use actual intensity from source region
        flows = self.create_test_flows_data()
        generation = self.create_test_generation_data()

        # VIC has 0.8 tCO2/MWh intensity
        vic_data = generation[generation["network_region"] == "VIC1"].iloc[0]
        self.assertEqual(vic_data["emission_intensity"], 0.8)

        # Flow from VIC to NSW should use VIC's emission intensity
        vic_nsw_flow = flows[flows["interconnector_code"] == "VIC1-NSW1"].iloc[0]
        expected_emissions = vic_nsw_flow["flow_mwh"] * 0.8
        self.assertAlmostEqual(expected_emissions, (500 / 12) * 0.8, places=2)

    @patch("opennem.core.flow_solver_graph.get_memgraph_connection")
    def test_circular_flow_detection(self, mock_get_connection):
        """Test detection of circular flows."""
        mock_get_connection.return_value = self.mock_memgraph

        # Mock circular flow query result
        mock_circular_flow = [
            (
                "VIC1",  # start_region
                ["VIC1", "NSW1", "QLD1", "SA1", "VIC1"],  # loop_path
                [  # flows
                    {"interconnector": "VIC1-NSW1", "mwh": 50, "emissions_t": 40},
                    {"interconnector": "NSW1-QLD1", "mwh": 45, "emissions_t": 31.5},
                    {"interconnector": "QLD1-SA1", "mwh": 40, "emissions_t": 32},
                    {"interconnector": "SA1-VIC1", "mwh": 35, "emissions_t": 10.5},
                ],
                35,  # bottleneck_mwh
                114,  # total_emissions_t
            )
        ]

        self.mock_memgraph.execute.return_value = mock_circular_flow

        solver = GraphFlowSolver(self.interconnectors)
        circular_flows = solver._detect_circular_flows(self.test_interval)

        self.assertEqual(len(circular_flows), 1)
        self.assertEqual(circular_flows[0]["start_region"], "VIC1")
        self.assertEqual(circular_flows[0]["loop_length"], 4)  # 4 hops in the loop
        self.assertEqual(circular_flows[0]["bottleneck_mwh"], 35)

    @patch("opennem.core.flow_solver_graph.get_memgraph_connection")
    def test_multi_hop_flow_tracing(self, mock_get_connection):
        """Test tracing of multi-hop flows."""
        mock_get_connection.return_value = self.mock_memgraph

        # Mock multi-hop flow query result
        mock_multi_hop = [
            (
                "VIC1",  # from_region
                "QLD1",  # to_region
                ["VIC1", "NSW1", "QLD1"],  # path
                [  # flow_details
                    {"interconnector": "VIC1-NSW1", "mwh": 100, "emissions_t": 80},
                    {"interconnector": "NSW1-QLD1", "mwh": 95, "emissions_t": 66.5},
                ],
                95,  # bottleneck_mwh
                146.5,  # total_emissions_t
                2,  # hop_count
            )
        ]

        self.mock_memgraph.execute.return_value = mock_multi_hop

        solver = GraphFlowSolver(self.interconnectors)
        multi_hop_flows = solver._trace_multi_hop_flows(self.test_interval)

        self.assertEqual(len(multi_hop_flows), 1)
        self.assertEqual(multi_hop_flows[0]["from_region"], "VIC1")
        self.assertEqual(multi_hop_flows[0]["to_region"], "QLD1")
        self.assertEqual(multi_hop_flows[0]["hop_count"], 2)
        self.assertEqual(multi_hop_flows[0]["bottleneck_mwh"], 95)

    @patch("opennem.core.flow_solver_graph.get_memgraph_connection")
    def test_regional_flow_calculation(self, mock_get_connection):
        """Test calculation of regional flows."""
        mock_get_connection.return_value = self.mock_memgraph

        # Mock region query
        mock_regions = [
            ("NSW1", 4000, 2800),  # region, generation, emissions
            ("VIC1", 3000, 2400),
            ("QLD1", 3500, 2800),
        ]

        # Mock import/export queries
        mock_imports = [(500 / 12, 40)]  # imports_mwh, import_emissions
        mock_exports = [(300 / 12, 21)]  # exports_mwh, export_emissions

        self.mock_memgraph.execute.side_effect = [
            mock_regions,  # First call for regions
            mock_imports,  # Import query for NSW1
            mock_exports,  # Export query for NSW1
            [(0, 0)],  # Import query for VIC1
            [(700 / 12, 56)],  # Export query for VIC1
            [(300 / 12, 21)],  # Import query for QLD1
            [(0, 0)],  # Export query for QLD1
        ]

        solver = GraphFlowSolver(self.interconnectors)
        regional_flows = solver._calculate_regional_flows(self.test_interval)

        self.assertEqual(len(regional_flows), 3)

        # Check NSW1 (net importer)
        nsw = regional_flows[regional_flows["network_region"] == "NSW1"].iloc[0]
        self.assertAlmostEqual(nsw["imports_mwh"], 500 / 12, places=2)
        self.assertAlmostEqual(nsw["exports_mwh"], 300 / 12, places=2)
        self.assertAlmostEqual(nsw["net_position_mwh"], 200 / 12, places=2)  # Net import

    @patch("opennem.core.flow_solver_graph.get_memgraph_connection")
    def test_flow_addition(self, mock_get_connection):
        """Test adding flows (e.g., NSW-SA interconnector)."""
        mock_get_connection.return_value = self.mock_memgraph
        self.mock_memgraph.execute_and_commit.return_value = None

        solver = GraphFlowSolver(self.interconnectors)

        # Add NSW-SA interconnector flow
        # Calculate emissions based on actual data
        flow_mwh = 300 / 12
        emissions_t = flow_mwh * 0.7  # Using NSW emission intensity

        success = solver.add_flow(
            self.test_interval,
            "NSW1",
            "SA1",
            "NSW1-SA1",
            300,  # 300 MW
            emissions_t,  # Actual emissions
        )
        self.assertTrue(success)

        # Check that execute_and_commit was called with correct parameters
        self.mock_memgraph.execute_and_commit.assert_called()
        call_args = self.mock_memgraph.execute_and_commit.call_args

        # Check the parameters
        params = call_args[0][1]
        self.assertEqual(params["from"], "NSW1")
        self.assertEqual(params["to"], "SA1")
        self.assertEqual(params["mw"], 300)
        self.assertAlmostEqual(params["mwh"], 300 / 12, places=2)
        self.assertAlmostEqual(params["emissions"], emissions_t, places=2)

    def test_interconnector_config(self):
        """Test InterconnectorConfig dataclass."""
        ic = InterconnectorConfig(code="TEST1", capacity_mw=1000)

        self.assertEqual(ic.code, "TEST1")
        self.assertEqual(ic.capacity_mw, 1000)

    @patch("opennem.core.flow_solver_graph.get_memgraph_connection")
    def test_solve_integration(self, mock_get_connection):
        """Test the complete solve process."""
        mock_get_connection.return_value = self.mock_memgraph
        self.mock_memgraph.execute_and_commit.return_value = None
        self.mock_memgraph.execute.return_value = []

        solver = GraphFlowSolver(self.interconnectors)

        flows = self.create_test_flows_data()
        generation = self.create_test_generation_data()

        # Mock the internal method returns
        with patch.object(solver, "_calculate_regional_flows") as mock_regional:
            with patch.object(solver, "_detect_circular_flows") as mock_circular:
                with patch.object(solver, "_trace_multi_hop_flows") as mock_multi:
                    mock_regional.return_value = pd.DataFrame([{"network_region": "NSW1", "imports_mwh": 100, "exports_mwh": 50}])
                    mock_circular.return_value = []
                    mock_multi.return_value = []

                    solution = solver.solve(self.test_interval, flows, generation)

                    self.assertEqual(solution.interval, self.test_interval)
                    self.assertEqual(len(solution.regional_flows), 1)
                    self.assertEqual(len(solution.circular_flows), 0)
                    self.assertEqual(len(solution.multi_hop_flows), 0)


if __name__ == "__main__":
    unittest.main()
