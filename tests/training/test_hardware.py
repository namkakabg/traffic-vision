from __future__ import annotations

from types import SimpleNamespace

from trafficvision.training.hardware import detect_training_devices


def test_detect_training_devices_prefers_a_verified_cuda_gpu() -> None:
    fake_torch = SimpleNamespace(
        cuda=SimpleNamespace(
            is_available=lambda: True,
            device_count=lambda: 1,
            get_device_name=lambda index: "NVIDIA GeForce GTX 1050 Ti",
        )
    )

    devices = detect_training_devices(torch_module=fake_torch)

    assert [(device.value, device.is_cuda) for device in devices] == [("0", True), ("cpu", False)]
    assert devices[0].label == "GPU 0 - NVIDIA GeForce GTX 1050 Ti"


def test_detect_training_devices_keeps_cpu_when_cuda_is_unavailable() -> None:
    fake_torch = SimpleNamespace(
        cuda=SimpleNamespace(is_available=lambda: False, device_count=lambda: 0)
    )

    devices = detect_training_devices(torch_module=fake_torch)

    assert [(device.value, device.is_cuda) for device in devices] == [("cpu", False)]
