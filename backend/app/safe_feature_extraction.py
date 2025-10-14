import ipaddress
import re
import urllib.request
from bs4 import BeautifulSoup
import socket
import requests
from urllib.parse import urlparse
import time

class SafeFeatureExtraction:
    def __init__(self, url, timeout=10):
        self.features = []
        self.url = url
        self.domain = ""
        self.urlparse = ""
        self.response = ""
        self.soup = ""
        self.timeout = timeout

        try:
            # Thiết lập timeout và headers
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            
            # Sử dụng session để tái sử dụng connection
            session = requests.Session()
            session.headers.update(headers)
            
            self.response = session.get(url, timeout=self.timeout, allow_redirects=True)
            self.soup = BeautifulSoup(self.response.text[:10000], 'html.parser')  # Giới hạn nội dung
            session.close()
        except Exception as e:
            print(f"Warning: Cannot fetch content for {url}: {e}")
            pass

        try:
            self.urlparse = urlparse(url)
            self.domain = self.urlparse.netloc
        except Exception as e:
            print(f"Warning: Cannot parse URL {url}: {e}")
            pass

        # Extract features với error handling
        self.extract_all_features()

    def extract_all_features(self):
        """Extract all features with individual error handling"""
        feature_methods = [
            self.UsingIp, self.LongUrl, self.ShortUrl, self.Symbol, 
            self.Redirecting, self.PrefixSuffix, self.SubDomains, 
            self.Hppts, self.Favicon, self.NonStdPort, self.HTTPSDomainURL,
            self.RequestURL, self.AnchorURL, self.LinksInScriptTags,
            self.ServerFormHandler, self.InfoEmail, self.WebsiteForwarding,
            self.StatusBarCust, self.DisableRightClick, self.UsingPopupWindow,
            self.IframeRedirection, self.LinksPointingToPage
        ]
        
        for method in feature_methods:
            try:
                feature_value = method()
                self.features.append(feature_value)
            except Exception as e:
                print(f"Error in {method.__name__} for {self.url}: {e}")
                self.features.append(0)  # Default value

    def UsingIp(self):
        try:
            hostname = self.urlparse.netloc if self.urlparse else self.url
            ip_pattern = r'((25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.){3}(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)'
            
            if hostname and re.search(ip_pattern, hostname):
                return -1
            else:
                return 1
        except:
            return 1

    def LongUrl(self):
        try:
            if len(self.url) < 54:
                return 1
            elif len(self.url) >= 54 and len(self.url) <= 75:
                return 0
            else:
                return -1
        except:
            return 0

    def ShortUrl(self):
        try:
            shortening_services = r"bit\.ly|goo\.gl|shorte\.st|go2l\.ink|x\.co|ow\.ly|t\.co|tinyurl|tr\.im|is\.gd|cli\.gs|" \
                                r"yfrog\.com|migre\.me|ff\.im|tiny\.cc|url4\.eu|twit\.ac|su\.pr|twurl\.nl|snipurl\.com|" \
                                r"short\.to|BudURL\.com|ping\.fm|post\.ly|Just\.as|bkite\.com|snipr\.com|fic\.kr|loopt\.us|" \
                                r"doiop\.com|short\.ie|kl\.am|wp\.me|rubyurl\.com|om\.ly|to\.ly|bit\.do|t\.co|lnkd\.in|db\.tt|" \
                                r"qr\.ae|adf\.ly|goo\.gl|bitly\.com|cur\.lv|tinyurl\.com|ow\.ly|bit\.ly|ity\.im|q\.gs|is\.gd|" \
                                r"po\.st|bc\.vc|twitthis\.com|u\.to|j\.mp|buzurl\.com|cutt\.us|u\.bb|yourls\.org|x\.co|" \
                                r"prettylinkpro\.com|scrnch\.me|filoops\.info|vzturl\.com|qr\.net|1url\.com|tweez\.me|v\.gd|" \
                                r"tr\.im|link\.zip\.net"

            if re.search(shortening_services, self.url):
                return -1
            else:
                return 1
        except:
            return 1

    def Symbol(self):
        try:
            if re.findall("@", self.url):
                return -1
            return 1
        except:
            return 1

    def Redirecting(self):
        try:
            if self.url.rfind('//') > 6:
                return -1
            return 1
        except:
            return 1

    def PrefixSuffix(self):
        try:
            if self.domain and re.findall('\-', self.domain):
                return -1
            return 1
        except:
            return 1

    def SubDomains(self):
        try:
            dot_count = len(re.findall("\.", self.url))
            if dot_count == 1:
                return 1
            elif dot_count == 2:
                return 0
            return -1
        except:
            return 0

    def Hppts(self):
        try:
            if self.urlparse and 'https' in self.urlparse.scheme:
                return 1
            return -1
        except:
            return -1

    # Các phương thức khác với error handling tương tự
    def Favicon(self):
        try:
            if self.soup:
                for head in self.soup.find_all('head'):
                    for link in head.find_all('link', href=True):
                        dots = [x.start(0) for x in re.finditer('\.', link['href'])]
                        if self.url in link['href'] or len(dots) == 1 or self.domain in link['href']:
                            return 1
                return -1
            return 0
        except:
            return 0

    def NonStdPort(self):
        try:
            if self.urlparse and self.urlparse.port:
                port = self.urlparse.port
                if port != 80 and port != 443:
                    return -1
            return 1
        except:
            return 1

    def HTTPSDomainURL(self):
        try:
            if self.domain and 'https' in self.domain:
                return -1
            return 1
        except:
            return 1

    # 13. RequestURL
    def RequestURL(self):
        try:
            i = 0
            success = 0
            
            for img in self.soup.find_all('img', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', img['src'])]
                if self.url in img['src'] or self.domain in img['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            for audio in self.soup.find_all('audio', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', audio['src'])]
                if self.url in audio['src'] or self.domain in audio['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            for embed in self.soup.find_all('embed', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', embed['src'])]
                if self.url in embed['src'] or self.domain in embed['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            for iframe in self.soup.find_all('iframe', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', iframe['src'])]
                if self.url in iframe['src'] or self.domain in iframe['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            try:
                percentage = success/float(i) * 100
                if percentage < 22.0:
                    return 1
                elif((percentage >= 22.0) and (percentage < 61.0)):
                    return 0
                else:
                    return -1
            except:
                return 0
        except:
            return -1

    # 14. AnchorURL
    def AnchorURL(self):
        try:
            i, unsafe = 0, 0
            for a in self.soup.find_all('a', href=True):
                if "#" in a['href'] or "javascript" in a['href'].lower() or "mailto" in a['href'].lower() or not (self.url in a['href'] or self.domain in a['href']):
                    unsafe = unsafe + 1
                i = i + 1

            try:
                percentage = unsafe / float(i) * 100
                if percentage < 31.0:
                    return 1
                elif ((percentage >= 31.0) and (percentage < 67.0)):
                    return 0
                else:
                    return -1
            except:
                return -1
        except:
            return -1

    # 15. LinksInScriptTags
    def LinksInScriptTags(self):
        try:
            i, success = 0, 0
            
            for link in self.soup.find_all('link', href=True):
                dots = [x.start(0) for x in re.finditer(r'\.', link['href'])]
                if self.url in link['href'] or self.domain in link['href'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            for script in self.soup.find_all('script', src=True):
                dots = [x.start(0) for x in re.finditer(r'\.', script['src'])]
                if self.url in script['src'] or self.domain in script['src'] or len(dots) == 1:
                    success = success + 1
                i = i+1

            try:
                percentage = success / float(i) * 100
                if percentage < 17.0:
                    return 1
                elif((percentage >= 17.0) and (percentage < 81.0)):
                    return 0
                else:
                    return -1
            except:
                return 0
        except:
            return -1

    # 16. ServerFormHandler
    def ServerFormHandler(self):
        try:
            if len(self.soup.find_all('form', action=True))==0:
                return 1
            else :
                for form in self.soup.find_all('form', action=True):
                    if form['action'] == "" or form['action'] == "about:blank":
                        return -1
                    elif self.url not in form['action'] and self.domain not in form['action']:
                        return 0
                    else:
                        return 1
        except:
            return -1

    # 17. InfoEmail
    def InfoEmail(self):
        try:
            if re.findall(r"[mail\(\)|mailto:?]", self.response.text):
                return -1
            else:
                return 1
        except:
            return -1

    # 19. WebsiteForwarding
    def WebsiteForwarding(self):
        try:
            if len(self.response.history) <= 1:
                return 1
            elif len(self.response.history) <= 4:
                return 0
            else:
                return -1
        except:
             return -1

    # 20. StatusBarCust
    def StatusBarCust(self):
        try:
            if re.findall("<script>.+onmouseover.+</script>", self.response.text):
                return 1
            else:
                return -1
        except:
             return -1

    # 21. DisableRightClick
    def DisableRightClick(self):
        try:
            if re.findall(r"event.button ?== ?2", self.response.text):
                return 1
            else:
                return -1
        except:
             return -1

    # 22. UsingPopupWindow
    def UsingPopupWindow(self):
        try:
            if re.findall(r"alert\(", self.response.text):
                return 1
            else:
                return -1
        except:
             return -1

    # 23. IframeRedirection
    def IframeRedirection(self):
        try:
            if re.findall(r"[<iframe>|<frameBorder>]", self.response.text):
                return 1
            else:
                return -1
        except:
             return -1

    # 29. LinksPointingToPage
    def LinksPointingToPage(self):
        try:
            number_of_links = len(re.findall(r"<a href=", self.response.text))
            if number_of_links == 0:
                return 1
            elif number_of_links <= 2:
                return 0
            else:
                return -1
        except:
            return -1
