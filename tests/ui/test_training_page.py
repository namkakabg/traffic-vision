from pathlib import Path

import onnx
from onnx import TensorProto, helper
from streamlit.testing.v1 import AppTest

from trafficvision.config import AppPaths
from trafficvision.data.catalog import VIETNAM_TRAFFIC_SIGN_CATALOG
from trafficvision.domain import ModelManifest
from trafficvision.registry import ModelRegistry, sha256_file
from trafficvision.training.candidate import package_candidate
from trafficvision.training.evaluator import EvaluationMetrics
from trafficvision.training.exporter import ExportResult


def setup_test_environment(tmp_path: Path):
    paths = AppPaths.from_root(tmp_path)
    paths.ensure_directories()
    dummy_onnx = tmp_path / "model.onnx"
    dummy_onnx.write_bytes(b"dummy-onnx-weights")
    digest = sha256_file(dummy_onnx)

    manifest = ModelManifest(
        schema_version="1.0",
        model_id="yolo11n-baseline-test",
        stage="production",
        source_model_id="yolo11n-baseline-orig",
        artifact_filename="model.onnx",
        backend="onnx",
        task="detect",
        class_names={0: "bien_cam", 1: "bien_hieu_lenh", 2: "bien_chi_dan"},
        imgsz=640,
        sha256=digest,
        source="ultralytics-test",
        created_at="2026-09-27T21:00:00Z",
    )
    registry = ModelRegistry(paths)
    registry.install_baseline(dummy_onnx, manifest)
    return paths, manifest


def create_valid_onnx(path: Path) -> None:
    node = helper.make_node("Identity", ["X"], ["Y"])
    graph = helper.make_graph(
        [node],
        "test",
        [helper.make_tensor_value_info("X", TensorProto.FLOAT, [1, 3, 640, 640])],
        [helper.make_tensor_value_info("Y", TensorProto.FLOAT, [1, 3, 640, 640])],
    )
    model = helper.make_model(
        graph,
        producer_name="test",
        ir_version=9,
        opset_imports=[helper.make_operatorsetid("", 17)],
    )
    path.parent.mkdir(parents=True, exist_ok=True)
    onnx.save(model, str(path))


def create_test_candidate(runs_dir: Path, run_id: str = "run_test_001") -> Path:
    run_dir = runs_dir / run_id
    run_dir.mkdir(parents=True, exist_ok=True)
    weights_path = run_dir / "weights" / "best.pt"
    weights_path.parent.mkdir(parents=True, exist_ok=True)
    weights_path.write_bytes(b"dummy-weights")

    onnx_path = run_dir / "weights" / "best.onnx"
    create_valid_onnx(onnx_path)

    onnx_res = ExportResult(
        onnx_path=onnx_path,
        is_parity_valid=True,
        max_abs_diff=0.0001,
        cpu_latency_ms=12.5,
        cpu_fps=80.0,
    )
    eval_m = EvaluationMetrics(
        precision=0.88,
        recall=0.84,
        f1=0.86,
        map50=0.89,
        map50_95=0.65,
    )
    class_names = {sc.id: sc.name_vi for sc in VIETNAM_TRAFFIC_SIGN_CATALOG}
    cand_dir = package_candidate(
        run_id=run_id,
        weights_path=weights_path,
        onnx_result=onnx_res,
        eval_metrics=eval_m,
        class_names=class_names,
        runs_dir=runs_dir,
    )
    return cand_dir


