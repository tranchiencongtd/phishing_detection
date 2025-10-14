import pandas as pd
from urllib.parse import urlparse

def extract_domain(url):
    """
    Trích xuất domain từ URL
    """
    try:
        parsed_url = urlparse(url)
        return parsed_url.netloc
    except:
        return ""

# Đọc file dataset gốc
print("Đang đọc file dataset.csv...")
df1 = pd.read_csv('dataset.csv')
print(f"Dataset.csv có {len(df1)} dòng và {len(df1.columns)} cột")

# Đọc file phishing_url
print("Đang đọc file phishing_url.csv...")
df2 = pd.read_csv('phishing_url.csv')
print(f"Phishing_url.csv có {len(df2)} dòng và {len(df2.columns)} cột")

# Chuẩn hóa tên cột và giá trị
df2.columns = df2.columns.str.lower()
# Chuẩn hóa giá trị type thành chữ thường
df2['type'] = df2['type'].str.lower()

print("\nMột vài dòng đầu tiên từ dataset.csv:")
print(df1.head())
print("\nMột vài dòng đầu tiên từ phishing_url.csv (sau chuẩn hóa):")
print(df2.head())

# Ghép hai dataset lại với nhau
print(f"\nGhép hai dataset...")
df = pd.concat([df1, df2], ignore_index=True)
print(f"Dataset sau khi ghép có {len(df)} dòng và {len(df.columns)} cột")

# Tạo cột domain mới từ cột url
print("\nĐang tạo cột domain...")
df['domain'] = df['url'].apply(extract_domain)

# Sắp xếp lại thứ tự cột: url, domain, type
df = df[['url', 'domain', 'type']]

# Loại bỏ các domain bị trùng lặp, chỉ giữ lại bản ghi đầu tiên
# print(f"\nTrước khi loại bỏ duplicate: {len(df)} dòng")
# df = df.drop_duplicates(subset=['domain'], keep='first')
# print(f"Sau khi loại bỏ duplicate: {len(df)} dòng")

print("\nDataset sau khi thêm cột domain và loại bỏ duplicate:")
print(df.head(10))

# Đếm số lượng các type
print("\n=== THỐNG KÊ SỐ LƯỢNG CÁC TYPE ===")
type_counts = df['type'].value_counts()
print(f"Số loại type khác nhau: {len(type_counts)}")
print("\nSố lượng từng type:")
for type_name, count in type_counts.items():
    print(f"  - {type_name}: {count:,} records ({count/len(df)*100:.2f}%)")

# Kiểm tra một số thống kê
print(f"\nSố lượng domain duy nhất: {df['domain'].nunique()}")
print("\nMột số domain phổ biến nhất:")
print(df['domain'].value_counts().head(10))

# Lưu file mới
output_file = 'dataset_with_domain.csv'
df.to_csv(output_file, index=False)
print(f"\nĐã lưu dataset mới vào file: {output_file}")

# Hiển thị thông tin về file đầu ra
print(f"\nFile mới có {len(df)} dòng và {len(df.columns)} cột: {list(df.columns)}")