import configparser

from tools.configure_lid import configure_lid


def test_lid_changes_preserve_battery_idle_settings_and_original_backup(tmp_path):
    path = tmp_path / "lxqt-powermanagement.conf"
    original = (
        "[General]\n"
        "lidClosedAction=1\n"
        "powerLowAction=3\n"
        "powerLowLevel=8\n"
        "enableBatteryWatcher=true\n"
        "idlenessACAction=2\n"
        "[Other]\n"
        "custom=100% unchanged\n"
    )
    path.write_text(original)
    configure_lid(path)
    first = path.read_text()
    configure_lid(path)
    assert path.read_text() == first
    assert path.with_name(path.name + ".before-klt-lid").read_text() == original
    settings = configparser.ConfigParser(interpolation=None)
    settings.read(path)
    general = settings["General"]
    assert general["enableLidWatcher"] == "true"
    for key in ("lidClosedAction", "lidClosedAcAction", "lidClosedExtMonAction", "lidClosedExtMonAcAction"):
        assert general[key] == "-1"
    assert general["powerLowAction"] == "3"
    assert general["powerLowLevel"] == "8"
    assert general["enableBatteryWatcher"] == "true"
    assert general["idlenessACAction"] == "2"
    assert settings["Other"]["custom"] == "100% unchanged"


def test_lid_config_can_create_missing_desktop_settings(tmp_path):
    path = tmp_path / "lxqt" / "lxqt-powermanagement.conf"
    configure_lid(path)
    assert "lidClosedAction=-1" in path.read_text()
    assert not path.with_name(path.name + ".before-klt-lid").exists()