def test_training_page_renders_4_steps(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    setup_test_environment(tmp_path)
    app_path = str(Path(__file__).parents[2] / "app.py")

    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Huấn luyện AI").run()
    assert not at.exception

    all_text = " ".join(
        [m.value for m in at.markdown]
        + [t.value for t in at.title]
        + [tab.label for tab in at.tabs]
    )
    assert "Dữ liệu" in all_text
    assert "Kiểm định" in all_text
    assert "Huấn luyện" in all_text
    assert "Đánh giá" in all_text
    assert "CPU" in all_text or "CUDA" in all_text


def test_step1_dataset_input_scan_and_generate(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    paths, _ = setup_test_environment(tmp_path)
    app_path = str(Path(__file__).parents[2] / "app.py")

    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Huấn luyện AI").run()
    assert not at.exception

    # Check text input for dataset directory exists
    assert len(at.text_input) >= 1
    # Check scan or generate buttons exist
    buttons = {b.label: b for b in at.button}
    assert any("quét" in lbl.lower() for lbl in buttons)
    assert any("mẫu" in lbl.lower() or "synthetic" in lbl.lower() for lbl in buttons)

    # Click generate demo synthetic dataset
    gen_btn = next(b for lbl, b in buttons.items() if "mẫu" in lbl.lower() or "synthetic" in lbl.lower())
    gen_btn.click().run()
    assert not at.exception

    all_text = " ".join([m.value for m in at.markdown] + [i.value for i in at.info] + [s.value for s in at.success])
    # Should display dataset info, sample count, or scan result
    assert "ảnh" in all_text.lower() or "sample" in all_text.lower() or "tổng" in all_text.lower()
    # Check HF download guidance
    assert "huggingface" in all_text.lower() or "download" in all_text.lower() or "tải" in all_text.lower()


def test_step2_validation_blocking_error_disables_training(tmp_path: Path, monkeypatch):
    from tests.fixtures.dataset_fixture import create_synthetic_dataset

    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    paths, _ = setup_test_environment(tmp_path)

    # Create invalid dataset with corrupt image
    invalid_dir = create_synthetic_dataset(tmp_path / "invalid_data", num_samples=5, invalid_case="corrupt_image")

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Huấn luyện AI").run()

    # Set data dir to invalid
    dir_input = at.text_input[0]
    dir_input.input(str(invalid_dir)).run()

    # Click scan / validate
    validate_btns = [b for b in at.button if "kiểm định" in b.label.lower() or "quét" in b.label.lower()]
    if validate_btns:
        validate_btns[0].click().run()

    assert not at.exception
    # Should show blocking error message or red alert
    all_text = " ".join([m.value for m in at.markdown] + [e.value for e in at.error])
    assert "corrupt" in all_text.lower() or "blocking" in all_text.lower() or "lỗi" in all_text.lower()

    # Train button should be disabled
    start_train_btns = [b for b in at.button if "bắt đầu" in b.label.lower()]
    assert len(start_train_btns) >= 1
    assert start_train_btns[0].disabled is True


def test_step2_validation_success_shows_eda_and_snapshot(tmp_path: Path, monkeypatch):
    from tests.fixtures.dataset_fixture import create_synthetic_dataset

    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    paths, _ = setup_test_environment(tmp_path)

    clean_dir = create_synthetic_dataset(tmp_path / "clean_data", num_samples=10)

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Huấn luyện AI").run()

    dir_input = at.text_input[0]
    dir_input.input(str(clean_dir)).run()

    # Click validate
    validate_btns = [b for b in at.button if "kiểm định" in b.label.lower() or "quét" in b.label.lower()]
    if validate_btns:
        validate_btns[0].click().run()

    assert not at.exception
    all_text = " ".join([m.value for m in at.markdown] + [s.value for s in at.success] + [i.value for i in at.info])
    assert "hợp lệ" in all_text.lower() or "eda" in all_text.lower() or "phân bố" in all_text.lower() or "train" in all_text.lower()

    # Click snapshot button
    snapshot_btns = [b for b in at.button if "snapshot" in b.label.lower()]
    assert len(snapshot_btns) >= 1
    snapshot_btns[0].click().run()
    assert not at.exception
    all_text_after = " ".join([m.value for m in at.markdown] + [s.value for s in at.success])
    assert "snapshot" in all_text_after.lower()


def test_step3_training_controls_and_live_polling(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    paths, _ = setup_test_environment(tmp_path)

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Huấn luyện AI").run()
    assert not at.exception

    # Check hyperparameter controls
    assert len(at.number_input) >= 2  # epochs, batch, etc.
    assert len(at.checkbox) >= 1  # amp

    # Check Start and Stop buttons exist
    button_labels = [b.label.lower() for b in at.button]
    assert any("bắt đầu" in lbl for lbl in button_labels)
    assert any("dừng" in lbl for lbl in button_labels)

    # Check metrics / log elements exist
    all_text = " ".join([m.value for m in at.markdown])
    assert "epoch" in all_text.lower()
    assert "map" in all_text.lower()
    assert "loss" in all_text.lower()


def test_step4_evaluation_and_production_promotion(tmp_path: Path, monkeypatch):
    monkeypatch.setenv("TRAFFICVISION_ROOT", str(tmp_path))
    paths, _ = setup_test_environment(tmp_path)

    # Create a candidate in runs
    create_test_candidate(paths.runs, run_id="run_promote_001")

    app_path = str(Path(__file__).parents[2] / "app.py")
    at = AppTest.from_file(app_path, default_timeout=25)
    at.run()
    at.sidebar.radio[0].set_value("Huấn luyện AI").run()
    assert not at.exception

    all_text = " ".join([m.value for m in at.markdown])
    assert "map@50" in all_text.lower() or "map50" in all_text.lower()
    assert "cpu" in all_text.lower()

    # Locate promote button
    promote_btns = [b for b in at.button if "production" in b.label.lower() or "thăng cấp" in b.label.lower()]
    assert len(promote_btns) >= 1

    promote_btns[0].click().run()
    assert not at.exception

    all_text_after = " ".join([s.value for s in at.success] + [m.value for m in at.markdown])
    assert "production" in all_text_after.lower()

    # Verify model in registry is promoted
    reg = ModelRegistry(paths)
    prod = reg.get_production()
    assert len(prod.manifest.class_names) == 82
    assert prod.manifest.stage == "production"
