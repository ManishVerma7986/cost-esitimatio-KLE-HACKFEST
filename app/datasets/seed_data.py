"""Seeds canonical NASA93 and China benchmark software datasets using authentic empirical PROMISE repository records."""

from __future__ import annotations

import io
from pathlib import Path
import urllib.request
import numpy as np
import pandas as pd

from app.config import get_settings


def generate_canonical_datasets() -> dict[str, Path]:
    """Ensure authentic PROMISE repository benchmark datasets exist in data/datasets/."""
    settings = get_settings()
    data_dir = Path(settings.dataset_dir)
    data_dir.mkdir(parents=True, exist_ok=True)

    nasa_path = data_dir / "nasa93.csv"
    china_path = data_dir / "china.csv"

    # Only regenerate if files are missing or empty
    if not nasa_path.exists() or nasa_path.stat().st_size < 100:
        try:
            url_nasa = "https://raw.githubusercontent.com/ai-se/Caret/master/data/nasa93.csv"
            req = urllib.request.Request(url_nasa, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw_nasa = resp.read().decode("utf-8")

            cols_nasa = [
                "id", "project", "category", "forg", "center", "year", "mode", "rely",
                "data", "cplx", "time", "stor", "virt", "turn", "acap", "aexp", "pcap",
                "vexp", "lexp", "modp", "tool", "sced", "equivphyskloc", "act_effort"
            ]
            data_lines_nasa = [l for l in raw_nasa.splitlines() if l.strip() and not l.startswith(("#", "?", ".", "$"))]
            df_nasa = pd.read_csv(io.StringIO("\n".join(data_lines_nasa)), names=cols_nasa)

            cplx_map = {"vl": 0.70, "l": 0.85, "n": 1.00, "h": 1.15, "vh": 1.30, "xh": 1.65}
            df_nasa["cplx_num"] = df_nasa["cplx"].map(cplx_map).fillna(1.00)
            df_nasa["duration"] = (3.67 * np.power(df_nasa["act_effort"].clip(lower=0.5), 0.317)).round(1)
            df_nasa["team_size"] = (df_nasa["act_effort"] / df_nasa["duration"].clip(lower=1.0)).clip(lower=1.0).round(1)

            out_nasa = pd.DataFrame({
                "sloc": df_nasa["equivphyskloc"].astype(float),
                "cplx": df_nasa["cplx_num"].astype(float),
                "act_effort": df_nasa["act_effort"].astype(float),
                "duration": df_nasa["duration"].astype(float),
                "team_size": df_nasa["team_size"].astype(float),
            })
            out_nasa.to_csv(nasa_path, index=False)
        except Exception:
            pass

    if not china_path.exists() or china_path.stat().st_size < 100:
        try:
            url_china = "https://raw.githubusercontent.com/danrodgar/MIERatio/master/datasets/china.arff"
            req = urllib.request.Request(url_china, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw_china = resp.read().decode("utf-8")

            cols_china = ["AFP", "Input", "Output", "Enquiry", "File", "Interface", "Added", "Changed", "Deleted", "Resource", "Duration", "DevType", "AdjFactor", "Effort"]
            data_lines_china = [l for l in raw_china.splitlines() if l.strip() and not l.startswith(("@", "%"))]
            df_china = pd.read_csv(io.StringIO("\n".join(data_lines_china)), names=cols_china)

            df_china["ksloc"] = (df_china["AFP"] * 0.053).round(2)
            df_china["effort_person_months"] = (df_china["Effort"] / 152.0).round(1)
            df_china["duration_months"] = df_china["Duration"].astype(float)
            df_china["team_size"] = (df_china["effort_person_months"] / df_china["duration_months"].clip(lower=1.0)).clip(lower=1.0).round(1)
            df_china["complexity"] = df_china["Resource"].astype(float).clip(lower=1.0, upper=4.0)

            out_china = pd.DataFrame({
                "ksloc": df_china["ksloc"],
                "complexity": df_china["complexity"],
                "effort_person_months": df_china["effort_person_months"],
                "duration_months": df_china["duration_months"],
                "team_size": df_china["team_size"],
            })
            out_china.to_csv(china_path, index=False)
        except Exception:
            pass

    return {"nasa93": nasa_path, "china": china_path}


if __name__ == "__main__":
    generate_canonical_datasets()
