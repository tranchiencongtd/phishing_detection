import pandas as pd
import os
import glob

def recovery_from_checkpoint():
    """
    Khôi phục và gộp các checkpoint files
    """
    
    # Tìm tất cả checkpoint files
    checkpoint_files = glob.glob('checkpoint_features_*.csv')
    
    if not checkpoint_files:
        print("Không tìm thấy checkpoint files")
        return None
    
    # Sắp xếp theo số thứ tự
    checkpoint_files.sort(key=lambda x: int(x.split('_')[-1].split('.')[0]))
    
    print(f"Tìm thấy {len(checkpoint_files)} checkpoint files:")
    for file in checkpoint_files:
        size = os.path.getsize(file)
        df = pd.read_csv(file)
        print(f"  {file}: {len(df)} records, {size/1024/1024:.1f}MB")
    
    # Lấy checkpoint cuối cùng (lớn nhất)
    latest_checkpoint = checkpoint_files[-1]
    print(f"\nSử dụng checkpoint mới nhất: {latest_checkpoint}")
    
    df = pd.read_csv(latest_checkpoint)
    
    print(f"Recovered dataset:")
    print(f"  Shape: {df.shape}")
    print(f"  Label distribution:")
    print(df['Label'].value_counts())
    
    # Lưu thành file final
    df.to_csv('recovered_features_final.csv', index=False)
    print(f"\nĐã lưu file recovered_features_final.csv")
    
    return df

def get_last_processed_index():
    """
    Lấy index của record cuối cùng được xử lý
    """
    checkpoint_files = glob.glob('checkpoint_features_*.csv')
    
    if not checkpoint_files:
        return 0
    
    # Lấy số lớn nhất từ tên file
    numbers = []
    for file in checkpoint_files:
        try:
            num = int(file.split('_')[-1].split('.')[0])
            numbers.append(num)
        except:
            pass
    
    if numbers:
        last_index = max(numbers)
        print(f"Index cuối cùng được xử lý: {last_index}")
        return last_index
    
    return 0

if __name__ == "__main__":
    print("=== RECOVERY TOOL ===")
    print("1. Khôi phục từ checkpoint")
    print("2. Kiểm tra index cuối cùng")
    
    choice = input("Chọn (1 hoặc 2): ").strip()
    
    if choice == "1":
        recovery_from_checkpoint()
    elif choice == "2":
        last_idx = get_last_processed_index()
        print(f"Bạn có thể tiếp tục từ index: {last_idx}")
    else:
        print("Lựa chọn không hợp lệ")