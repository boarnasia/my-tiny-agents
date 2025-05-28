# My Tiny Agents 🤖

AIコーディングのみで実装した、LLMエージェントとMCP（Model Context Protocol）サーバーを組み合わせたミニマリストなエージェントです。

参考: [TinyAgents: A Minimal Experiment with Code Agents and MCP Tools](https://huggingface.co/blog/albertvillanova/tiny-agents)

## クイックスタート
```bash
# 依存関係のインストール
make install

# エージェントの起動（デフォルトで全サーバーに接続）
make run-agent
```

## 含まれるMCPサーバー

| サーバー | 機能 | 主なツール |
|---------|------|-----------|
| **GitHub Trends** | GitHubのトレンドリポジトリ取得 | `fetch_github_trends` |
| **Command Executor** | システムコマンド実行・ファイル操作 | `execute_command`, `read_file`, `list_directory` |
| **Web Search** | Web検索・ニュース検索 | `search_web`, `search_news` |
| **Python Executor** | Pythonコード実行・分析 | `execute_python`, `analyze_code` |
| **Task Manager** | タスク管理 | `add_task`, `list_tasks`, `complete_task` |

## 💡 使用例

```
Query: フィボナッチ数列の最初の20個を計算して、fibonacci.txtに保存して

📋 Action Plan:
1. Pythonでフィボナッチ数列を計算
2. 結果をfibonacci.txtに保存
3. ファイルの内容を確認
```

その他の例：
- `GitHubのPythonトレンドを取得して、上位5つをtrends.txtに保存して`
- `現在のディレクトリのPythonファイルを全て分析して`
- `"READMEを更新"という高優先度タスクを作成して`

## 設定

### 環境変数

使用するLLMに応じて設定：
- OpenAI: `export OPENAI_API_KEY="your-api-key"`
- Anthropic: `export ANTHROPIC_API_KEY="your-api-key"`
- Google: `export GEMINI_API_KEY="your-api-key"`

### 推奨モデル

- `openai/gpt-4.1` (デフォルト)
- `anthropic/claude-3-5-sonnet-20241022`
- `gemini/gemini-2.0-flash-exp`

## 開発

```bash
# 開発モードでインストール
make dev-install

# 新しいMCPサーバーの作成
# servers/ディレクトリに新しい.pyファイルを作成し、FastMCPを使用

# クリーンアップ
make clean
```

## ライセンス
MITライセンス
