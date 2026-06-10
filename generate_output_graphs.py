from __future__ import annotations

import argparse
from html import escape
from pathlib import Path
from typing import Iterable

import pandas as pd  # type: ignore


SVG_WIDTH = 1200
SVG_HEIGHT = 720
MARGIN_LEFT = 180
MARGIN_RIGHT = 40
MARGIN_TOP = 80
MARGIN_BOTTOM = 100
PLOT_WIDTH = SVG_WIDTH - MARGIN_LEFT - MARGIN_RIGHT
PLOT_HEIGHT = SVG_HEIGHT - MARGIN_TOP - MARGIN_BOTTOM

BACKGROUND = "#f6f2ea"
PANEL = "#fffdf8"
TEXT = "#1f2937"
GRID = "#d9d2c5"
ACCENT = "#b85c38"
ACCENT_ALT = "#457b9d"
ACCENT_SOFT = "#d8a47f"


def load_dataset(dataset_dir: Path) -> pd.DataFrame:
    parquet_files = sorted(dataset_dir.glob("*.parquet"))
    if not parquet_files:
        raise FileNotFoundError(f"Aucun parquet trouve dans {dataset_dir}")
    return pd.read_parquet(dataset_dir)


def nice_number(value: float) -> str:
    if abs(value) >= 1_000_000:
        return f"{value / 1_000_000:.1f}M"
    if abs(value) >= 1_000:
        return f"{value / 1_000:.1f}K"
    if float(value).is_integer():
        return str(int(value))
    return f"{value:.2f}"


def svg_header(title: str, subtitle: str) -> list[str]:
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" viewBox="0 0 {SVG_WIDTH} {SVG_HEIGHT}">',
        f'<rect x="0" y="0" width="{SVG_WIDTH}" height="{SVG_HEIGHT}" fill="{BACKGROUND}"/>',
        f'<rect x="24" y="24" width="{SVG_WIDTH - 48}" height="{SVG_HEIGHT - 48}" rx="24" fill="{PANEL}" stroke="#eadfce"/>',
        f'<text x="60" y="78" font-family="Segoe UI, Arial, sans-serif" font-size="30" font-weight="700" fill="{TEXT}">{escape(title)}</text>',
        f'<text x="60" y="108" font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="#6b7280">{escape(subtitle)}</text>',
    ]


def svg_footer() -> list[str]:
    return ["</svg>"]


def write_svg(target: Path, lines: Iterable[str]) -> None:
    target.parent.mkdir(parents=True, exist_ok=True)
    target.write_text("\n".join(lines), encoding="utf-8")


def render_bar_chart(
    df: pd.DataFrame,
    label_col: str,
    value_col: str,
    title: str,
    subtitle: str,
    target: Path,
    top_n: int = 15,
    horizontal: bool = True,
    color: str = ACCENT,
) -> None:
    chart_df = df[[label_col, value_col]].dropna().copy().sort_values(value_col, ascending=False).head(top_n)
    if chart_df.empty:
        return

    lines = svg_header(title, subtitle)
    max_value = float(chart_df[value_col].max()) or 1.0

    if horizontal:
        row_height = PLOT_HEIGHT / len(chart_df)
        for idx, row in enumerate(chart_df.itertuples(index=False), start=0):
            label = str(getattr(row, label_col))
            value = float(getattr(row, value_col))
            y = MARGIN_TOP + idx * row_height + 8
            bar_height = row_height - 16
            bar_width = (value / max_value) * (PLOT_WIDTH - 40)

            lines.append(
                f'<text x="{MARGIN_LEFT - 16}" y="{y + bar_height / 2 + 5}" text-anchor="end" '
                f'font-family="Segoe UI, Arial, sans-serif" font-size="16" fill="{TEXT}">{escape(label)}</text>'
            )
            lines.append(
                f'<rect x="{MARGIN_LEFT}" y="{y}" width="{bar_width:.2f}" height="{bar_height:.2f}" '
                f'rx="8" fill="{color}"/>'
            )
            lines.append(
                f'<text x="{MARGIN_LEFT + bar_width + 10:.2f}" y="{y + bar_height / 2 + 5:.2f}" '
                f'font-family="Segoe UI, Arial, sans-serif" font-size="15" fill="{TEXT}">{escape(nice_number(value))}</text>'
            )
    else:
        bar_count = len(chart_df)
        bar_slot = PLOT_WIDTH / bar_count
        for idx, row in enumerate(chart_df.itertuples(index=False), start=0):
            label = str(getattr(row, label_col))
            value = float(getattr(row, value_col))
            x = MARGIN_LEFT + idx * bar_slot + 12
            bar_width = max(bar_slot - 24, 12)
            bar_height = (value / max_value) * (PLOT_HEIGHT - 40)
            y = MARGIN_TOP + PLOT_HEIGHT - bar_height

            lines.append(
                f'<rect x="{x:.2f}" y="{y:.2f}" width="{bar_width:.2f}" height="{bar_height:.2f}" rx="8" fill="{color}"/>'
            )
            lines.append(
                f'<text x="{x + bar_width / 2:.2f}" y="{MARGIN_TOP + PLOT_HEIGHT + 24}" text-anchor="middle" '
                f'font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="{TEXT}" transform="rotate(25 {x + bar_width / 2:.2f} {MARGIN_TOP + PLOT_HEIGHT + 24})">{escape(label)}</text>'
            )
            lines.append(
                f'<text x="{x + bar_width / 2:.2f}" y="{y - 10:.2f}" text-anchor="middle" '
                f'font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="{TEXT}">{escape(nice_number(value))}</text>'
            )

    lines.extend(svg_footer())
    write_svg(target, lines)


