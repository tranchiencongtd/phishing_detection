import pandas as pd
import numpy as np
import time
import gc
from safe_feature_extraction import SafeFeatureExtraction

def safe_feature_extraction(start_idx=0, batch_size=100):
    """
    Trích xuất đặc trưng một cách an toàn với batch processing
    """
    
    # Load data
    print("Đang tải dữ liệu...")
    data_url = pd.read_csv("DataFiles/dataset_with_domain.csv")
    print(f"Total dataset size: {data_url.shape}")
    
    # Sample data
    np.random.seed(42)
    legitimate_data = data_url[data_url['type'] == 'legitimate']
    phishing_data = data_url[data_url['type'] == 'phishing']
    
    legitimate_sample = legitimate_data.sample(n=5000, random_state=42)
    phishing_sample = phishing_data.sample(n=5000, random_state=42)
    
    sampled_data = pd.concat([legitimate_sample, phishing_sample], ignore_index=True)
    sampled_data = sampled_data.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"Sampled dataset size: {sampled_data.shape}")
    
    # Load existing features if available
    features = []
    if start_idx > 0:
        try:
            existing_df = pd.read_csv(f'checkpoint_features_{start_idx}.csv')
            features = existing_df.values.tolist()
            print(f"Đã tải {len(features)} features từ checkpoint")
        except:
            print("Không thể tải checkpoint, bắt đầu từ đầu")
            start_idx = 0
    
    feature_names = ['UsingIp', 'LongUrl', 'ShortUrl', 'Symbol', 'Redirecting', 'PrefixSuffix',
                     'SubDomains', 'Https', 'Favicon', 'NonStdPort', 'HTTPSDomainURL', 'RequestURL', 
                     'AnchorURL', 'LinksInScriptTags', 'ServerFormHandler', 'InfoEmail', 
                     'WebsiteForwarding', 'StatusBarCust', 'DisableRightClick', 'UsingPopupWindow',
                     'IframeRedirection', 'LinksPointingToPage', 'Label']
    
    total_samples = len(sampled_data)
    
    print(f"Bắt đầu từ mẫu {start_idx}/{total_samples}")
    
    for i in range(start_idx, total_samples, batch_size):
        batch_end = min(i + batch_size, total_samples)
        print(f"\n=== Xử lý batch {i}-{batch_end-1} ===")
        
        batch_features = []
        
        for j in range(i, batch_end):
            try:
                url = sampled_data['url'].iloc[j]
                label = sampled_data['type'].iloc[j]
                
                print(f"[{j}/{total_samples}] Processing: {url[:80]}...")
                
                # Sử dụng SafeFeatureExtraction với timeout ngắn
                extractor = SafeFeatureExtraction(url, timeout=5)
                extracted_features = extractor.features.copy()
                extracted_features.append(1 if label == 'legitimate' else -1)
                
                batch_features.append(extracted_features)
                
                # Cleanup
                del extractor
                 
                # Delay để tránh overload
                time.sleep(0.2)
                
            except Exception as e:
                print(f"Lỗi tại mẫu {j}: {e}")
                # Thêm default features
                default_features = [0] * 22 + [1 if sampled_data['type'].iloc[j] == 'legitimate' else -1]
                batch_features.append(default_features)
        
        # Thêm batch vào features chính
        features.extend(batch_features)
        
        # Lưu checkpoint
        checkpoint_df = pd.DataFrame(features, columns=feature_names)
        checkpoint_df.to_csv(f'checkpoint_features_{batch_end}.csv', index=False)
        print(f"Đã lưu checkpoint với {len(features)} features")
        
        # Memory cleanup
        gc.collect()
        
        print(f"Hoàn thành batch. Tổng cộng: {len(features)} features")
        
        # Pause giữa các batch
        time.sleep(1)
    
    # Lưu kết quả cuối cùng
    final_df = pd.DataFrame(features, columns=feature_names)
    final_df.to_csv('extracted_features_10k_samples_final.csv', index=False)
    
    print(f"\n=== HOÀN THÀNH ===")
    print(f"Tổng số features: {len(features)}")
    print(f"Label distribution:")
    print(final_df['Label'].value_counts())
    
    return final_df

if __name__ == "__main__":
    # Bạn có thể điều chỉnh start_idx nếu muốn tiếp tục từ một vị trí cụ thể
    start_idx = 0  # Thay đổi thành vị trí bạn muốn bắt đầu
    batch_size = 50  # Kích thước batch nhỏ hơn để tránh timeout
    
    result_df = safe_feature_extraction(start_idx=start_idx, batch_size=batch_size)
    print("Xong!")