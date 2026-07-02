"""Unit tests for the pure filtering/scoring logic in scraper/scrape.py.

No network access — these exercise parse_watchlist, kw_match, the
geography/language guards, extract_salary, passes_filters/score,
posting_dedup_key, compute_chips, and the shared strip_html helper.
Manual live-testing against real ATS APIs remains the norm for adapters
(see CONTRIBUTING.md); this suite covers the logic that doesn't need
the network to be right.

Run from the repo root: python3 -m unittest discover tests

All companies/roles/salaries/locations in fixtures are fictional.
"""

import sys
import tempfile
import unittest
from pathlib import Path

# Same sys.path pattern scrape.py itself uses, so tests run without
# installing the package or relying on a conftest.py.
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scraper"))

import scrape
from sources import strip_html


# ─── parse_watchlist ────────────────────────────────────────────

FIXTURE_WATCHLIST = """\
# Fixture watchlist (fictional, tests only)

## Companies

### Tier one (priority)
- initech (greenhouse)
- umbrella-corp

### Tier two
- hooli (lever)

## Feeds

- remotive (design)
- fakefeed (widgets)

## Title must match one of

- design

## Strong titles

- product designer
- ui

## Title excludes

- engineer
- recruiter

## Department excludes

- game design

## Boost keywords

- fintech
- design system

## Company tier boosts

- tier one: 5
- tier two: 2

## Score penalties

- junior: 2
- intern: 4

## Salary floor

- 130,000

## Company aliases

- initech labs: initech
- umbrella subsidiary: umbrella-corp

## Locations

- remote
- austin
"""


class ParseWatchlistTests(unittest.TestCase):
    def setUp(self):
        fh = tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        )
        fh.write(FIXTURE_WATCHLIST)
        fh.close()
        self.path = Path(fh.name)
        self.addCleanup(self.path.unlink)
        self.criteria = scrape.parse_watchlist(self.path)

    def test_companies_and_pinned_source(self):
        self.assertEqual(
            self.criteria["companies"],
            [("initech", "greenhouse"), ("umbrella-corp", None), ("hooli", "lever")],
        )

    def test_feeds(self):
        self.assertEqual(
            self.criteria["feeds"],
            [("remotive", "design"), ("fakefeed", "widgets")],
        )

    def test_company_tiers(self):
        self.assertEqual(
            self.criteria["company_tiers"],
            {
                "initech": "tier one (priority)",
                "umbrella-corp": "tier one (priority)",
                "hooli": "tier two",
            },
        )

    def test_tier_boosts(self):
        self.assertEqual(
            self.criteria["tier_boosts"],
            [("tier one", 5), ("tier two", 2)],
        )

    def test_score_penalties_reuses_tier_boost_shape(self):
        self.assertEqual(
            self.criteria["score_penalties"],
            [("junior", 2), ("intern", 4)],
        )

    def test_salary_floor_strips_commas(self):
        self.assertEqual(self.criteria["salary_floor"], 130000)

    def test_simple_sections_lowered(self):
        self.assertEqual(self.criteria["title_includes"], ["design"])
        self.assertEqual(self.criteria["strong_titles"], ["product designer", "ui"])
        self.assertEqual(self.criteria["title_excludes"], ["engineer", "recruiter"])
        self.assertEqual(self.criteria["department_excludes"], ["game design"])
        self.assertEqual(
            self.criteria["boost_keywords"], ["fintech", "design system"]
        )
        self.assertEqual(self.criteria["locations"], ["remote", "austin"])

    def test_company_aliases(self):
        self.assertEqual(
            self.criteria["company_aliases"],
            {"initech labs": "initech", "umbrella subsidiary": "umbrella-corp"},
        )

    def test_missing_salary_floor_is_none(self):
        path = Path(tempfile.mktemp(suffix=".md"))
        path.write_text("## Companies\n- foo\n")
        self.addCleanup(path.unlink)
        criteria = scrape.parse_watchlist(path)
        self.assertIsNone(criteria["salary_floor"])

    def test_missing_company_aliases_is_empty_dict(self):
        path = Path(tempfile.mktemp(suffix=".md"))
        path.write_text("## Companies\n- foo\n")
        self.addCleanup(path.unlink)
        criteria = scrape.parse_watchlist(path)
        self.assertEqual(criteria["company_aliases"], {})


