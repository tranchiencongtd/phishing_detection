#%% md
# # **Phishing Detection: Trích xuất đặc trưng**
# 
# 
#%%
#importing required packages for this module
import sys
import ipaddress
import re
from dateutil.parser import parse as date_parse
from urllib.parse import urlparse
import pandas as pd

# Thêm đường dẫn Google Drive vào sys.path
#sys.path.append('/content/drive/MyDrive/an_toan_thong_tin_3')

# Import feature extraction class từ Google Drive
from feature import FeatureExtraction

#loading the URLs data to dataframe
data_url = pd.read_csv("DataFiles/dataset_with_domain.csv")
print(f"Total dataset size: {data_url.shape}")
print(f"Type distribution:")
print(data_url['type'].value_counts())
#%%
data_url.shape
#%%
# Lấy ngẫu nhiên 5000 mẫu legitimate và 5000 mẫu phishing
import numpy as np

# Đặt seed để kết quả có thể tái lập
np.random.seed(42)

# Lọc dữ liệu theo type
legitimate_data = data_url[data_url['type'] == 'legitimate']
phishing_data = data_url[data_url['type'] == 'phishing']

print(f"Available legitimate URLs: {len(legitimate_data)}")
print(f"Available phishing URLs: {len(phishing_data)}")

# Lấy ngẫu nhiên 5000 mẫu từ mỗi loại
legitimate_sample = legitimate_data.sample(n=5000, random_state=42)
phishing_sample = phishing_data.sample(n=5000, random_state=42)

# Gộp lại và xáo trộn
sampled_data = pd.concat([legitimate_sample, phishing_sample], ignore_index=True)
sampled_data = sampled_data.sample(frac=1, random_state=42).reset_index(drop=True)

print(f"Final sampled dataset size: {sampled_data.shape}")
print(f"Sampled type distribution:")
print(sampled_data['type'].value_counts())

# Hiển thị một vài mẫu
sampled_data.head()
#%% md
# # **Feature Extraction:**
# 
# Trích xuất đặc trưng
# 
# 
# 1.   Address Bar based Features
# 
# 
#%% md
# ### **3.1. Address Bar Based Features:**
# 
# 
# 1.1. Address Bar based Features
# 1.1.1.	Using the IP Address
# 1.1.2.	Long URL to Hide the Suspicious Part
# 1.1.3.	Using URL Shortening Services “TinyURL”
# 1.1.4.	URL’s having “@” Symbol
# 1.1.5.	Redirecting using “//”
# 1.1.6.	Adding Prefix or Suffix Separated by (-) to the Domain
# 1.1.7.	Sub Domain and Multi Sub Domains
# 1.1.8.	HTTPS (Hyper Text Transfer Protocol with Secure Sockets Layer) 
# 1.1.9.	The Existence of “HTTPS” Token in the Domain Part of the URL
# 
# 
#%%
#Function to extract features
def featureExtraction(url, label):
    try:
        extractor = FeatureExtraction(url)
        features = extractor.features
        features.append(1 if label == 'legitimate' else -1)  # Convert label to numeric
        return features
    except Exception as e:
        print(f"Error processing URL {url}: {e}")
        pass
#%%
# Extracting features từ sampled data
features = []
total_samples = len(sampled_data)

print("Bắt đầu trích xuất đặc trưng...")
print(f"Tổng số mẫu cần xử lý: {total_samples}")

for i in range(total_samples):
    if i % 100 == 0:  # In progress mỗi 1000 mẫu
        print(f"Đã xử lý: {i}/{total_samples} mẫu ({i/total_samples*100:.1f}%)")

    try:
        url = sampled_data['url'].iloc[i]
        label = sampled_data['type'].iloc[i]

        print(url)

        extracted_features = featureExtraction(url, label)
        features.append(extracted_features)
    except Exception as e:
        pass

print(f"Hoàn thành! Đã trích xuất đặc trưng cho {len(features)} URL.")
#%%
#converting the list to dataframe
feature_names = ['UsingIp', 'LongUrl', 'ShortUrl', 'Symbol', 'Redirecting', 'PrefixSuffix',
                 'SubDomains', 'Https', 'Favicon', 'NonStdPort', 'HTTPSDomainURL', 'RequestURL', 
                 'AnchorURL', 'LinksInScriptTags', 'ServerFormHandler', 'InfoEmail', 
                 'WebsiteForwarding', 'StatusBarCust', 'DisableRightClick', 'UsingPopupWindow',
                 'IframeRedirection', 'LinksPointingToPage', 'Label']

data = pd.DataFrame(features, columns=feature_names)
print(f"DataFrame shape: {data.shape}")
print(f"Label distribution:")
print(data['Label'].value_counts())
data.head()
#%%
# Storing the extracted URLs features to csv file
data.to_csv('extracted_features_10k_samples.csv', index=False)
print("Đã lưu file extracted_features_10k_samples.csv thành công!")
print(f"File chứa {len(data)} mẫu với {len(data.columns)} đặc trưng.")
#%% md
# 