from pathlib import Path


def latest_parquet(dataset_dir: Path) -> Path:
    files = sorted(dataset_dir.glob("*.parquet"), key=lambda path: path.stat().st_mtime)
    if not files:
        raise FileNotFoundError(f"No parquet files found in {dataset_dir}")
    return files[-1]


def latest_parquets_by_leaf(root_dir: Path) -> dict[str, Path]:
    datasets: dict[str, Path] = {}
    for dataset_dir in sorted(path for path in root_dir.rglob("*") if path.is_dir()):
        if dataset_dir.name.startswith("_"):
            continue
        parquet_files = list(dataset_dir.glob("*.parquet"))
        if parquet_files:
            datasets[dataset_dir.name] = latest_parquet(dataset_dir)
    return datasets
