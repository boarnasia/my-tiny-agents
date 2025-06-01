# 🧠 2. Concept: Code Agent with MCP – TinyAgents 拡張実験

## 🔍 概要

この章では、Julien Chaumond 氏の Tiny Agents のアイデアをもとに、Albert Villanova 氏が提唱した **「Code Agent」** のコンセプトと実装例を解説します。

元記事：[TinyAgents: A Minimal Experiment with Code Agents and MCP Tools](https://huggingface.co/blog/albertvillanova/tiny-agents)

---

## 💡 なぜ Code Agent か？

従来の **Tool-calling Agent** は、ユーザーの指示を受けて単一のツールを呼び出す仕組みです。  
ただしこの方法では、「複数のツールを組み合わせる」「ループや条件分岐を含む」ような **構成的（compositional）思考** を要するタスクが苦手です。

### 👉 解決策：エージェント自身に**コードを書かせて実行させる**

---

## 🔁 Tool Agent vs Code Agent（比較）

| 特性 | Tool-calling Agent | Code Agent |
|------|--------------------|------------|
| 呼び出し方 | 単一のツールを呼び出す | 複数のツール呼び出しをコードに埋め込む |
| 柔軟性 | 低（固定的な指示のみ） | 高（条件分岐・ループ対応） |
| LLM呼び出し回数 | 多くなりがち | 最小限（1回のコード生成で済む） |
| ワークフローの表現力 | 限定的 | 構成的・複合的処理が可能 |

---

## 🧪 実験例：天気警報を3州で取得せよ

### 🧰 Tool Agent の出力（不十分）

```text
「New York の警報だけ」取得して終了。
California と Alaska は無視される。
````

→ なぜか？：1つの tool call のみ処理され、複雑な構成を実行できなかった。

---

### 💻 Code Agent の出力（理想的）

```python
# Get weather alerts for NY, CA, and AK
ny_alerts = get_alerts("NY")
ca_alerts = get_alerts("CA")
ak_alerts = get_alerts("AK")

# Print results
print(ny_alerts)
print(ca_alerts)
print(ak_alerts)
```

→ LLM がこのコードを1ステップで生成 → 実行 → 結果を整形して出力

---

## 🧰 技術的構成

* **MCP Tools**：`get_alerts()` などのツールが Python 関数形式で提供されている
* **LLM**：Pythonコードを生成する（例: Claude, GPT-4, Qwen）
* **Code Executor**：生成されたコードを安全に実行して結果を返す

---

## ✨ 今後の展望

* 🛠 Code Agent に**安全なコード実行環境**を追加
* 🧪 LLM に**より長期的・マルチステップの推論**を担わせる
* 🔗 ツールとコードの**ハイブリッド運用**も視野に入れる

---

## 📎 参考リンク

* ブログ記事：[https://huggingface.co/blog/albertvillanova/tiny-agents](https://huggingface.co/blog/albertvillanova/tiny-agents)
* MCP公式：[https://modelcontextprotocol.io](https://modelcontextprotocol.io)
* TinyAgents GitHub: [https://github.com/albertvillanova/tinyagents](https://github.com/albertvillanova/tinyagents)

---

## 📌 要点まとめ

> **Code Agent = LLM + Python実行環境 + MCP Tools**
> 少ないLLM呼び出しで、構成的な複雑タスクを柔軟に処理できる次世代エージェントの形