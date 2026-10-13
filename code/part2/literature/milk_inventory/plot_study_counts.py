"""Plot study-specific published counts; editable values come from source notes."""

from pathlib import Path
import csv, json, hashlib
import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parents[4]
OUT = ROOT / "output/part2/milk_inventory/study_counts"
CAT = ROOT / "output/part2/sources/Quellen.tsv"
PANELS = [
    (
        "10.1371/journal.pone.0154129",
        "A  Fraktionen frischer Kuhmilch",
        "Li 2016 · ≥10 CPM in ≥2/4 Kühen",
        "#00883a",
    ),
    (
        "10.1038/cr.2010.80",
        "B  Reife Kuhmilch und Kolostrum",
        "Chen 2010 · positive Einträge, je ein Pool aus 40 Kühen",
        "#568797",
    ),
    (
        "10.1016/j.crfs.2026.101453",
        "C  Kuhbasierte Formelnahrung",
        "Leroux 2026 · >1 Read über je drei Chargen",
        "#00883a",
    ),
    (
        "10.1016/j.idairyj.2025.106422",
        "D  Kuhbasierte Formelnahrung",
        "Ali 2026 · gemeinsame Tabelle aus vier Produkten",
        "#a66b28",
    ),
]


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    with CAT.open() as f:
        catalog = {r["DOI"]: r for r in csv.DictReader(f, delimiter="\t")}
    rows = []
    plt.rcParams.update(
        {
            "font.family": "DejaVu Sans",
            "font.size": 10,
            "svg.hashsalt": "cfsb-study-counts",
        }
    )
    fig, axes = plt.subplots(2, 2, figsize=(12, 8.4))
    fig.subplots_adjust(
        left=0.19, right=0.96, bottom=0.18, top=0.78, wspace=0.7, hspace=1.12
    )
    fig.text(
        0.06, 0.95, "Wie viele miRNAs wurden nachgewiesen?", fontsize=19, weight="bold"
    )
    fig.text(
        0.06,
        0.90,
        "Kuhmilch und kuhbasierte Säuglingsnahrung · getrennte Studienbefunde",
        fontsize=12,
        color="#56615b",
    )
    for ax, (doi, title, subtitle, color) in zip(axes.flat, PANELS):
        vals = json.loads(catalog[doi]["Diagrammwerte"])
        for v in vals:
            rows.append({"doi": doi, "source_note": catalog[doi]["Notiz"], **v})
        ax.set_title(title, loc="left", fontsize=12, weight="bold", pad=37)
        ax.text(
            0, 1.12, subtitle, transform=ax.transAxes, fontsize=8.5, color="#56615b"
        )
        bars = ax.barh(
            range(len(vals)), [v["Anzahl"] for v in vals], height=0.51, color=color
        )
        ax.set_yticks(range(len(vals)), [v["Material"] for v in vals], fontsize=9)
        ax.invert_yaxis()
        ax.set_xlim(0, 530)
        ax.set_xticks([0, 100, 200, 300, 400, 500])
        ax.set_axisbelow(True)
        ax.xaxis.grid(color="#e2e7e3")
        ax.spines[["top", "right", "left"]].set_visible(False)
        ax.tick_params(axis="y", length=0)
        ax.set_xlabel("Anzahl miRNA-Annotationen", fontsize=9, labelpad=8)
        for b, v in zip(bars, vals):
            ax.text(
                b.get_width() + 8,
                b.get_y() + b.get_height() / 2,
                str(v["Anzahl"]),
                va="center",
                fontsize=11,
                weight="bold",
            )
    fig.text(
        0.06,
        0.104,
        "Unterschiedliche Proben, Referenzen und Nachweisgrenzen. Die Balken zeigen keinen Verarbeitungseffekt.",
        fontsize=10,
        color="#37483d",
    )
    fig.text(
        0.06,
        0.066,
        "Ali: 57 Tabellenzeilen, davon 36 mit >1 Read. Der Text nennt abweichend 57 bei >1 Read.",
        fontsize=9,
        color="#7e511c",
    )
    fig.text(
        0.06,
        0.03,
        "Keine Addition über Gruppen; keine Aussage zur Menge, Aufnahme oder Wirkung der miRNAs.",
        fontsize=9,
        color="#56615b",
    )
    for ext in ["png", "svg"]:
        fig.savefig(
            OUT / ("study_counts." + ext),
            dpi=180,
            metadata={"Software": "CFSB"}
            if ext == "png"
            else {"Date": None, "Creator": "CFSB"},
        )
    plt.close(fig)
    with (OUT / "counts.tsv").open("w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t")
        w.writeheader()
        w.writerows(rows)
    manifest = {
        "source_catalogue_sha256": hashlib.sha256(CAT.read_bytes()).hexdigest(),
        "script_sha256": hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
        "n_studies": 4,
        "bars": len(rows),
        "meaning": "Study-specific annotation counts, not pooled richness or a processing effect.",
        "outputs": {
            p.name: hashlib.sha256(p.read_bytes()).hexdigest()
            for p in sorted(OUT.glob("*"))
            if p.name != "manifest.json"
        },
    }
    (OUT / "manifest.json").write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n"
    )
    print("Saved 4 panels and 9 bars with source locators.")


if __name__ == "__main__":
    main()
