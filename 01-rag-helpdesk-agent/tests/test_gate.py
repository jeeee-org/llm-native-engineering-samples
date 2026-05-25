import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from rag_helpdesk.answer import REFUSAL, compose  # noqa: E402
from rag_helpdesk.chunking import Chunk  # noqa: E402
from rag_helpdesk.gate import assess  # noqa: E402
from rag_helpdesk.retriever import Hit  # noqa: E402


def _hit(score: float) -> Hit:
    return Hit(Chunk(id="x::0", source="x.md", heading="H", text="body"), score)


class GateTest(unittest.TestCase):
    def test_no_hits_is_unanswerable(self):
        self.assertFalse(assess([]).answerable)

    def test_below_threshold_is_unanswerable(self):
        self.assertFalse(assess([_hit(1.0)], min_score=3.0).answerable)

    def test_above_threshold_is_answerable(self):
        self.assertTrue(assess([_hit(9.0)], min_score=3.0).answerable)


class ComposeTest(unittest.TestCase):
    def test_refuses_when_gate_blocks(self):
        gate = assess([], min_score=3.0)
        answer = compose("q", [], gate)
        self.assertTrue(answer.refused)
        self.assertEqual(answer.text, REFUSAL)
        self.assertEqual(answer.citations, [])

    def test_extractive_answer_includes_citation(self):
        hits = [_hit(9.0)]
        gate = assess(hits, min_score=3.0)
        answer = compose("q", hits, gate, provider="extractive")
        self.assertFalse(answer.refused)
        self.assertIn("x.md#H", answer.text)
        self.assertEqual(answer.citations, ["x.md#H"])


if __name__ == "__main__":
    unittest.main()