# ─── kw_match ────────────────────────────────────────────────────

class KwMatchTests(unittest.TestCase):
    def test_short_keyword_respects_word_boundary(self):
        # 'ui' must not match inside 'building' — that's the whole point
        # of the <=3-char word-boundary rule.
        self.assertFalse(scrape.kw_match("ui", "building modern apps"))
        self.assertFalse(scrape.kw_match("ux", "luxury goods team"))

    def test_short_keyword_matches_standalone(self):
        self.assertTrue(scrape.kw_match("ui", "ui designer"))
        self.assertTrue(scrape.kw_match("ui", "senior ui/ux designer"))

    def test_long_keyword_keeps_substring_semantics(self):
        # 'design' (>3 chars) should still match inside 'designer'.
        self.assertTrue(scrape.kw_match("design", "senior designer"))

    def test_long_keyword_no_match(self):
        self.assertFalse(scrape.kw_match("design", "software engineer"))


# ─── is_international ───────────────────────────────────────────

class IsInternationalTests(unittest.TestCase):
    """is_international expects pre-lowercased input, matching how
    passes_filters() calls it (location.lower() happens at the call site)."""

    def test_us_state_abbreviation_takes_precedence(self):
        # "Ontario, CA" is a real US-namesake trap — must NOT be flagged.
        self.assertFalse(scrape.is_international("ontario, ca"))

    def test_us_signal_word(self):
        self.assertFalse(scrape.is_international("remote, united states"))

    def test_unknown_location_fails_open(self):
        self.assertFalse(scrape.is_international(""))
        self.assertFalse(scrape.is_international("somewhere over the rainbow"))

    def test_foreign_only_is_dropped(self):
        self.assertTrue(scrape.is_international("dubai, uae"))
        self.assertTrue(scrape.is_international("toronto, ontario"))

    def test_foreign_with_us_option_survives(self):
        self.assertFalse(scrape.is_international("london; new york"))


# ─── is_non_english ──────────────────────────────────────────────

class IsNonEnglishTests(unittest.TestCase):
    def test_english_kept(self):
        text = (
            "We are looking for a designer to join our team and work "
            "with our clients on great products for your role."
        )
        self.assertFalse(scrape.is_non_english(text))

    def test_portuguese_dropped(self):
        text = (
            "Não temos certeza, mas você não precisa de experiência "
            "anterior para trabalhar conosco. Nós somos uma equipe incrível "
            "que oferece mais do que uma empresa comum."
        )
        self.assertTrue(scrape.is_non_english(text))

    def test_spanish_dropped(self):
        text = (
            "Usted no necesita experiencia previa para trabajar con nuestro "
            "equipo. Nuestro trabajo es sobre las mejores experiencias de "
            "los usuarios y las nuevas ideas."
        )
        self.assertTrue(scrape.is_non_english(text))

    def test_short_text_kept(self):
        self.assertFalse(scrape.is_non_english("Hi"))
        self.assertFalse(scrape.is_non_english(""))

    def test_ambiguous_mix_kept(self):
        # A couple of stray foreign hits shouldn't flip an otherwise
        # English posting — fail-open requires a real margin.
        text = "We are hiring a designer. Our team loves great work and your role matters a lot que."
        self.assertFalse(scrape.is_non_english(text))


# ─── extract_salary ──────────────────────────────────────────────

