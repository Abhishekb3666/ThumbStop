import json

import pytest

from thumbstop import personas, simulate


def test_builtin_packs_valid(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    assert {"fitness", "finance", "food", "tech"} <= set(personas.available())
    for n in personas.available() + ["unknown niche"]:
        people, _ = personas.load(n)
        assert abs(sum(p.weight for p in people) - 1) < 1e-9


def test_user_pack_overrides_and_validates(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    d = tmp_path / "packs"
    d.mkdir()
    (d / "pets.json").write_text(json.dumps({"curiosity": ["puppy"], "personas": [
        {"name": "Dog mom", "weight": 2, "hook_sens": .5, "patience": .5, "share": .5, "follow": .5, "bio": "Loves {niche}"}]}))
    people, extra = personas.load("pets")
    assert people[0].weight == 1 and people[0].bio == "Loves pets" and extra == ["puppy"]
    (d / "bad.json").write_text(json.dumps({"personas": [{"name": "x"}]}))
    with pytest.raises(ValueError):
        personas.load("bad")


def test_pack_curiosity_words_boost_hook(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    hook = "Your plateau is a protein problem."
    assert simulate(hook, "fitness", use_llm=False).hook_score > simulate(hook, "general", use_llm=False).hook_score


def test_cli_smoke(tmp_path, monkeypatch, capsys):
    from thumbstop.cli import main
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    f = tmp_path / "s.txt"
    f.write_text("Stop wasting 3 hours on this gym mistake. Follow for more.")
    main(["analyze", str(f), "--niche", "fitness", "--no-llm", "--save", "a"])
    main(["packs"])
    main(["plan", "--days", "1"])
    assert "REACH SCORE" in capsys.readouterr().out


def test_web_api(tmp_path, monkeypatch):
    monkeypatch.setenv("THUMBSTOP_HOME", str(tmp_path))
    from api.analyze import run
    code, out = run({"script": "Stop wasting 3 hours on this gym mistake. Follow for more.", "niche": "fitness"})
    assert code == 200 and out["score"] > 0 and out["breakdown"] and "fitness" in out["packs"]
    assert run({"script": "  "})[0] == 400
    assert run({"script": "x" * 5000})[0] == 400
