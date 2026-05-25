# 01 — RAG Helpdesk Agent

社内ドキュメントを根拠付きで検索回答する、最小構成の RAG ヘルプデスク。
A minimal, dependency-free Retrieval-Augmented Generation helpdesk over a fictional
company's internal docs (**Acme AI Corp**). Answers cite their sources and the agent
**refuses** ("わかりません") when the docs don't cover the question.

```console
$ python -m rag_helpdesk.cli ask "有給休暇は何日前までに申請しますか？"
有給休暇は、取得を希望する日の **3営業日前まで** に勤怠システムから申請する。…
[1] employment-rules.md#有給休暇の申請

$ python -m rag_helpdesk.cli ask "明日の天気は？"
わかりません。提供された社内ドキュメントに該当する記述が見つかりませんでした。
```

## What this demonstrates

RAG案件で実際に問われる「**作れる/設計できる証拠**」を、小さく筋の通った形で示す:

- **Grounded answers with citations** — すべての回答は取得チャンクに紐づき、`file#heading` で出典を明示。
- **Refusal over hallucination** — 取得スコアが閾値未満なら、もっともらしい嘘を返さず明示的に拒否。
- **Evals that run in CI without secrets** — 正答/拒否を検証する評価スイートがオフラインで回る（`evals/`）。
- **Swappable retrieval seam** — 検索層は小さなインターフェイスに隔離し、BM25 → 埋め込み+Vector DB へ差し替え可能。
- **Provider abstraction** — 回答生成は extractive（既定・APIキー不要）/ OpenAI / Anthropic を切替。
- **Security-aware** — APIキーは環境変数のみ、コーパスに秘密情報を置かない、Anthropic 側は prompt caching を使用。

> 正直な範囲: これは「動く設計サンプル」であり、本番投入可能な製品ではない。限界は [Failure modes](#failure-modes) に明記。

## Architecture

```
question
   │  tokenize() … CJK を文字バイグラム化（形態素解析器に非依存）
   ▼
BM25Retriever.retrieve(query, k)   ← in-memory Okapi BM25
   │  top-k Hits (chunk + score)
   ▼
gate.assess(hits)                  ── top score < 閾値 ──►  REFUSAL「わかりません」
   │  answerable
   ▼
answer.compose(question, hits)
   ├─ extractive  (default, offline, deterministic)
   ├─ openai      (lazy import)
   └─ anthropic   (lazy import, prompt caching)
   │
   ▼
answer text + citations [1] [2] …
```

- `rag_helpdesk/chunking.py` — Markdown を見出し単位のチャンクに分割（`Chunk.citation = file#heading`）。
- `rag_helpdesk/tokenizer.py` — ASCII は語、CJK は文字バイグラム。純ひらがなバイグラム（助詞・活用語尾）はノイズとして除外。
- `rag_helpdesk/retriever.py` — 依存ゼロの Okapi BM25。`retrieve(query, k) -> [Hit]` だけが外部契約。
- `rag_helpdesk/gate.py` — 「答えない」判断（取得信頼度の閾値）。
- `rag_helpdesk/answer.py` — 引用必須・コンテキスト限定で回答を生成、または拒否。
- `rag_helpdesk/cli.py` — エントリポイント。

## Security considerations

- **Secrets**: APIキーは環境変数（`OPENAI_API_KEY` / `ANTHROPIC_API_KEY`）からのみ取得。リポジトリやコーパスに秘密情報を置かない。
- **Grounding**: モデルには「コンテキスト外は答えない」と明示し、拒否文を固定。プロンプトインジェクション耐性は限定的（下記）。
- **Prompt caching**: Anthropic 呼び出しは静的システムプロンプトを `cache_control` でキャッシュ対象にし、コスト/レイテンシを抑制。
- **PII**: コーパスは完全な架空データ。実データを扱う場合はアクセス制御・監査・マスキングが別途必要。

## Failure modes

正直に、既知の弱点と対処方針:

- **Lexical retrieval の限界** — BM25 は語の一致に依存し、言い換え/同義語に弱い。→ 埋め込み検索やハイブリッド（BM25 + ベクトル）へ。
- **閾値はコーパス依存** — `DEFAULT_MIN_SCORE` は同梱コーパスで校正済み。別コーパスでは再校正が必要。→ 正規化スコアやクロスエンコーダで校正不要化。
- **バイグラム除外の副作用** — 純ひらがなの内容語（例「おすすめ」）は検索に効かない。本コーパスでは内容語が漢字中心のため許容。形態素解析器導入で解消可。
- **プロンプトインジェクション** — コーパス本文に悪意ある指示があると LLM 生成経路で従う可能性。→ 入力サニタイズ・出力検証・権限分離。
- **拒否の取りこぼし/過剰拒否** — 閾値運用なので境界事例は誤る。→ evals 拡充と人手レビュー。

## Evaluation strategy

`evals/cases.json` にラベル付き質問（in-scope は期待出典、out-of-scope は拒否）を定義し、`evals/run_evals.py` で検証する。
- in-scope: 回答可能かつ期待した出典が1位で取得される。
- out-of-scope: **拒否**される（ハルシネーション防止）。
- APIキー不要・決定的なので **CI で毎PR実行**できる（`.github/workflows/ci.yml`）。

```console
$ python evals/run_evals.py
…
12 passed, 0 failed
```

## How to run

Python 3.12+。依存はオフライン経路では**ゼロ**。

```console
# 質問する（既定: extractive = APIキー不要）
python -m rag_helpdesk.cli ask "経費精算の締め日はいつ？"

# LLM で生成（要 SDK & APIキー）
pip install openai anthropic   # or: pip install -r requirements-optional.txt
export ANTHROPIC_API_KEY=...   # or OPENAI_API_KEY
python -m rag_helpdesk.cli ask "副業はできますか？" --provider anthropic

# 評価とテスト
python evals/run_evals.py
python -m unittest discover -s tests -t .
```

## Future improvements

- 埋め込み検索（OpenAI/Voyage）＋ pgvector / sqlite-vec への `Retriever` 差し替え（インターフェイスは既に分離済み）。
- ハイブリッド検索（BM25 + ベクトル）とリランカー。
- 回答の faithfulness を測る LLM-as-judge eval の追加。
- Slack ボット化（`#helpdesk` 連携）と会話履歴。
- インデックスの永続化と増分更新。
