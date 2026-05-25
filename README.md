# llm-native-engineering-samples

Practical examples of AI Agent, RAG, MCP, and LLM workflow automation for
real-world engineering teams.

実務に近い制約のなかで、AI Agent / RAG / MCP / LLM ワークフローを**設計・実装できること**を示す小さなサンプル集。
巨大な1本より、筋の通った小さなサンプルを積み上げる方針。各サンプルは「動く + READMEで意図と限界が伝わる」を最低ラインとする。

## Samples

| # | Sample | What it shows | Stack |
|---|--------|---------------|-------|
| 01 | [RAG Helpdesk Agent](01-rag-helpdesk-agent/) | 根拠付きRAG・拒否（ハルシネーション防止）・オフラインevals・検索層の差し替え設計 | Python (依存ゼロ) + OpenAI/Anthropic 任意 |

### Planned

- 02 — GitHub Issue Triage Agent（分類・優先度・関連ファイル提示 / tool calling）
- 03 — MCP Server 集（LLMが安全に外部ツールを呼ぶ境界設計）
- 04 — PR Review Assistant（仕様逸脱・テスト不足・セキュリティ）
- 05 — AI Workflow Orchestrator（要件→仕様→分解→実装計画→テスト生成→PR説明）

## Principles

- **動く証拠 > 主張** — 各サンプルは実行可能で、評価（evals）が付く。
- **限界を書く** — README に Failure modes / Security / Evaluation を必ず含める。
- **秘密情報を持たない** — APIキーは環境変数のみ。オフライン経路は依存ゼロで CI が回る。

## License

MIT — see [LICENSE](LICENSE).
