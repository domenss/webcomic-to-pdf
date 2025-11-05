# WebComic2PDF

Simple script to download comics from Marmota Comics and convert them to PDF.

## 🚀 Installation

```bash
# 1. Create virtual environment
python3 -m venv .venv

# 2. Activate virtual environment
source .venv/bin/activate  # On Linux/Mac
# .venv\Scripts\activate   # On Windows

# 3. Install dependencies
pip install -r requirements.txt

# 4. Install browser
playwright install chromium
playwright install-deps
```

## 📖 Usage

### 1. Create urls.txt file

```text
https://marmota.me/comic/batman-damned-2018/batman-damned-1/|Batman: Dammed #1
https://marmota.me/comic/nightwing-2016/nightwing-65-1-anual-2/|Nightwing 2016
```

### 2. Run

```bash
source .venv/bin/activate

python3 webcomic2pdf.py
```

PDFs will be created in the current directory.

## 🛠️ Dependencies

- playwright
- requests
- Pillow
- img2pdf
