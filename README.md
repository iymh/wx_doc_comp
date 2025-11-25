# watsonx .ai と WatsonDiccoveryを使ったドキュメント検索アプリ

## for IBM Buisiness Partner only

## Python環境のセットアップ
```
# Set virtual environment
python -m venv .venv
source .venv/bin/activate
pip list
```
* 初回で Packageが pip と setuptools の２つだけの状態を確認
* 他のフォルダを参照したりしている場合は、 source の行を再度実行する

### モジュールを一括インストールする場合
```
# Install the required modules
pip install -r requirements.txt
```

### モジュールを個別でインストールする場合
```
# add python modules
pip install uvicorn fastapi python-dotenv langchain gunicorn

# add IBM SDK
pip install ibm-watsonx-ai langchain_ibm ibm-watson ibm-code-engine-sdk

```


## 実行
* サーバを起動
  ```
  # python server.py
  ```
* http://localhost:8000 等でブラウザで表示


## CodeEngine へ デプロイ

デプロイには、Pythonスクリプトを使用する自動化された方法と、IBM Cloudコンソールを使用する手動の方法の2通りがあります。

### 方法A: Pythonスクリプトで自動デプロイ (推奨)

Pythonスクリプト `deploy.py` を使用して、**GitHubのソースコードからビルドを行い**、アプリケーションをデプロイします。

#### 1. 事前準備
*   **IBM Cloud アカウント**: APIキーが必要です。
*   **Code Engine プロジェクト**: 事前にコンソールまたはCLIで作成済みのプロジェクトが必要です（プロジェクトIDを使用します）。
*   **レジストリシークレット**: ビルドしたイメージを保存するために、Code Engineプロジェクト内にレジストリシークレットを作成しておく必要があります（例: `ce-registry-secret`）。

#### 2. 設定ファイルの準備

デプロイ設定は `ce_config.json` で管理し、アプリケーションの環境変数は `.env` で管理します。

**A. デプロイ設定 (`ce_config.json`)**

`ce_config.json.sample` をコピーして `ce_config.json` を作成し、値を設定してください。

```bash
cp ce_config.json.sample ce_config.json
```

`ce_config.json` の内容:
```json
{
    "IBM_REGION": "us-south",
    "CE_PROJECT_ID": "YOUR_PROJECT_GUID",
    "CE_APP_NAME": "wx-doc-comp-app",
    "CE_APP_PORT": 8000,
    "CE_MIN_INSTANCES": 1,
    "BUILD_CONFIG": {
        "GIT_REPO_URL": "https://github.com/YOUR_ORG/YOUR_REPO",
        "GIT_BRANCH": "main",
        "IMAGE_URL": "us.icr.io/namespace/image:tag",
        "REGISTRY_SECRET_NAME": "your-registry-secret"
    }
}
```
※ `API_KEY` もこのファイルに記述可能ですが、セキュリティのため `.env` (または環境変数) に設定することを推奨します。

**B. アプリケーション環境変数 (`.env`)**

`.env.sample` をコピーして `.env` を作成し、Watsonx.ai などのAPIキーを設定してください。これらはデプロイされたアプリに環境変数として渡されます。

```bash
cp .env.sample .env
```

### 3. デプロイの実行

以下のコマンドを実行すると、ソースコードのビルドからデプロイまでが自動で行われます。

```bash
python deploy.py
```

ビルドをスキップしてデプロイのみ行う場合（コード変更がない場合など）:
```bash
python deploy.py --skip-build
```
### 方法B: コンソールから手動デプロイ

  1. Code Engineプロジェクトの概要ページで アプリケーションの作成 をクリックします。
  2. ソース・コード を選択し、ビルド詳細の指定 をクリックします。
  3. ソース タブで以下の情報を入力します。
     * コード・リポジトリー URL: SSH形式のURLを入力します。
       ```
       https://github.com/iymh/wx_doc_comp
       ```
     * 次へ をクリックし、戦略 タブに進みます。
  4. Dockerfileへのパス: Dockerfile (ソースコードのルートディレクトリからの相対パスなので、このままでOK)
     * 必要に応じてリソース（CPU、メモリーなど）を設定し、次へ をクリックします。
  5. 出力 タブで、ビルドされるコンテナイメージのレジストリー情報を確認・設定します。
     * 初回はレジストリシークレットを作成する必要があります。
     * 適当に名前をつけて作成。
     * Done をクリックします。
  6. 環境変数を .envファイルの内容を追加します。
  7. イメージ始動オプションで .env内で指定したPORT番号を指定します。
     * デフォルトは8000　
  8. 最後にデプロイの実行をクリックして開始します。
  9. デプロイが成功したら アプリケーションのURL をブラウザで開く。


## 開発ツール
### ESLint
JavaScript/HTMLのコード品質を確保するためのツールです。

```
# ESLintとプラグインを個別にインストール
npm install eslint eslint-plugin-html globals --save-dev
```
```
# または、package.jsonがあるため一括でインストール
npm install
```

* eslint.config.jsファイルには
  * JavaScriptとHTML内のJavaScriptの両方をチェックする設定が含まれています。
  * 設定を変更する場合は、このファイルを編集してください。

* ESLintはVSCode上で自動的に実行されます。
  * ESLint拡張機能がインストールされていれば、コードを編集する際にリアルタイムでエラーや警告が表示されます。
  * もし自動実行が動作しない場合は、VSCodeを再起動してみてください。

###

