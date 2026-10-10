"""
MineGuard AI - Model Registry & Lifecycle Management (Phase C4)
Tracks trained model artifacts, metrics, hyperparameters, and lineage.
"""

from pathlib import Path
from typing import Dict, Any, List, Optional
import json


class ModelRegistry:
    """
    Central repository tracking risk prediction model artifacts and performance benchmarks.
    """

    def __init__(self, registry_dir: str = "data/models"):
        self.registry_dir = Path(registry_dir)
        self.registry_dir.mkdir(parents=True, exist_ok=True)
        self._models: Dict[str, Any] = {}
        self._metadata: Dict[str, Dict[str, Any]] = {}
        self._load_persisted_metadata()

    def _load_persisted_metadata(self) -> None:
        """Reads all metadata JSON files currently stored in registry_dir."""
        for meta_file in self.registry_dir.glob("*_metadata.json"):
            name = meta_file.stem.replace("_metadata", "")
            try:
                with open(meta_file, "r", encoding="utf-8") as f:
                    self._metadata[name] = json.load(f)
            except Exception:
                pass

    def register(self, name: str, model: Any, metadata: Dict[str, Any]) -> None:
        """Registers a model artifact with corresponding metadata."""
        self._models[name] = model
        self._metadata[name] = metadata

        meta_path = self.registry_dir / f"{name}_metadata.json"
        with open(meta_path, "w", encoding="utf-8") as f:
            json.dump(metadata, f, indent=2)

    def get(self, name: str) -> Optional[Any]:
        """Retrieves in-memory model or attempts to load from disk."""
        if name in self._models:
            return self._models[name]

        model_path = self.registry_dir / f"{name}.joblib"
        if model_path.exists():
            import joblib
            try:
                model = joblib.load(str(model_path))
                self._models[name] = model
                return model
            except Exception:
                return None
        return None

    def get_metadata(self, name: str) -> Optional[Dict[str, Any]]:
        return self._metadata.get(name)

    def list_all(self) -> List[Dict[str, Any]]:
        """Lists all registered models with their metadata."""
        items = []
        for name, meta in self._metadata.items():
            entry = dict(meta)
            entry["model_name"] = name
            items.append(entry)
        return items

    def compare_models(self) -> List[Dict[str, Any]]:
        """Generates a side-by-side performance comparison table across all registered models."""
        comparison = []
        for name, meta in self._metadata.items():
            metrics = meta.get("metrics", {}).get("test", meta.get("metrics", {}))
            comparison.append({
                "model_name": name,
                "model_type": meta.get("model_type", "Unknown"),
                "accuracy": metrics.get("accuracy", 0.0),
                "precision": metrics.get("precision", 0.0),
                "recall": metrics.get("recall", 0.0),
                "f1": metrics.get("f1", 0.0),
                "roc_auc": metrics.get("roc_auc", 0.0),
                "trained_at": meta.get("trained_at", "")
            })
        return comparison

    def select_best(self, metric: str = "f1") -> Optional[str]:
        """Selects the best performing model identifier based on the requested evaluation metric."""
        if not self._metadata:
            return None

        best_name = None
        best_val = -1.0

        for name, meta in self._metadata.items():
            metrics = meta.get("metrics", {}).get("test", meta.get("metrics", {}))
            val = float(metrics.get(metric, 0.0))
            if val > best_val:
                best_val = val
                best_name = name

        return best_name


# Default global registry singleton
registry = ModelRegistry()