def render_line_chart(
    df: pd.DataFrame,
    x_col: str,
    y_col: str,
    title: str,
    subtitle: str,
    target: Path,
) -> None:
    chart_df = df[[x_col, y_col]].dropna().copy().sort_values(x_col)
    if chart_df.empty:
        return

    x_values = chart_df[x_col].astype(str).tolist()
    y_values = chart_df[y_col].astype(float).tolist()
    max_value = max(y_values) or 1.0

    lines = svg_header(title, subtitle)

    for step in range(6):
        y = MARGIN_TOP + (PLOT_HEIGHT / 5) * step
        value = max_value - (max_value / 5) * step
        lines.append(f'<line x1="{MARGIN_LEFT}" y1="{y:.2f}" x2="{MARGIN_LEFT + PLOT_WIDTH}" y2="{y:.2f}" stroke="{GRID}" stroke-width="1"/>')
        lines.append(
            f'<text x="{MARGIN_LEFT - 14}" y="{y + 5:.2f}" text-anchor="end" font-family="Segoe UI, Arial, sans-serif" font-size="13" fill="#6b7280">{escape(nice_number(value))}</text>'
        )

    points: list[str] = []
    point_gap = PLOT_WIDTH / max(len(x_values) - 1, 1)
    for idx, (x_value, y_value) in enumerate(zip(x_values, y_values, strict=True)):
        x = MARGIN_LEFT + idx * point_gap
        y = MARGIN_TOP + PLOT_HEIGHT - ((y_value / max_value) * PLOT_HEIGHT)
        points.append(f"{x:.2f},{y:.2f}")
        lines.append(f'<circle cx="{x:.2f}" cy="{y:.2f}" r="5" fill="{ACCENT}"/>')
        lines.append(
            f'<text x="{x:.2f}" y="{MARGIN_TOP + PLOT_HEIGHT + 30}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="{TEXT}">{escape(x_value)}</text>'
        )
        lines.append(
            f'<text x="{x:.2f}" y="{y - 12:.2f}" text-anchor="middle" font-family="Segoe UI, Arial, sans-serif" font-size="12" fill="{TEXT}">{escape(nice_number(y_value))}</text>'
        )

    lines.append(
        f'<polyline fill="none" stroke="{ACCENT_ALT}" stroke-width="4" points="{" ".join(points)}"/>'
    )
    lines.extend(svg_footer())
    write_svg(target, lines)


