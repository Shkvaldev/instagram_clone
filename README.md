# Instagram clone 
> Cloning bookmarks and followings to a new account

## Usage
1. Clone repo:
```bash
git clone <repo>
```
2. Create venv:
```bash
python -m venv .venv
source .venv/bin/activate
```
3. Install requirements
```bash
pip install -r requirements.txt
```
4. Run app:
```bash
# Dev
fastapi dev app.py --port 3000

# Release
fastapi run app.py --port 3000
```