class ExtractSalaryTests(unittest.TestCase):
    def test_dollar_range_with_commas(self):
        comp = scrape.extract_salary("Pay: $120,000 - $150,000 per year")
        self.assertEqual(comp["min"], 120000.0)
        self.assertEqual(comp["max"], 150000.0)
        self.assertFalse(comp["hourly"])

    def test_k_shorthand_en_dash(self):
        comp = scrape.extract_salary("Compensation $120k–$150k")
        self.assertEqual(comp["min"], 120000.0)
        self.assertEqual(comp["max"], 150000.0)

    def test_usd_prefix(self):
        comp = scrape.extract_salary("Salary: USD 120,000 to USD 150,000")
        self.assertEqual(comp["min"], 120000.0)
        self.assertEqual(comp["max"], 150000.0)

    def test_hourly_rate(self):
        comp = scrape.extract_salary("Contract rate: $70/hr")
        self.assertTrue(comp["hourly"])
        self.assertEqual(comp["min"], comp["max"])
        self.assertEqual(comp["min"], 70.0)

    def test_no_match_returns_none(self):
        self.assertIsNone(scrape.extract_salary("Competitive salary, great benefits."))
        self.assertIsNone(scrape.extract_salary(""))
        self.assertIsNone(scrape.extract_salary(None))

    def test_tiny_amount_guard(self):
        # A bare sub-$1000 figure with no k/M/period qualifier isn't a
        # real comp mention (e.g. a gift card) — should be skipped.
        self.assertIsNone(scrape.extract_salary("Get a $5 gift card on day one."))

    def test_single_figure_min_equals_max(self):
        comp = scrape.extract_salary("Starting at $95,000 annually.")
        self.assertEqual(comp["min"], comp["max"])
        self.assertEqual(comp["min"], 95000.0)


# ─── passes_filters + score ──────────────────────────────────────

def _criteria(**overrides):
    base = {
        "title_includes": ["design"],
        "strong_titles": ["product designer"],
        "title_excludes": ["engineer"],
        "department_excludes": ["game design"],
        "boost_keywords": ["fintech", "design system"],
        "locations": ["remote"],
        "tier_boosts": [],
        "score_penalties": [],
    }
    base.update(overrides)
    return base


def _posting(**overrides):
    base = {
        "title": "Senior Product Designer",
        "company": "Initech",
        "location": "Remote",
        "remote": True,
        "department": "Design",
        "description": "Join our fintech team building a design system.",
        "source": "greenhouse",
        "tier": "",
    }
    base.update(overrides)
    return base


class PassesFiltersTests(unittest.TestCase):
    def test_strong_title_passes(self):
        self.assertTrue(scrape.passes_filters(_posting(), _criteria()))

    def test_title_exclude_wins(self):
        posting = _posting(title="Senior Design Engineer")
        self.assertFalse(scrape.passes_filters(posting, _criteria()))

    def test_department_exclude(self):
        posting = _posting(department="Game Design")
        self.assertFalse(scrape.passes_filters(posting, _criteria()))

    def test_no_title_match_fails(self):
        posting = _posting(title="Marketing Manager")
        self.assertFalse(scrape.passes_filters(posting, _criteria()))

    def test_international_without_target_location_fails(self):
        posting = _posting(location="Berlin, Germany", remote=True)
        self.assertFalse(scrape.passes_filters(posting, _criteria()))

    def test_international_with_explicit_target_location_survives(self):
        posting = _posting(location="Berlin, Germany", remote=False)
        criteria = _criteria(locations=["remote", "berlin"])
        self.assertTrue(scrape.passes_filters(posting, criteria))


class ScoreTests(unittest.TestCase):
    def test_strong_title_and_seniority_and_boosts(self):
        points = scrape.score(_posting(), _criteria())
        # +3 strong title, +2 "senior", +2 boost keywords (fintech,
        # design system both hit), +1 remote = 8
        self.assertEqual(points, 8)

    def test_generic_title_no_strong_bonus(self):
        posting = _posting(title="Designer", description="", remote=False)
        criteria = _criteria(strong_titles=["product designer"])
        points = scrape.score(posting, criteria)
        self.assertEqual(points, 0)

    def test_score_penalties_subtract_and_sum(self):
        posting = _posting(description="junior fintech design system, intern welcome")
        without_penalties = scrape.score(posting, _criteria(score_penalties=[]))
        with_penalties = scrape.score(
            posting, _criteria(score_penalties=[("junior", 2), ("intern", 4)])
        )
        # Same posting, only score_penalties differs -> both penalty
        # keywords hit ("junior" and "intern" both appear in the
        # description) and SUM (unlike tier_boosts, which takes the max).
        self.assertEqual(with_penalties, without_penalties - 6)

    def test_tier_boost_takes_max_not_sum(self):
        posting = _posting(tier="priority flagship")
        criteria = _criteria(
            tier_boosts=[("priority", 5), ("flagship", 3)]
        )
        with_boost = scrape.score(posting, criteria)
        without_boost = scrape.score(_posting(tier=""), criteria)
        # Only the larger matching tier_boost (5) applies, not 5+3=8.
        self.assertEqual(with_boost, without_boost + 5)

    def test_source_cost_penalty(self):
        canonical = scrape.score(_posting(source="greenhouse"), _criteria())
        aggregator = scrape.score(_posting(source="remoteok"), _criteria())
        self.assertEqual(canonical - aggregator, scrape.SOURCE_COST["remoteok"])