def render_metric_cards(output_dir: Path, target: Path) -> None:
    metric_map = {
        "enriched": "Lignes enrichies",
        "country_sales": "Pays",
        "monthly_sales": "Mois",
        "supplier_sales": "Fournisseurs",
        "supplier_sales_uk_2011": "Fournisseurs UK 2011",
        "continent_sales": "Continents",
        "cancellations_by_continent": "Continents annules",
    }
    values: list[tuple[str, int]] = []
    for dataset_name, label in metric_map.items():
        dataset_path = output_dir / dataset_name
        if dataset_path.exists():
            df = pd.read_parquet(dataset_path)
            values.append((label, len(df)))

    lines = svg_header("ETL Output Snapshot", "Vue rapide des volumes produits par le dernier run")
    card_width = 300
    card_height = 130
    gap_x = 28
    gap_y = 28
    start_x = 70
    start_y = 160

    for idx, (label, value) in enumerate(values):
        row = idx // 3
        col = idx % 3
        x = start_x + col * (card_width + gap_x)
        y = start_y + row * (card_height + gap_y)
        lines.append(f'<rect x="{x}" y="{y}" width="{card_width}" height="{card_height}" rx="18" fill="{PANEL}" stroke="#e5dac9"/>')
        lines.append(f'<text x="{x + 24}" y="{y + 46}" font-family="Segoe UI, Arial, sans-serif" font-size="18" fill="#6b7280">{escape(label)}</text>')
        lines.append(f'<text x="{x + 24}" y="{y + 96}" font-family="Segoe UI, Arial, sans-serif" font-size="34" font-weight="700" fill="{TEXT}">{value}</text>')

    lines.extend(svg_footer())
    write_svg(target, lines)


def generate_graphs(output_dir: Path, target_dir: Path) -> None:
    target_dir.mkdir(parents=True, exist_ok=True)

    render_metric_cards(output_dir, target_dir / "00_output_snapshot.svg")

    if (output_dir / "country_sales").exists():
        country_df = load_dataset(output_dir / "country_sales")
        render_bar_chart(
            country_df,
            label_col="Country",
            value_col="TotalAmount",
            title="Country Sales",
            subtitle="Top pays par montant total de ventes",
            target=target_dir / "01_country_sales.svg",
            horizontal=True,
        )

    if (output_dir / "monthly_sales").exists():
        monthly_df = load_dataset(output_dir / "monthly_sales")
        render_line_chart(
            monthly_df,
            x_col="InvoiceMonth",
            y_col="TotalSales",
            title="Monthly Sales Trend",
            subtitle="Evolution mensuelle du chiffre d'affaires",
            target=target_dir / "02_monthly_sales.svg",
        )

    if (output_dir / "supplier_sales").exists():
        supplier_df = load_dataset(output_dir / "supplier_sales")
        render_bar_chart(
            supplier_df,
            label_col="SupplierID",
            value_col="TotalAmount",
            title="Supplier Sales",
            subtitle="Top fournisseurs par montant total",
            target=target_dir / "03_supplier_sales.svg",
            horizontal=True,
            color=ACCENT_ALT,
        )

    if (output_dir / "supplier_sales_uk_2011").exists():
        supplier_uk_df = load_dataset(output_dir / "supplier_sales_uk_2011")
        render_bar_chart(
            supplier_uk_df,
            label_col="SupplierID",
            value_col="TotalAmount",
            title="Supplier Sales UK 2011",
            subtitle="Top fournisseurs sur le Royaume-Uni en 2011",
            target=target_dir / "04_supplier_sales_uk_2011.svg",
            horizontal=True,
            color=ACCENT_SOFT,
        )

    if (output_dir / "continent_sales").exists():
        continent_df = load_dataset(output_dir / "continent_sales")
        render_bar_chart(
            continent_df,
            label_col="Continent",
            value_col="TotalAmount",
            title="Continent Sales",
            subtitle="Ventes agregees par continent",
            target=target_dir / "05_continent_sales.svg",
            horizontal=False,
        )

    if (output_dir / "cancellations_by_continent").exists():
        cancellations_df = load_dataset(output_dir / "cancellations_by_continent")
        render_bar_chart(
            cancellations_df,
            label_col="Continent",
            value_col="CancelledOperations",
            title="Cancellations by Continent",
            subtitle="Nombre d'operations annulees par continent",
            target=target_dir / "06_cancellations_by_continent.svg",
            horizontal=False,
            color="#8c3f4d",
        )


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Genere des graphes SVG a partir des sorties Parquet du projet."
    )
    parser.add_argument("--output-dir", default="output", help="Dossier contenant les sorties organisees.")
    parser.add_argument("--target-dir", default="output_graphs", help="Dossier ou ecrire les graphes SVG.")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    if not output_dir.exists():
        raise FileNotFoundError(f"Dossier introuvable: {output_dir}")

    generate_graphs(output_dir, Path(args.target_dir))
    print(f"Graphs generated in: {Path(args.target_dir)}")


if __name__ == "__main__":
    main()