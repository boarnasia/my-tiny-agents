# 🧠 1. Concept: Tiny Agents - Minimal LLM Agents powered by MCP

## 🔍 概要

このプロジェクトの中核アイデアの一つは、[Hugging Face Blog: Tiny Agents](https://huggingface.co/blog/tiny-agents) に示されているミニマルなエージェント設計です。

**Tiny Agents** は、最新の LLM が持つ「ツール呼び出し（Function Calling）」機能と、[Model Context Protocol (MCP)](https://modelcontextprotocol.io) の標準仕様を活用して、**約50行のコードで実現できるシンプルなエージェントアーキテクチャ**を提示しています。

---

## 🛠 MCPとは？

Model Context Protocol (MCP) は、LLMが外部ツールを呼び出せるようにする**統一インターフェース**です。ツールは名前・説明・パラメータスキーマを備えた「関数」として記述され、MCP経由で LLM に公開されます。

```ts
const weatherTool = {
  type: "function",
  function: {
    name: "get_weather",
    description: "Get current temperature for a given location.",
    parameters: {
      type: "object",
      properties: {
        location: {
          type: "string",
          description: "e.g. Tokyo, Japan"
        }
      }
    }
  }
};
````

---

## 🧱 基本構造（Agentの構成）

Tiny Agent のアーキテクチャは以下の3層で構成されます：

1. **Inference Client**：LLM 呼び出し（例: Qwen, Claude, Gemini）
2. **MCP Client**：外部 MCP サーバーとの接続（複数可）
3. **Tool List**：利用可能なツールを集約し、LLMに提示

```ts
const agent = new Agent({
  provider: "nebius", // or other inference provider
  model: "Qwen/Qwen2.5-72B-Instruct",
  apiKey: process.env.HF_TOKEN,
  servers: [localFileSystemServer, playwrightBrowserServer],
});
```

---

## 🧪 実行例

### ✅ ファイル生成

> 「Hugging Faceコミュニティについての俳句を作り、それを 'hf.txt' としてDesktopに保存して」

→ → MCPのファイルサーバーツールがファイル操作を担当。

### ✅ Web検索

> 「Brave Searchで 'HF inference providers' を検索し、最初の3つのリンクを開いて」

→ → MCP経由で Playwright ツールがブラウザ操作を自動実行。

---

## ✨ 特徴と利点

| 項目        | 内容                                    |
| --------- | ------------------------------------- |
| 💡 シンプル   | フレームワークに依存せず、最小限の構成で実行可能              |
| 🔌 拡張可能   | MCPを通じて任意のツールを追加できる                   |
| 🔁 汎用性    | Python・JavaScript など複数の言語でクライアント実装が可能 |
| ⚡ パフォーマンス | コードベースが軽量なので高速デバッグ可能                  |
| 🔍 学習コスト低 | LangChainのような複雑な依存を排除                 |

---

## 🚀 このプロジェクトでの応用

* **第一歩として「シンプルなエージェント構築」から開始**
* MCPサーバー・ツールを必要に応じて拡張
* 徐々に複雑な意思決定（条件分岐、ループ）に対応する**Code Agent**へ進化

---

## 📎 参考リンク

* ブログ記事：[Tiny Agents: an MCP-powered agent in 50 lines of code](https://huggingface.co/blog/tiny-agents)
* GitHub実装：[huggingface/huggingface.js (mcp-client)](https://github.com/huggingface/huggingface.js/tree/main/packages/mcp-client)
* MCP公式：[https://modelcontextprotocol.io](https://modelcontextprotocol.io)