# ─── posting_dedup_key / _norm ────────────────────────────────────

class DedupKeyTests(unittest.TestCase):
    def setUp(self):
        # Aliases are module-level state (see scrape.set_company_aliases);
        # reset after each test so tests don't leak into each other.
        self.addCleanup(scrape.set_company_aliases, {})

    def test_noise_tokens_stripped(self):
        a = scrape._norm("Staff Designer")
        b = scrape._norm("Staff Designer (USA - Remote)")
        self.assertEqual(a, b)

    def test_parenthetical_content_kept(self):
        # Meaningful qualifiers inside parens should NOT be stripped —
        # only the noise tokens are removed from the token stream.
        norm = scrape._norm("Staff Designer (Developer Success)")
        self.assertIn("developer", norm)
        self.assertIn("success", norm)

    def test_key_combines_company_and_title(self):
        posting = {"company": "Initech", "title": "Product Designer"}
        key = scrape.posting_dedup_key(posting)
        self.assertEqual(key, "initech|product designer")

    def test_alias_folds_company_half(self):
        scrape.set_company_aliases({"initech labs": "initech"})
        p1 = {"company": "Initech Labs", "title": "Product Designer"}
        p2 = {"company": "Initech", "title": "Product Designer"}
        self.assertEqual(
            scrape.posting_dedup_key(p1), scrape.posting_dedup_key(p2)
        )

    def test_no_alias_configured_is_noop(self):
        p1 = {"company": "Initech Labs", "title": "Product Designer"}
        p2 = {"company": "Initech", "title": "Product Designer"}
        self.assertNotEqual(
            scrape.posting_dedup_key(p1), scrape.posting_dedup_key(p2)
        )


# ─── compute_chips ───────────────────────────────────────────────

class ComputeChipsTests(unittest.TestCase):
    def test_strong_title_chip_first(self):
        chips = scrape.compute_chips(_posting(), _criteria())
        self.assertEqual(chips[0], "product designer")

    def test_capped_at_five(self):
        posting = _posting(
            title="Senior Staff Product Designer",
            department="Design Systems",
            description=(
                "fintech design system full-time role building a design "
                "system for a fintech company"
            ),
        )
        criteria = _criteria(
            boost_keywords=["fintech", "design system", "full-time", "systems"]
        )
        chips = scrape.compute_chips(posting, criteria)
        self.assertLessEqual(len(chips), 5)


# ─── strip_html ──────────────────────────────────────────────────

class StripHtmlTests(unittest.TestCase):
    def test_tags_removed(self):
        self.assertEqual(strip_html("<p>Hello <b>world</b></p>"), "Hello world")

    def test_entities_decoded(self):
        self.assertEqual(strip_html("Design &amp; Build"), "Design & Build")
        self.assertEqual(strip_html("It&#39;s great"), "It's great")
        self.assertEqual(strip_html("A&nbsp;B"), "A B")

    def test_whitespace_collapsed(self):
        self.assertEqual(
            strip_html("<div>Line1</div>\n\n   <div>Line2</div>"),
            "Line1 Line2",
        )

    def test_empty_and_none(self):
        self.assertEqual(strip_html(""), "")
        self.assertEqual(strip_html(None), "")


if __name__ == "__main__":
    unittest.main()
