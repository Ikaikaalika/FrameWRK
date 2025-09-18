from app.services.ops_service import OpsService


def test_dashboard_payload():
    service = OpsService.from_file()
    data = service.dashboard()
    assert data["meta"]["total_surgeries"] > 0
    assert len(data["locations"]) >= 1
    assert len(data["tasks"]) >= 1
