"""
Mock ISTAT SDMX API server for CI/CD testing.

Provides a lightweight mock server that simulates ISTAT API responses
for integration testing in CI/CD environments where external API access
may be limited or unreliable.
"""
import json
import threading
import time
import xml.etree.ElementTree as ET
from datetime import datetime
from typing import Any, Dict

from flask import Flask, Response, jsonify, request


class MockIstatServer:
    """Mock ISTAT SDMX API server for testing."""

    def __init__(self, host: str = "localhost", port: int = 8080):
        """Initialize mock server."""
        self.host = host
        self.port = port
        self.app = Flask(__name__)
        self.server_thread = None
        self.running = False

        # Mock data
        self.mock_dataflows = self._create_mock_dataflows()
        self.mock_datasets = self._create_mock_datasets()

        self._setup_routes()

    def _create_mock_dataflows(self) -> str:
        """Create mock dataflows XML response."""
        return """<?xml version="1.0" encoding="UTF-8"?>
<message:StructureSpecificData
    xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
    xmlns:str="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure"
    xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
    <message:Header>
        <message:ID>MOCK_DATAFLOWS</message:ID>
        <message:Test>true</message:Test>
        <message:Prepared>{timestamp}</message:Prepared>
        <message:Sender id="IT1"/>
    </message:Header>
    <message:Structures>
        <str:Dataflows>
            <str:Dataflow id="DCIS_POPRES1" agencyID="IT1" version="1.0">
                <common:Name xml:lang="it">Popolazione residente</common:Name>
                <common:Name xml:lang="en">Resident population</common:Name>
            </str:Dataflow>
            <str:Dataflow id="DCIS_POPSTRRES1" agencyID="IT1" version="1.0">
                <common:Name xml:lang="it">Popolazione per struttura</common:Name>
                <common:Name xml:lang="en">Population by structure</common:Name>
            </str:Dataflow>
            <str:Dataflow id="TEST_DATASET" agencyID="IT1" version="1.0">
                <common:Name xml:lang="it">Dataset di test</common:Name>
                <common:Name xml:lang="en">Test dataset</common:Name>
            </str:Dataflow>
        </str:Dataflows>
    </message:Structures>
</message:StructureSpecificData>""".format(
            timestamp=datetime.now().isoformat()
        )

    def _create_mock_datasets(self) -> Dict[str, str]:
        """Create mock dataset responses."""
        return {
            "DCIS_POPRES1": """<?xml version="1.0" encoding="UTF-8"?>
<message:GenericData
    xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message"
    xmlns:generic="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/data/generic"
    xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
    <message:Header>
        <message:ID>DCIS_POPRES1_DATA</message:ID>
        <message:Test>true</message:Test>
        <message:Prepared>{timestamp}</message:Prepared>
    </message:Header>
    <message:DataSet>
        <generic:Series>
            <generic:SeriesKey>
                <generic:Value id="ITTER107" value="IT"/>
                <generic:Value id="SEXISTAT1" value="1"/>
            </generic:SeriesKey>
            <generic:Obs>
                <generic:ObsDimension value="2020"/>
                <generic:ObsValue value="59641488"/>
            </generic:Obs>
            <generic:Obs>
                <generic:ObsDimension value="2021"/>
                <generic:ObsValue value="59236213"/>
            </generic:Obs>
        </generic:Series>
        <generic:Series>
            <generic:SeriesKey>
                <generic:Value id="ITTER107" value="IT"/>
                <generic:Value id="SEXISTAT1" value="2"/>
            </generic:SeriesKey>
            <generic:Obs>
                <generic:ObsDimension value="2020"/>
                <generic:ObsValue value="30494366"/>
            </generic:Obs>
            <generic:Obs>
                <generic:ObsDimension value="2021"/>
                <generic:ObsValue value="30277472"/>
            </generic:Obs>
        </generic:Series>
    </message:DataSet>
</message:GenericData>""".format(
                timestamp=datetime.now().isoformat()
            ),
            "TEST_DATASET": """<?xml version="1.0" encoding="UTF-8"?>
<GenericData>
    <DataSet>
        <Obs><ObsValue value="100"/></Obs>
        <Obs><ObsValue value="200"/></Obs>
        <Obs><ObsValue value="300"/></Obs>
    </DataSet>
</GenericData>""",
            "EMPTY_DATASET": """<?xml version="1.0" encoding="UTF-8"?>
<GenericData>
    <DataSet>
        <!-- No observations -->
    </DataSet>
</GenericData>""",
        }

    def _setup_routes(self):
        """Setup Flask routes for mock API."""

        @self.app.route("/SDMXWS/rest/dataflow/IT1")
        def get_dataflows():
            """Mock dataflows endpoint."""
            return Response(
                self.mock_dataflows,
                mimetype="application/xml",
                headers={
                    "Content-Type": "application/xml; charset=utf-8",
                    "X-Mock-Server": "true",
                },
            )

        @self.app.route("/SDMXWS/rest/datastructure/IT1/<dataset_id>")
        def get_datastructure(dataset_id):
            """Mock datastructure endpoint."""
            structure_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<message:Structure xmlns:message="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/message">
    <message:Header>
        <message:ID>{dataset_id}_STRUCTURE</message:ID>
        <message:Test>true</message:Test>
    </message:Header>
    <message:Structures>
        <str:DataStructure id="{dataset_id}" xmlns:str="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/structure">
            <common:Name xmlns:common="http://www.sdmx.org/resources/sdmxml/schemas/v2_1/common">
                Structure for {dataset_id}
            </common:Name>
        </str:DataStructure>
    </message:Structures>
