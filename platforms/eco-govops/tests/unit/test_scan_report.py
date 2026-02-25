"""Test scan report domain entity."""

from domain.entities.scan_report import Finding, ScanReport, ScanStatus
from domain.value_objects.severity import Severity


def test_scan_report_creation():
    r = ScanReport(scanner_type="module_scanner", cycle_id="cycle-001")
    assert r.status == ScanStatus.PENDING
    assert r.issues_found == 0
    assert r.findings == []


def test_scan_report_add_finding():
    r = ScanReport(scanner_type="hash_scanner")
    f = Finding(
        module_id="mod-1",
        rule_id="HASH-001",
        severity=Severity.CRITICAL,
        title="Hash mismatch",
        description="SHA-256 hash does not match expected value",
    )
    r.add_finding(f)
    assert r.issues_found == 1
    assert len(r.findings) == 1


def test_scan_report_lifecycle():
    r = ScanReport(scanner_type="semantic_scanner")
    r.mark_running()
    assert r.status == ScanStatus.RUNNING
    r.modules_scanned = 5
    r.mark_completed()
    assert r.status == ScanStatus.COMPLETED
    assert r.completed_at is not None


def test_scan_report_failed():
    r = ScanReport(scanner_type="test")
    r.mark_running()
    r.mark_failed("timeout")
    assert r.status == ScanStatus.FAILED


def test_scan_report_severity_counts():
    r = ScanReport(scanner_type="test")
    r.add_finding(Finding(severity=Severity.CRITICAL, title="crit1"))
    r.add_finding(Finding(severity=Severity.CRITICAL, title="crit2"))
    r.add_finding(Finding(severity=Severity.HIGH, title="high1"))
    r.add_finding(Finding(severity=Severity.LOW, title="low1"))
    counts = r.severity_counts()
    assert counts[Severity.CRITICAL] == 2
    assert counts[Severity.HIGH] == 1
    assert counts[Severity.LOW] == 1
    assert counts[Severity.INFO] == 0


def test_scan_report_severity_counts_excludes_fixed():
    r = ScanReport(scanner_type="test")
    f = Finding(severity=Severity.CRITICAL, title="fixed-crit")
    f.mark_fixed()
    r.add_finding(f)
    r.add_finding(Finding(severity=Severity.CRITICAL, title="open-crit"))
    counts = r.severity_counts()
    assert counts[Severity.CRITICAL] == 1


def test_scan_report_open_findings():
    r = ScanReport(scanner_type="test")
    f1 = Finding(severity=Severity.HIGH, title="open")
    f2 = Finding(severity=Severity.LOW, title="fixed")
    f2.mark_fixed()
    r.add_finding(f1)
    r.add_finding(f2)
    opens = r.open_findings()
    assert len(opens) == 1
    assert opens[0].title == "open"


def test_scan_report_auto_fixable():
    r = ScanReport(scanner_type="test")
    r.add_finding(Finding(severity=Severity.LOW, auto_fixable=True, title="auto"))
    r.add_finding(Finding(severity=Severity.LOW, auto_fixable=False, title="manual"))
    fixable = r.auto_fixable_findings()
    assert len(fixable) == 1
    assert fixable[0].title == "auto"


def test_scan_report_has_blocking_findings():
    r = ScanReport(scanner_type="test")
    r.add_finding(Finding(severity=Severity.LOW, title="non-blocking"))
    assert r.has_blocking_findings() is False
    r.add_finding(Finding(severity=Severity.CRITICAL, title="blocker"))
    assert r.has_blocking_findings() is True


def test_scan_report_merge():
    r1 = ScanReport(scanner_type="scanner-a", modules_scanned=3)
    r1.add_finding(Finding(severity=Severity.HIGH, title="from-a"))
    r2 = ScanReport(scanner_type="scanner-b", modules_scanned=2)
    r2.add_finding(Finding(severity=Severity.LOW, title="from-b"))
    r1.merge(r2)
    assert r1.issues_found == 2
    assert r1.modules_scanned == 5


def test_scan_report_summary():
    r = ScanReport(scanner_type="test", cycle_id="c1", modules_scanned=10)
    r.add_finding(Finding(severity=Severity.HIGH, title="issue"))
    r.mark_running()
    r.mark_completed()
    s = r.summary()
    assert s["scanner_type"] == "test"
    assert s["modules_scanned"] == 10
    assert s["issues_found"] == 1
    assert s["status"] == "completed"
    assert s["duration_seconds"] is not None


def test_finding_to_dict():
    f = Finding(
        module_id="m1",
        rule_id="R1",
        severity=Severity.MEDIUM,
        title="test",
        description="desc",
        location="/src/main.py:10",
        auto_fixable=True,
    )
    d = f.to_dict()
    assert d["severity"] == "medium"
    assert d["auto_fixable"] is True
    assert d["fixed"] is False


def test_scan_status_values():
    assert ScanStatus.PENDING.value == "pending"
    assert ScanStatus.RUNNING.value == "running"
    assert ScanStatus.COMPLETED.value == "completed"
    assert ScanStatus.FAILED.value == "failed"
    assert ScanStatus.CANCELLED.value == "cancelled"
