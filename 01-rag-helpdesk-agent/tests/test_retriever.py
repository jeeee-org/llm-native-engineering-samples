import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag_helpdesk.chunking import load_corpus  # noqa: E402
from rag_helpdesk.gate import DEFAULT_MIN_SCORE  # noqa: E402
from rag_helpdesk.retriever import BM25Retriever  # noqa: E402
from rag_helpdesk.tokenizer import tokenize  # noqa: E402


class TokenizerTest(unittest.TestCase):
    def test_ascii_words_kept_whole(self):
        self.assertIn("api", tokenize("API key"))
        self.assertIn("key", tokenize("API key"))

    def test_cjk_expanded_to_bigrams(self):
        tokens = tokenize("有給休暇")
        self.assertIn("有給", tokens)
        self.assertIn("給休", tokens)
        self.assertIn("休暇", tokens)


class RetrieverTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.retriever = BM25Retriever(load_corpus(ROOT / "corpus"))

    def test_in_scope_question_ranks_expected_source_first(self):
        hits = self.retriever.retrieve("有給休暇は何日前までに申請しますか", k=4)
        self.assertTrue(hits)
        self.assertEqual(hits[0].chunk.source, "employment-rules.md")

    def test_security_question_ranks_security_doc_first(self):
        hits = self.retriever.retrieve("APIキーはどこで管理しますか", k=4)
        self.assertEqual(hits[0].chunk.source, "security-policy.md")

    def test_out_of_scope_question_scores_below_threshold(self):
        hits = self.retriever.retrieve("明日の東京の天気", k=4)
        top = hits[0].score if hits else 0.0
        self.assertLess(top, DEFAULT_MIN_SCORE)

    def test_empty_corpus_rejected(self):
        with self.assertRaises(ValueError):
            BM25Retriever([])


if __name__ == "__main__":
    unittest.main()
