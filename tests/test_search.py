import pytest

from helpdesk.config import POLICIES_DIR
from helpdesk.search import Index, chunk_markdown, search_policies, tokenize


# ---------- chunking ----------
def test_every_policy_file_is_split_into_nonempty_chunks():
    files = sorted(POLICIES_DIR.glob("*.md"))
    assert len(files) == 3
    for path in files:
        chunks = chunk_markdown(path)
        assert chunks, path
        for c in chunks:
            assert c["heading"] and c["text"].strip()
            assert c["source"] == path.name


def test_chunk_keeps_table_with_its_heading():
    chunks = chunk_markdown(POLICIES_DIR / "cancellations.md")
    cancelling = next(c for c in chunks if c["heading"] == "Cancelling a booking")
    assert "48 hours or more" in cancelling["text"]
    assert "100%" in cancelling["text"]


def test_chunking_a_custom_folder(tmp_path):
    (tmp_path / "x.md").write_text("# Title\n\n## First\nalpha text\n\n## Second\nbeta text\n")
    index = Index(tmp_path)
    assert [c["heading"] for c in index.chunks] == ["First", "Second"]
    assert index.search("beta")[0]["heading"] == "Second"


# ---------- normalisation ----------
def test_ebike_and_electric_bikes_meet_in_the_middle():
    assert tokenize("e-bike") == tokenize("Electric bikes")


def test_stopwords_are_dropped_and_plurals_stemmed():
    assert tokenize("What are the opening hours?") == ["open", "hour"]


# ---------- retrieval quality ----------
@pytest.mark.parametrize(
    "query, heading",
    [
        ("What time do you open on Saturday?", "When are you open?"),
        ("How much is an e-bike for a whole day?", "Bike rental"),
        ("Can my 14-year-old rent an e-bike?", "Are there age limits?"),
        ("I want to cancel booking CW-1002. How much will I get back?", "Cancelling a booking"),
        ("What happens if there is a storm warning?", "Bad weather"),
        ("Can I change my booking dates?", "Changing a booking"),
        ("Do I need a helmet?", "Do I have to wear a helmet?"),
        ("My bike was stolen", "What if the bike is stolen or lost?"),
        ("Is there a child seat and what does it cost?", "Add-ons"),
    ],
)
def test_right_section_is_ranked_first(query, heading):
    results = search_policies(query)["results"]
    assert results[0]["heading"] == heading


def test_voucher_refund_question_finds_how_money_comes_back():
    headings = [r["heading"] for r in search_policies("refund to voucher or card")["results"]]
    assert "How the money comes back" in headings[:2]


# ---------- no answer / bad input ----------
@pytest.mark.parametrize("query", ["What is the capital of Australia?", "", "   ", "???", None])
def test_unrelated_or_empty_queries_return_no_results_and_do_not_raise(query):
    r = search_policies(query)
    assert r["results"] == []
    assert "message" in r


def test_top_k_is_respected_and_clamped():
    assert len(search_policies("bike", top_k=1)["results"]) == 1
    assert len(search_policies("bike", top_k=999)["results"]) <= 5


def test_nonsense_top_k_does_not_raise():
    r = search_policies("bike", top_k="oops")
    assert r["results"] == [] and "failed" in r["message"].lower()