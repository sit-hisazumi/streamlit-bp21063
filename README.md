[![Open in Codespaces](https://classroom.github.com/assets/launch-codespace-2972f46106e565e64193e422d61a12cf1da4916b45550586e14ef0a7c637dd04.svg)](https://classroom.github.com/open-in-codespaces?assignment_repo_id=22079215)
# Streamlit Template

**複数のStreamlitアプリケーション開発用テンプレート**

GitHub CodespacesとVSCodeでの開発に最適化された、複数のStreamlitアプリを効率的に管理できるテンプレートプロジェクトです。

## 🚀 クイックスタート

### GitHub Codespaces（推奨）

1. **このリポジトリをフォーク**
2. **Codespace作成**: 緑の「Code」ボタン → 「Create codespace on main」
3. **自動セットアップ完了を待機**
4. **アプリ実行**:
   ```bash
   streamlit run hello_world.py
   ```

### ローカル環境

#### uv使用（推奨）
```bash
git clone <your-repo-url>
cd streamlit-template
uv sync
uv run streamlit run hello_world.py
```

#### pip使用
```bash
git clone <your-repo-url>
cd streamlit-template
pip install -r requirements.txt
streamlit run hello_world.py
```

## 📁 プロジェクト構造

```
streamlit-template/
├── hello_world.py             # メインアプリ
├── data/                      # データファイル
├── utils/                     # 共通ユーティリティ関数
├── scripts/                   # 管理・自動化スクリプト
├── .devcontainer/             # GitHub Codespaces設定
├── .vscode/                   # VSCode設定
├── .streamlit/                # Streamlit設定・シークレット
├── pyproject.toml             # プロジェクト設定（uv対応）
├── requirements.txt           # pip互換依存関係
└── .gitignore                 # Git除外設定
```

## 🎯 使用方法

### 新しいアプリの作成

```python
# my_new_app.py
import streamlit as st

st.title("My New App 🚀")
st.write("Hello, Streamlit!")

name = st.text_input("Your name:")
if name:
    st.success(f"Hello, {name}!")
```

### 複数アプリの実行

```bash
# 異なるポートで複数アプリを同時実行
streamlit run hello_world.py --server.port 8501 &
streamlit run my_new_app.py --server.port 8502 &
```

## 🛠️ 開発環境

### 含まれる設定

- **GitHub Codespaces**: 自動環境構築
- **VSCode設定**: Python開発最適化
- **Code Formatter**: Black
- **Linter**: Ruff
- **Streamlit設定**: 開発モード有効

### 推奨VSCode拡張機能

- Python
- Black Formatter
- Ruff
- Pylint

## 🔧 カスタマイズ

### 依存関係の追加

```bash
# uv使用
uv add package-name

# pip使用
pip install package-name
echo "package-name" >> requirements.txt
```

### Streamlit設定

- **基本設定**: `.streamlit/config.toml`
- **シークレット**: `.streamlit/secrets.toml` (gitignoreに含まれます)

### VSCode設定

- **エディタ設定**: `.vscode/settings.json`
- **推奨拡張**: `.vscode/extensions.json`

## 🔐 セキュリティ

- **`.streamlit/secrets.toml`** は自動的にgitignoreされます
- **APIキー**は secrets.toml で管理してください
- **本番環境**では環境変数を使用してください

## 📦 デプロイ

### Streamlit Community Cloud

1. GitHubにプッシュ
2. [share.streamlit.io](https://share.streamlit.io) でデプロイ
3. メインファイル: `hello_world.py` または作成したアプリファイル

### その他のプラットフォーム

- Heroku
- Railway
- Render
- Docker

## 🤝 貢献

プルリクエストやイシューを歓迎します！

## 📄 ライセンス

MIT License

---

**🌟 Happy Streamlit Development!**