</message:Structure>"""

            return Response(
                structure_xml,
                mimetype="application/xml",
                headers={"X-Mock-Server": "true"},
            )

        @self.app.route("/SDMXWS/rest/data/<dataset_id>")
        def get_dataset_data(dataset_id):
            """Mock dataset data endpoint."""
            # Simulate network delay
            delay = request.args.get("delay", 0, type=float)
            if delay > 0:
                time.sleep(min(delay, 5.0))  # Max 5 second delay

            # Simulate errors for specific datasets
            if dataset_id == "ERROR_DATASET":
                return Response("Internal Server Error", status=500)

            if dataset_id == "NOT_FOUND_DATASET":
                return Response("Dataset not found", status=404)

            # Return mock data
            dataset_xml = self.mock_datasets.get(
                dataset_id, self.mock_datasets["TEST_DATASET"]
            )

            return Response(
                dataset_xml,
                mimetype="application/xml",
                headers={
                    "Content-Type": "application/xml; charset=utf-8",
                    "X-Mock-Server": "true",
                    "X-Dataset-ID": dataset_id,
                },
            )

        @self.app.route("/health")
        def health_check():
            """Health check endpoint."""
            return jsonify(
                {
                    "status": "healthy",
                    "mock_server": True,
                    "timestamp": datetime.now().isoformat(),
                    "available_datasets": list(self.mock_datasets.keys()),
                }
            )

        @self.app.route("/mock/control/latency/<int:ms>")
        def set_latency(ms):
            """Control endpoint to simulate latency."""
            # This could be expanded to set global latency
            return jsonify(
                {
                    "message": f"Latency simulation set to {ms}ms",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        @self.app.route("/mock/control/error/<dataset_id>")
        def simulate_error(dataset_id):
            """Control endpoint to simulate errors for specific datasets."""
            # This could be expanded to maintain error states
            return jsonify(
                {
                    "message": f"Error simulation enabled for {dataset_id}",
                    "timestamp": datetime.now().isoformat(),
                }
            )

    def start(self):
        """Start the mock server in a separate thread."""
        if not self.running:
            self.running = True
            self.server_thread = threading.Thread(
                target=lambda: self.app.run(
                    host=self.host, port=self.port, debug=False, use_reloader=False
                )
            )
            self.server_thread.daemon = True
            self.server_thread.start()

            # Wait for server to start
            time.sleep(1)
            print(f"🚀 Mock ISTAT server started at http://{self.host}:{self.port}")

    def stop(self):
        """Stop the mock server."""
        if self.running:
            self.running = False
            # Flask doesn't have a clean shutdown method in development mode
            # In production, you'd use a proper WSGI server
            print("🛑 Mock ISTAT server stopped")

    def get_base_url(self) -> str:
        """Get the base URL for the mock server."""
        return f"http://{self.host}:{self.port}"


# Convenience functions for testing
def start_mock_server(port: int = 8080) -> MockIstatServer:
    """Start a mock ISTAT server for testing."""
    server = MockIstatServer(port=port)
    server.start()
    return server


def stop_mock_server(server: MockIstatServer):
    """Stop a mock ISTAT server."""
    server.stop()


# Context manager for testing
class MockIstatServerContext:
    """Context manager for mock ISTAT server."""

    def __init__(self, port: int = 8080):
        self.port = port
        self.server = None

    def __enter__(self) -> MockIstatServer:
        """Start server on context entry."""
        self.server = start_mock_server(self.port)
        return self.server

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Stop server on context exit."""
        if self.server:
            stop_mock_server(self.server)


# Usage example
if __name__ == "__main__":
    # Start mock server for manual testing
    server = start_mock_server(8080)

    try:
        print("Mock server is running. Press Ctrl+C to stop.")
        print("Available endpoints:")
        print("  - GET /SDMXWS/rest/dataflow/IT1")
        print("  - GET /SDMXWS/rest/datastructure/IT1/<dataset_id>")
        print("  - GET /SDMXWS/rest/data/<dataset_id>")
        print("  - GET /health")

        # Keep server running
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        stop_mock_server(server)
        print("\n✅ Mock server stopped")
