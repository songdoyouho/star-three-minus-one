# windows 需使用 conda 安裝 pytorch 及 ultralytics，請勿使用 pipenv 
from ultralytics import YOLO
import torch

if __name__ == "__main__":
    # 檢查 GPU 可用性
    print("=" * 50)
    print("設備檢查:")
    print(f"CUDA 可用: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"CUDA 版本: {torch.version.cuda}")
        print(f"GPU 數量: {torch.cuda.device_count()}")
        for i in range(torch.cuda.device_count()):
            print(f"  GPU {i}: {torch.cuda.get_device_name(i)}")
            print(f"    記憶體: {torch.cuda.get_device_properties(i).total_memory / 1024**3:.2f} GB")
    else:
        print("警告: 未檢測到 GPU，將使用 CPU")
    print("=" * 50)
    
    # Create a new YOLO model from scratch
    model = YOLO("yolo11x.yaml")

    # Load a pretrained YOLO model (recommended for training)
    model = YOLO("yolo11x.pt")
    
    # 確認模型設備
    print(f"\n模型設備: {next(model.model.parameters()).device}")
    if torch.cuda.is_available():
        print("✓ 模型已載入到 GPU")
    else:
        print("⚠ 模型在 CPU 上運行")

    # Train the model using the 'coco8.yaml' dataset for 3 epochs
    # 在 Windows 上設置 workers=0 以避免 multiprocessing 問題
    results = model.train(data="coco8.yaml", epochs=3, workers=0)

    # Evaluate the model's performance on the validation set
    results = model.val()

    # Perform object detection on an image using the model
    print("\n" + "=" * 50)
    print("執行 Inference...")
    print(f"Inference 設備: {next(model.model.parameters()).device}")
    if torch.cuda.is_available():
        print("✓ Inference 在 GPU 上執行")
    results = model("https://ultralytics.com/images/bus.jpg")
    print("=" * 50)

    # Export the model to ONNX format
    success = model.export(format="onnx")