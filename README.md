# yonmy.com

Hugo 정적 블로그. `main`에 push하면 GitHub Actions가 빌드해 GitHub Pages로 배포한다.

- 글: `content/posts/*.md` (front matter: title, date, url, categories, tags)
- 워드프레스 원본: `raw/posts.json` → `python convert.py` 로 재변환 가능
- 로컬 미리보기: `hugo server`
