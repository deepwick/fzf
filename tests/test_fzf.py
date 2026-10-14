import re
import shlex
import shutil
import subprocess
from pathlib import Path

import pytest

from deepwick_spec.ansi import runs
from deepwick_spec.check_port import check_port
from deepwick_spec.palette import load_palette
from deepwick_spec.tui import capture, tmux_available

REPO = Path(__file__).resolve().parents[1]
PALETTE = load_palette()
C = PALETTE.colors
EXPECTED = {
    "fg": "foreground", "bg": "background", "hl": "blue",
    "fg+": "foreground", "bg+": "selection", "hl+": "lightBlue",
    "info": "muted", "prompt": "blue", "pointer": "magenta", "marker": "green",
    "spinner": "teal", "header": "comment", "border": "overlay", "gutter": "background",
    "query": "foreground", "label": "blue",
}


def colors(path):
    value = re.search(r'FZF_DEFAULT_OPTS[= ]"\$FZF_DEFAULT_OPTS (.*?)"', path.read_text()).group(1)
    pairs = {}
    for opt in shlex.split(value):
        assert opt.startswith("--color="), opt
        for item in opt.removeprefix("--color=").split(","):
            key, color = item.split(":", 1)
            pairs[key] = color
    return pairs


def test_sh_colors_follow_roles():
    assert colors(REPO / "deepwick.sh") == {k: C[v] for k, v in EXPECTED.items()}


def test_fish_matches_sh():
    assert colors(REPO / "deepwick.fish") == colors(REPO / "deepwick.sh")


@pytest.mark.skipif(shutil.which("fzf") is None, reason="requires fzf")
def test_fzf_accepts_colors():
    opts = [f"--color={k}:{v}" for k, v in colors(REPO / "deepwick.sh").items()]
    result = subprocess.run(["fzf", "--filter", "zzz", *opts], input="", capture_output=True, text=True)
    assert result.returncode == 1, result.stderr


@pytest.mark.skipif(not (tmux_available() and shutil.which("fzf")), reason="requires tmux and fzf")
def test_fzf_renders_deepwick_colors():
    text = capture(
        f"bash --norc -c 'source {REPO / 'deepwick.sh'}; printf \"alpha\\nbeta\\ngamma\\n\" | fzf'",
        wait_for="3/3",
    )
    styles = runs(text)
    assert any(s["bg"] == C["selection"].lower() for _, s in styles)
    assert any("3/3" in chunk and s["fg"] == C["muted"].lower() for chunk, s in styles)


def test_port_conventions():
    assert check_port(REPO, PALETTE.allowed_hex()) == []
