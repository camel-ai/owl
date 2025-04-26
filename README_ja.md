<h1 align="center">
	🦉 OWL: 労働力学習の最適化による、現実世界のタスク自動化における一般的なマルチエージェント支援
</h1>


<div align="center">

[![ドキュメント][docs-image]][docs-url]
[![Discord][discord-image]][discord-url]
[![X][x-image]][x-url]
[![Reddit][reddit-image]][reddit-url]
[![Wechat][wechat-image]][wechat-url]
[![Wechat][owl-image]][owl-url]
[![Hugging Face][huggingface-image]][huggingface-url]
[![Star][star-image]][star-url]
[![パッケージライセンス][package-license-image]][package-license-url]


</div>


<hr>

<div align="center">
<h4 align="center">

[中文阅读](https://github.com/camel-ai/owl/tree/main/README_zh.md) |
[コミュニティ](https://github.com/camel-ai/owl#community) |
[インストール](#️-installation) |
[例](https://github.com/camel-ai/owl/tree/main/owl) |
[論文](https://arxiv.org/abs/2303.17760) |
[引用](https://github.com/camel-ai/owl#citation) |
[貢献](https://github.com/camel-ai/owl/graphs/contributors) |
[CAMEL-AI](https://www.camel-ai.org/)

</h4>

<div align="center" style="background-color: #f0f7ff; padding: 10px; border-radius: 5px; margin: 15px 0;">
  <h3 style="color: #1e88e5; margin: 0;">
    🏆 OWLはGAIAベンチマークで<span style="color: #d81b60; font-weight: bold; font-size: 1.2em;">58.18</span>の平均スコアを達成し、オープンソースフレームワークの中で<span style="color: #d81b60; font-weight: bold; font-size: 1.2em;">🏅️ #1</span>にランクインしました！ 🏆
  </h3>
</div>

<div align="center">

🦉 OWLは、タスク自動化の限界を押し広げる最先端のマルチエージェント協力フレームワークであり、[CAMEL-AIフレームワーク](https://github.com/camel-ai/camel)の上に構築されています。

私たちのビジョンは、AIエージェントが現実のタスクを解決するためにどのように協力するかを革命的に変えることです。動的なエージェントの相互作用を活用することで、OWLは多様な分野でより自然で効率的かつ堅牢なタスク自動化を実現します。

</div>

![](./assets/owl_architecture.png)

<br>


</div>

<!-- # Key Features -->
# 📋 目次

- [📋 目次](#-目次)
- [🔥 ニュース](#-ニュース)
- [🎬 デモビデオ](#-デモビデオ)
- [✨️ コア機能](#-コア機能)
- [🛠️ インストール](#️-インストール)
- [🚀 クイックスタート](#-クイックスタート)
- [🧰 ツールキットと機能](#-ツールキットと機能)
  - [モデルコンテキストプロトコル (MCP)](#モデルコンテキストプロトコル-mcp)
- [🌐 ウェブインターフェース](#-ウェブインターフェース)
- [🧪 実験](#-実験)
- [⏱️ 将来の計画](#️-将来の計画)
- [📄 ライセンス](#-ライセンス)
- [🖊️ 引用](#️-引用)
- [🤝 貢献](#-貢献)
- [🔥 コミュニティ](#-コミュニティ)
- [❓ FAQ](#-faq)
- [📚 CAMEL依存関係の探索](#-camel依存関係の探索)
- [⭐ Star History](#-star-history)

# 🔥 ニュース


<div align="center" style="background-color: #e8f5e9; padding: 15px; border-radius: 10px; border: 2px solid #4caf50; margin: 20px 0;">
  <h3 style="color: #2e7d32; margin: 0; font-size: 1.3em;">
    🧩 <b>新機能：コミュニティエージェントチャレンジ！</b> 🧩
  </h3>
  <p style="font-size: 1.1em; margin: 10px 0;">
    AIエージェントのためのユニークなチャレンジをデザインして、あなたの創造力を発揮してください！ <br>
    コミュニティに参加して、最先端のAIによってあなたの革新的なアイデアが実現されるのを見てみましょう。
  </p>
  <p>
    <a href="https://github.com/camel-ai/owl/blob/main/community_challenges.md" style="background-color: #2e7d32; color: white; padding: 8px 15px; text-decoration: none; border-radius: 5px; font-weight: bold;">チャレンジの表示と提出</a>
  </p>
</div>

<div style="background-color: #e3f2fd; padding: 12px; border-radius: 8px; border-left: 4px solid #1e88e5; margin: 10px 0;">
  <h4 style="color: #1e88e5; margin: 0 0 8px 0;">
    🎉 最新の主要アップデート - 2025年3月15日
  </h4>
  <p style="margin: 0;">
    <b>重要な改善点：</b>
    <ul style="margin: 5px 0 0 0; padding-left: 20px;">
      <li>システムの安定性を向上させるために、ウェブベースのUIアーキテクチャを再構築しました 🏗️</li>
      <li>パフォーマンスを向上させるために、OWLエージェントの実行メカニズムを最適化しました 🚀</li>
    </ul>
    <i>今すぐ試して、タスク自動化の改善されたパフォーマンスを体験してください！</i>
  </p>
</div>

- **[2025.03.21]**: OpenRouterモデルプラットフォームを統合し、Geminiツール呼び出しのバグを修正
- **[2025.03.20]**: MCPツールキットにAcceptヘッダーを追加し、Playwrightの自動インストールをサポート
- **[2025.03.16]**: Bing検索、Baidu検索をサポート
- **[2025.03.12]**: SearchToolkitにBocha検索を追加し、Volcano Engineモデルプラットフォームを統合し、AzureおよびOpenAI互換モデルの構造化出力とツール呼び出し機能を強化
- **[2025.03.11]**: MCPToolkit、FileWriteToolkit、およびTerminalToolkitを追加し、MCPツール呼び出し、ファイル書き込み機能、およびターミナルコマンド実行機能を強化
- **[2025.03.09]**: システムとの対話を容易にするためのウェブベースのユーザーインターフェースを追加
- **[2025.03.07]**: 🦉 OWLプロジェクトのコードベースをオープンソース化
- **[2025.03.03]**: OWLはGAIAベンチマークで58.18のスコアを達成し、オープンソースフレームワークの中で1位を獲得

# 🎬 デモビデオ

https://github.com/user-attachments/assets/2a2a825d-39ea-45c5-9ba1-f9d58efbc372

https://private-user-images.githubusercontent.com/55657767/420212194-e813fc05-136a-485f-8df3-f10d9b4e63ec.mp4

# ✨️ コア機能

- **オンライン検索**：複数の検索エンジン（Wikipedia、Google、DuckDuckGo、Baidu、Bochaなど）をサポートし、リアルタイムの情報検索と知識取得を実現
- **マルチモーダル処理**：インターネットまたはローカルのビデオ、画像、音声データの処理をサポート
- **ブラウザ自動化**：Playwrightフレームワークを利用してブラウザの操作をシミュレートし、スクロール、クリック、入力処理、ダウンロード、ナビゲーションなどをサポート
- **ドキュメント解析**：Word、Excel、PDF、PowerPointファイルからコンテンツを抽出し、テキストまたはMarkdown形式に変換
- **コード実行**：Pythonコードを記述してインタープリタを使用して実行
- **組み込みツールキット**：包括的な組み込みツールキットにアクセス可能
  - **モデルコンテキストプロトコル (MCP)**：AIモデルとさまざまなツールやデータソースとの相互作用を標準化するユニバーサルプロトコルレイヤー
  - **コアツールキット**：ArxivToolkit、AudioAnalysisToolkit、CodeExecutionToolkit、DalleToolkit、DataCommonsToolkit、ExcelToolkit、GitHubToolkit、GoogleMapsToolkit、GoogleScholarToolkit、ImageAnalysisToolkit、MathToolkit、NetworkXToolkit、NotionToolkit、OpenAPIToolkit、RedditToolkit、SearchToolkit、SemanticScholarToolkit、SymPyToolkit、VideoAnalysisToolkit、WeatherToolkit、BrowserToolkitなど、専門的なタスクに対応する多くのツールキット

# 🛠️ インストール

OWLは、ワークフロープリファレンスに合わせた複数のインストール方法をサポートしています。最適なオプションを選択してください。

## オプション1：uvを使用する（推奨）

```bash
# GitHubリポジトリをクローン
git clone https://github.com/camel-ai/owl.git

# プロジェクトディレクトリに移動
cd owl

# uvがインストールされていない場合はインストール
pip install uv

# 仮想環境を作成し、依存関係をインストール
# Python 3.10、3.11、3.12の使用をサポート
uv venv .venv --python=3.10

# 仮想環境をアクティブ化
# macOS/Linuxの場合
source .venv/bin/activate
# Windowsの場合
.venv\Scripts\activate

# すべての依存関係を含むCAMELをインストール
uv pip install -e .

# 完了したら仮想環境を終了
deactivate
```

## オプション2：venvとpipを使用する

```bash
# GitHubリポジトリをクローン
git clone https://github.com/camel-ai/owl.git

# プロジェクトディレクトリに移動
cd owl

# 仮想環境を作成
# Python 3.10の場合（3.11、3.12でも動作）
python3.10 -m venv .venv

# 仮想環境をアクティブ化
# macOS/Linuxの場合
source .venv/bin/activate
# Windowsの場合
.venv\Scripts\activate

# requirements.txtからインストール
pip install -r requirements.txt --use-pep517
```

## オプション3：condaを使用する

```bash
# GitHubリポジトリをクローン
git clone https://github.com/camel-ai/owl.git

# プロジェクトディレクトリに移動
cd owl

# conda環境を作成
conda create -n owl python=3.10

# conda環境をアクティブ化
conda activate owl

# オプション1：パッケージとしてインストール（推奨）
pip install -e .

# オプション2：requirements.txtからインストール
pip install -r requirements.txt --use-pep517

# 完了したらconda環境を終了
conda deactivate
```

## **環境変数の設定**

OWLは、さまざまなサービスと対話するために複数のAPIキーを必要とします。`owl/.env_template`ファイルには、すべての必要なAPIキーのプレースホルダーと、それらのサービスに登録するためのリンクが含まれています。

### オプション1：`.env`ファイルを使用する（推奨）

1. **テンプレートをコピーして名前を変更**：
   ```bash
   cd owl
   cp .env_template .env
   ```

2. **APIキーを設定**：
   お好みのテキストエディタで`.env`ファイルを開き、対応するフィールドにAPIキーを挿入します。
   
   > **注意**：最小限の例（`examples/run_mini.py`）の場合、LLM APIキー（例：`OPENAI_API_KEY`）のみを設定する必要があります。

### オプション2：環境変数を直接設定

または、ターミナルで環境変数を直接設定することもできます：

- **macOS/Linux (Bash/Zsh)**：
  ```bash
  export OPENAI_API_KEY="your-openai-api-key-here"
  ```

- **Windows (コマンドプロンプト)**：
  ```batch
  set OPENAI_API_KEY="your-openai-api-key-here"
  ```

- **Windows (PowerShell)**：
  ```powershell
  $env:OPENAI_API_KEY = "your-openai-api-key-here"
  ```

> **注意**：ターミナルで直接設定された環境変数は、現在のセッションでのみ有効です。



## **Dockerでの実行**

OWLはDockerを使用して簡単にデプロイでき、異なるプラットフォーム間で一貫した環境を提供します。

### **セットアップ手順**

```bash
# リポジトリをクローン
git clone https://github.com/camel-ai/owl.git
cd owl

# 環境変数を設定
cp owl/.env_template owl/.env
# .envファイルを編集し、APIキーを入力
```

### **デプロイメントオプション**

#### **オプション1：事前構築されたイメージを使用する（推奨）**

```bash
# このオプションはDocker Hubから即使用可能なイメージをダウンロードします
# 最速であり、ほとんどのユーザーに推奨されます
docker compose up -d

# コンテナ内でOWLを実行
docker compose exec owl bash
cd .. && source .venv/bin/activate
playwright install-deps
xvfb-python examples/run.py
```

#### **オプション2：ローカルでイメージを構築する**

```bash
# Dockerイメージをカスタマイズする必要があるユーザーやDocker Hubにアクセスできないユーザー向け：
# 1. docker-compose.ymlを開く
# 2. "image: mugglejinx/owl:latest"行をコメントアウト
# 3. "build:"セクションとそのネストされたプロパティをコメント解除
# 4. 次に実行：
docker compose up -d --build

# コンテナ内でOWLを実行
docker compose exec owl bash
cd .. && source .venv/bin/activate
playwright install-deps
xvfb-python examples/run.py
```

#### **オプション3：便利なスクリプトを使用する**

```bash
# コンテナディレクトリに移動
cd .container

# スクリプトを実行可能にし、Dockerイメージを構築
chmod +x build_docker.sh
./build_docker.sh

# 質問を使用してOWLを実行
./run_in_docker.sh "your question"
```

### **MCPデスクトップコマンダーのセットアップ**

Docker内でMCPデスクトップコマンダーを使用する場合、次を実行：

```bash
npx -y @wonderwhy-er/desktop-commander setup --force-file-protocol
```

クロスプラットフォームサポート、最適化された構成、トラブルシューティングなど、詳細なDocker使用手順については、[DOCKER_README.md](.container/DOCKER_README_en.md)を参照してください。

# 🚀 クイックスタート

## 基本的な使用法

インストールと環境変数の設定が完了したら、すぐにOWLを使用できます：

```bash
python examples/run.py
```

## 異なるモデルでの実行

### モデルの要件

- **ツール呼び出し**：OWLは、さまざまなツールキットと対話するために強力なツール呼び出し機能を持つモデルを必要とします。モデルはツールの説明を理解し、適切なツール呼び出しを生成し、ツールの出力を処理する必要があります。

- **マルチモーダル理解**：ウェブインタラクション、画像解析、ビデオ処理を含むタスクには、視覚コンテンツとコンテキストを解釈するためのマルチモーダル機能を持つモデルが必要です。

#### サポートされているモデル

AIモデルの設定に関する情報については、[CAMELモデルドキュメント](https://docs.camel-ai.org/key_modules/models.html#supported-model-platforms-in-camel)を参照してください。

> **注意**：最適なパフォーマンスを得るために、OpenAIモデル（GPT-4以降のバージョン）を強く推奨します。私たちの実験では、他のモデルは複雑なタスクやベンチマークで著しく低いパフォーマンスを示すことがあり、特に高度なマルチモーダル理解とツール使用を必要とするタスクでは顕著です。

OWLはさまざまなLLMバックエンドをサポートしていますが、機能はモデルのツール呼び出しおよびマルチモーダル機能に依存する場合があります。以下のスクリプトを使用して、異なるモデルで実行できます：

```bash
# Qwenモデルで実行
python examples/run_qwen_zh.py

# Deepseekモデルで実行
python examples/run_deepseek_zh.py

# 他のOpenAI互換モデルで実行
python examples/run_openai_compatible_model.py

# Azure OpenAIで実行
python examples/run_azure_openai.py

# Ollamaで実行
python examples/run_ollama.py
```

LLM APIキーのみを必要とするシンプルなバージョンについては、最小限の例を試してみてください：

```bash
python examples/run_mini.py
```

`examples/run.py`スクリプトを変更して、独自のタスクでOWLエージェントを実行できます：

```python
# 独自のタスクを定義
task = "Task description here."

society = construct_society(question)
answer, chat_history, token_count = run_society(society)

print(f"\033[94mAnswer: {answer}\033[0m")
```

ファイルをアップロードする場合は、質問と一緒にファイルパスを提供するだけです：

```python
# ローカルファイルを使用したタスク（例：ファイルパス：`tmp/example.docx`）
task = "What is in the given DOCX file? Here is the file path: tmp/example.docx"

society = construct_society(question)
answer, chat_history, token_count = run_society(society)
print(f"\033[94mAnswer: {answer}\033[0m")
```

OWLは自動的にドキュメント関連のツールを呼び出してファイルを処理し、回答を抽出します。


### 例のタスク

以下のタスクをOWLで試してみてください：

- "Apple Inc.の最新の株価を調べる"
- "気候変動に関する最近のツイートの感情を分析する"
- "このPythonコードのデバッグを手伝ってください：[ここにコードを貼り付け]"
- "この研究論文の主要なポイントを要約してください：[論文のURL]"
- "このデータセットのデータビジュアライゼーションを作成してください：[データセットのパス]"

# 🧰 ツールキットと機能

## モデルコンテキストプロトコル（MCP）

OWLのMCP統合は、AIモデルがさまざまなツールやデータソースと相互作用するための標準化された方法を提供します：

MCPを使用する前に、まずNode.jsをインストールする必要があります。
### **Node.jsのインストール**
### Windows

公式インストーラーをダウンロード：[Node.js](https://nodejs.org/en)。

インストール中に「Add to PATH」オプションをチェックします。

### Linux
```bash
sudo apt update
sudo apt install nodejs npm -y
```
### Mac
```bash
brew install node
```

### **Playwright MCPサービスのインストール**
```bash
npm install -g @executeautomation/playwright-mcp-server
npx playwright install-deps
```

`examples/run_mcp.py`の包括的なMCP例を試して、これらの機能を実際に体験してください！

## 利用可能なツールキット

> **重要**：ツールキットを効果的に使用するには、強力なツール呼び出し機能を持つモデルが必要です。マルチモーダルツールキット（Web、画像、ビデオ）には、マルチモーダル理解機能を持つモデルも必要です。

OWLはさまざまなツールキットをサポートしており、スクリプト内の`tools`リストを変更してカスタマイズできます：

```python
# ツールキットの設定
tools = [
    *BrowserToolkit(headless=False).get_tools(),  # ブラウザ自動化
    *VideoAnalysisToolkit(model=models["video"]).get_tools(),
    *AudioAnalysisToolkit().get_tools(),  # OpenAIキーが必要
    *CodeExecutionToolkit(sandbox="subprocess").get_tools(),
    *ImageAnalysisToolkit(model=models["image"]).get_tools(),
    SearchToolkit().search_duckduckgo,
    SearchToolkit().search_google,  # 利用できない場合はコメントアウト
    SearchToolkit().search_wiki,
    SearchToolkit().search_bocha,
    SearchToolkit().search_baidu,
    *ExcelToolkit().get_tools(),
    *DocumentProcessingToolkit(model=models["document"]).get_tools(),
    *FileWriteToolkit(output_dir="./").get_tools(),
]
```

## 利用可能なツールキット

主要なツールキットには以下が含まれます：

### マルチモーダルツールキット（マルチモーダルモデル機能が必要）
- **BrowserToolkit**：ウェブインタラクションとナビゲーションのためのブラウザ自動化
- **VideoAnalysisToolkit**：ビデオ処理とコンテンツ分析
- **ImageAnalysisToolkit**：画像解析と解釈

### テキストベースのツールキット
- **AudioAnalysisToolkit**：音声処理（OpenAI APIが必要）
- **CodeExecutionToolkit**：Pythonコードの実行と評価
- **SearchToolkit**：ウェブ検索（Google、DuckDuckGo、Wikipedia）
- **DocumentProcessingToolkit**：ドキュメント解析（PDF、DOCXなど）

その他の専門ツールキット：ArxivToolkit、GitHubToolkit、GoogleMapsToolkit、MathToolkit、NetworkXToolkit、NotionToolkit、RedditToolkit、WeatherToolkitなど。完全なツールキットのリストについては、[CAMELツールキットドキュメント](https://docs.camel-ai.org/key_modules/tools.html#built-in-toolkits)を参照してください。

## カスタマイズ設定

利用可能なツールをカスタマイズするには：

```python
# 1. ツールキットをインポート
from camel.toolkits import BrowserToolkit, SearchToolkit, CodeExecutionToolkit

# 2. ツールリストを設定
tools = [
    *BrowserToolkit(headless=True).get_tools(),
    SearchToolkit().search_wiki,
    *CodeExecutionToolkit(sandbox="subprocess").get_tools(),
]

# 3. アシスタントエージェントに渡す
assistant_agent_kwargs = {"model": models["assistant"], "tools": tools}
```

必要なツールキットのみを選択することで、パフォーマンスを最適化し、リソース使用量を削減できます。

# 🌐 ウェブインターフェース

<div align="center" style="background-color: #f0f7ff; padding: 15px; border-radius: 10px; border: 2px solid #1e88e5; margin: 20px 0;">
  <h3 style="color: #1e88e5; margin: 0;">
    🚀 強化されたウェブインターフェースが利用可能になりました！
  </h3>
  <p style="margin: 10px 0;">
    最新のアップデートでシステムの安定性とパフォーマンスが向上しました。
    使いやすいインターフェースを通じて、OWLの力を探索し始めましょう！
  </p>
</div>

## ウェブUIの起動

```bash
# 中国語版を起動
python owl/webapp_zh.py

# 英語版を起動
python owl/webapp.py

# 日本語版を起動
python owl/webapp_jp.py
```

## 機能

- **簡単なモデル選択**：異なるモデル（OpenAI、Qwen、DeepSeekなど）を選択
- **環境変数管理**：UIから直接APIキーやその他の設定を構成
- **インタラクティブなチャットインターフェース**：使いやすいインターフェースを通じてOWLエージェントと対話
- **タスク履歴**：対話の履歴と結果を表示

ウェブインターフェースはGradioを使用して構築されており、ローカルマシン上で実行されます。設定したモデルAPI呼び出しに必要なデータ以外は外部サーバーに送信されません。

# 🧪 実験

OWLのGAIAベンチマークスコア58.18を再現するには：

1. `gaia58.18`ブランチに切り替え：
   ```bash
   git checkout gaia58.18
   ```

2. 評価スクリプトを実行：
   ```bash
   python run_gaia_roleplaying.py
   ```

これにより、GAIAベンチマークでトップランクのパフォーマンスを達成したのと同じ構成が実行されます。

# ⏱️ 将来の計画

私たちはOWLの改善に継続的に取り組んでいます。以下は私たちのロードマップです：

- [ ] 現実のタスクにおけるマルチエージェント協力の探求と洞察を詳述する技術ブログ記事を書く
- [ ] 特定の分野のタスクに対応する専門ツールを追加してツールキットエコシステムを強化
- [ ] より高度なエージェント相互作用パターンと通信プロトコルを開発
- [ ] 複雑な多段階推論タスクのパフォーマンスを向上

# 📄 ライセンス

ソースコードはApache 2.0ライセンスの下でライセンスされています。

# 🖊️ 引用

このリポジトリが役立つと思われる場合は、以下を引用してください：


```
@misc{owl2025,
  title        = {OWL: Optimized Workforce Learning for General Multi-Agent Assistance in Real-World Task Automation},
  author       = {{CAMEL-AI.org}},
  howpublished = {\url{https://github.com/camel-ai/owl}},
  note         = {Accessed: 2025-03-07},
  year         = {2025}
}
```

# 🤝 貢献

私たちはコミュニティからの貢献を歓迎します！以下は、どのように支援できるかです：

1. [貢献ガイドライン](https://github.com/camel-ai/camel/blob/master/CONTRIBUTING.md)を読む
2. [オープンな問題](https://github.com/camel-ai/camel/issues)を確認するか、新しい問題を作成する
3. 改善点を含むプルリクエストを提出する

**現在貢献を受け付けている問題：**
- [#1915](https://github.com/camel-ai/camel/issues/1915)
- [#2190](https://github.com/camel-ai/camel/issues/2190)
- [#2165](https://github.com/camel-ai/camel/issues/2165)
- [#2121](https://github.com/camel-ai/camel/issues/2121)
- [#1908](https://github.com/camel-ai/camel/issues/1908)
- [#1538](https://github.com/camel-ai/camel/issues/1538)
- [#1481](https://github.com/camel-ai/camel/issues/1481)


問題を引き受けるには、興味を示すコメントを残すだけです。

# 🔥 コミュニティ
エージェントのスケーリング法則を見つけるための限界を押し広げるために、私たちと一緒に参加してください（[*Discord*](https://discord.camel-ai.org/)または[*WeChat*](https://ghli.org/camel/wechat.png)）。

さらなる議論に参加してください！
<!-- ![](./assets/community.png) -->
![](./assets/community.jpeg)

# ❓ FAQ

**Q: サンプルスクリプトを起動した後、なぜローカルでChromeが実行されていないのですか？**

A: OWLがタスクを非ブラウザツール（検索やコード実行など）を使用して完了できると判断した場合、ブラウザは起動しません。ブラウザベースのインタラクションが必要と判断された場合にのみ、ブラウザウィンドウが表示されます。

**Q: どのPythonバージョンを使用すべきですか？**

A: OWLはPython 3.10、3.11、および3.12をサポートしています。

**Q: プロジェクトにどのように貢献できますか？**

A: 参加方法の詳細については、[貢献](#-貢献)セクションを参照してください。コードの改善からドキュメントの更新まで、あらゆる種類の貢献を歓迎します。

# 📚 CAMEL依存関係の探索

OWLは[CAMEL](https://github.com/camel-ai/camel)フレームワークの上に構築されています。以下は、CAMELのソースコードを探索し、OWLとの連携方法を理解する方法です：

## CAMELソースコードへのアクセス

```bash
# CAMELリポジトリをクローン
git clone https://github.com/camel-ai/camel.git
cd camel
```

# ⭐ Star History

[![Star History Chart](https://api.star-history.com/svg?repos=camel-ai/owl&type=Date)](https://star-history.com/#camel-ai/owl&Date)



[docs-image]: https://img.shields.io/badge/Documentation-EB3ECC
[docs-url]: https://camel-ai.github.io/camel/index.html
[star-image]: https://img.shields.io/github/stars/camel-ai/owl?label=stars&logo=github&color=brightgreen
[star-url]: https://github.com/camel-ai/owl/stargazers
[package-license-image]: https://img.shields.io/badge/License-Apache_2.0-blue.svg
[package-license-url]: https://github.com/camel-ai/owl/blob/main/licenses/LICENSE

[colab-url]: https://colab.research.google.com/drive/1AzP33O8rnMW__7ocWJhVBXjKziJXPtim?usp=sharing
[colab-image]: https://colab.research.google.com/assets/colab-badge.svg
[huggingface-url]: https://huggingface.co/camel-ai
[huggingface-image]: https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-CAMEL--AI-ffc107?color=ffc107&logoColor=white
[discord-url]: https://discord.camel-ai.org/
[discord-image]: https://img.shields.io/discord/1082486657678311454?logo=discord&labelColor=%20%235462eb&logoColor=%20%23f5f5f5&color=%20%235462eb
[wechat-url]: https://ghli.org/camel/wechat.png
[wechat-image]: https://img.shields.io/badge/WeChat-CamelAIOrg-brightgreen?logo=wechat&logoColor=white
[x-url]: https://x.com/CamelAIOrg
[x-image]: https://img.shields.io/twitter/follow/CamelAIOrg?style=social
[twitter-image]: https://img.shields.io/twitter/follow/CamelAIOrg?style=social&color=brightgreen&logo=twitter
[reddit-url]: https://www.reddit.com/r/CamelAI/
[reddit-image]: https://img.shields.io/reddit/subreddit-subscribers/CamelAI?style=plastic&logo=reddit&label=r%2FCAMEL&labelColor=white
[ambassador-url]: https://www.camel-ai.org/community
[owl-url]: ./assets/qr_code.jpg
[owl-image]: https://img.shields.io/badge/WeChat-OWLProject-brightgreen?logo=wechat&logoColor=white
