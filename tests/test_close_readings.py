"""V3.1 public close-reading regression: provenance, copyright, IDs and source links."""
from __future__ import annotations

import copy
import json
import sys
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts" / "build"))
from catalog_core import read_catalog
from close_readings import outputs, validate_reading

class CloseReadingTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.doc=json.loads((ROOT/"catalog/close-readings/p148.json").read_text(encoding="utf-8"))
        _,cls.records,cls.tracks,_=read_catalog(ROOT)
        cls.paper_ids={x["paper"]["id"] for x in cls.records}
        cls.track_ids={x["id"] for x in cls.tracks}

    def test_all_source_units_and_legal_boundary(self):
        counts=validate_reading(self.doc,self.paper_ids,self.track_ids)
        self.assertEqual(counts,{"paragraphs":101,"figures":6,"tables":16})
        self.assertEqual(len(self.doc["sections"]),18)
        self.assertEqual(self.doc["paperId"],"p148")
        self.assertFalse(self.doc["copyright"]["originalFullTextRepublished"])
        self.assertFalse(self.doc["copyright"]["fullTranslationRepublished"])
        self.assertFalse(self.doc["copyright"]["figuresMirrored"])
        serialized=json.dumps(self.doc)
        for unsafe in ("data:image/", "base64,", "<script", "<iframe"):
            self.assertNotIn(unsafe, serialized.lower())
        units=[u for s in self.doc["sections"] for u in s["units"]]
        self.assertEqual(len(units),123)
        self.assertEqual(len({u["id"] for u in units}),123)
        self.assertTrue(all(u["sourceUrl"].startswith("https://arxiv.org/pdf/2611.08373v1#page=") for u in units))

    def test_builder_returns_lazy_shards(self):
        files,index=outputs(ROOT,self.records,self.tracks)
        self.assertEqual(len(index),1)
        self.assertEqual(index[0]["units"],123)
        self.assertEqual(index[0]["href"],"close-reading/p148/")
        self.assertIn("data/close-readings/p148.json",files)
        self.assertIn("data/close-readings/index.json",files)
        self.assertNotIn("base64,",files["data/close-readings/p148.json"])

    def test_disallowed_full_republishing_is_blocked(self):
        changed=copy.deepcopy(self.doc)
        changed["copyright"]["originalFullTextRepublished"]=True
        with self.assertRaisesRegex(ValueError,"unlicensed redistribution"):
            validate_reading(changed,self.paper_ids,self.track_ids)

    def test_wrong_pdf_page_is_blocked(self):
        changed=copy.deepcopy(self.doc)
        changed["sections"][0]["units"][0]["pdfPage"]=99
        with self.assertRaisesRegex(ValueError,"PDF page location"):
            validate_reading(changed,self.paper_ids,self.track_ids)

    def test_unknown_result_tracks_are_blocked(self):
        changed=copy.deepcopy(self.doc)
        changed["sections"][0]["units"][0]["evidenceTracks"]=["missing-vla-track"]
        with self.assertRaisesRegex(ValueError,"unknown Benchmark track"):
            validate_reading(changed,self.paper_ids,self.track_ids)

    def test_injected_markup_is_blocked(self):
        changed=copy.deepcopy(self.doc)
        changed["sections"][0]["units"][0]["criticalNote"]="<script>alert(1)</script>"
        with self.assertRaisesRegex(ValueError,"untrusted markup"):
            validate_reading(changed,self.paper_ids,self.track_ids)

if __name__=="__main__":
    unittest.main()
