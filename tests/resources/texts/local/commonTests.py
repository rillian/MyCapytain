# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import functools
import warnings
from io import open
from unittest import TestCase

from six import text_type as str

import MyCapytain.errors
from MyCapytain.common.constants import Mimetypes
from MyCapytain.common.reference._capitains_cts import CtsReference, URN, Citation, CtsReferenceSet
from MyCapytain.resources.texts.local.capitains.cts import CapitainsCtsText


def call_with_simple(f):
    """ Simple decorator tool to run a test with both simple = True and simple = False

    :param f:
    :return:
    """
    @functools.wraps(f)
    def decorator(s):
        for arg_tuple in [True, False]:
            f(s, arg_tuple)
    return decorator


class CapitainsXmlTextTest(TestCase):
    text = None
    TEI = None
    text_complex = None
    seneca = None

    def __init__(self, *args, **kwargs):
        """ Small helper to prevent run while inheriting from TestCase """
        super(CapitainsXmlTextTest, self).__init__(*args, **kwargs)
        self.helper = None
        # Kludge alert: We want this class to carry test cases without being run
        # by the unit test framework, so the `run' method is overridden to do
        # nothing.  But in order for sub-classes to be able to do something when
        # run is invoked, the constructor will rebind `run' from TestCase.
        if self.__class__ != CapitainsXmlTextTest:
            # Rebind `run' from the parent class.
            self.run = TestCase.run.__get__(self, self.__class__)
        else:
            self.run = lambda self, *args, **kwargs: None

    def testURN(self):
        """ Check that urn is set"""
        tei = CapitainsCtsText(resource=self.TEI.xml, urn="urn:cts:latinLit:phi1294.phi002.perseus-lat2")
        self.assertEqual(str(tei.urn), "urn:cts:latinLit:phi1294.phi002.perseus-lat2")

    def test_fulltext(self):
        """ Ensure that you can make a getPassage on the full text """
        self.assertEqual(
            self.TEI.getTextualNode(None).export(Mimetypes.PYTHON.ETREE), self.TEI.resource,
            "GetPassage empty on a text returns the full XML"
        )

    def testFindCitation(self):
        self.assertEqual(
            self.TEI.citation.export(Mimetypes.XML.TEI),
            '<tei:cRefPattern n="book" matchPattern="(\\w+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/'
            'tei:div/tei:div[@n=\\\'$1\\\'])"><tei:p>This pointer pattern extracts book</tei:p></tei:cRefPattern>'
        )
        self.assertEqual(
            self.TEI.citation.child.export(Mimetypes.XML.TEI),
            '<tei:cRefPattern n="poem" matchPattern="(\\w+)\.(\\w+)" replacementPattern="#xpath(/tei:TEI/tei:text'
            '/tei:body/tei:div/tei:div[@n=\\\'$1\\\']/tei:div[@n=\\\'$2\\\'])"><tei:p>This pointer pattern extracts '
            'poem</tei:p></tei:cRefPattern>'
        )
        self.assertEqual(
            self.TEI.citation.child.child.export(Mimetypes.XML.TEI),
            '<tei:cRefPattern n="line" matchPattern="(\\w+)\.(\\w+)\.(\\w+)" replacementPattern="#xpath(/tei:TEI/'
            'tei:text/tei:body/tei:div/tei:div[@n=\\\'$1\\\']/tei:div[@n=\\\'$2\\\']/tei:l[@n=\\\'$3\\\'])"><tei:p>'
            'This pointer pattern extracts line</tei:p></tei:cRefPattern>'
        )

        self.assertEqual(len(self.TEI.citation), 3)

    def testFindComplexCitation(self):
        self.assertEqual(len(self.text_complex.citation), 2)

    def testCitationSetters(self):
        d = Citation()
        c = Citation(
            name="ahah",
            refsDecl="/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']",
            child=None
        )
        b = Citation(
            name="ahah",
            refsDecl="/tei:TEI/tei:text/tei:body/tei:div/tei:z[@n='$1']",
            child=None
        )
        with open("tests/testing_data/texts/sample.xml", "rb") as sample:
            a = CapitainsCtsText(resource=sample, citation=b)

        """ Test original setting """
        self.assertIs(a.citation, b)
        """ Test simple replacement """
        a.citation = d
        self.assertIs(a.citation, d)
        """ Test conversion """
        a.citation = c
        self.assertEqual(a.citation.name, "ahah")
        self.assertEqual(a.citation.child, None)
        self.assertEqual(a.citation.refsDecl, "/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']")
        self.assertEqual(a.citation.scope, "/tei:TEI/tei:text/tei:body/tei:div")
        self.assertEqual(a.citation.xpath, "/tei:div[@n='?']")

    def testValidReffs(self):
        # Test level 1
        self.assertEqual(list(map(lambda x: str(x), self.TEI.getValidReff())), ["1", "2"])
        # Test level 2
        self.assertEqual(list(map(lambda x: str(x), self.TEI.getValidReff(level=2)))[0], "1.pr")
        # Test level 3
        self.assertEqual(list(map(lambda x: str(x), self.TEI.getValidReff(level=3)))[0], "1.pr.1")
        self.assertEqual(list(map(lambda x: str(x), self.TEI.getValidReff(level=3)))[-1], "2.40.8")

        # Test with reference and level
        self.assertEqual(
            "2.1.2",
            str(self.TEI.getValidReff(reference=CtsReference("2.1"), level=3)[1])
        )
        self.assertEqual(
            "2.1.12",
            str(self.TEI.getValidReff(reference=CtsReference("2.1"), level=3)[-1])

        )
        self.assertEqual(
            (CtsReference("2.38.1"), CtsReference("2.38.2"), CtsReference("2.39.1"), CtsReference("2.39.2")),
            self.TEI.getValidReff(reference=CtsReference("2.38-2.39"), level=3)
        )

        # Test with reference and level autocorrected because too small
        self.assertEqual(
            "2.1.12",
            str(self.TEI.getValidReff(reference=CtsReference("2.1"), level=0)[-1]),
            "Level should be autocorrected to len(citation) + 1"
        )
        self.assertEqual(
            "2.1.12",
            str(self.TEI.getValidReff(reference=CtsReference("2.1"), level=2)[-1]),
            "Level should be autocorrected to len(citation) + 1 even if level == len(citation)"
        )

        self.assertEqual(
            CtsReferenceSet(*[CtsReference(ref) for ref in [
                '2.1.1', '2.1.2', '2.1.3', '2.1.4', '2.1.5', '2.1.6', '2.1.7', '2.1.8', '2.1.9', '2.1.10', '2.1.11',
                '2.1.12', '2.2.1', '2.2.2', '2.2.3', '2.2.4', '2.2.5', '2.2.6'
            ]], level=3, citation=[c for c in self.TEI.citation][-1]),
            self.TEI.getValidReff(reference=CtsReference("2.1-2.2")),
            "It could be possible to ask for range reffs children")

        self.assertEqual(
            CtsReferenceSet(CtsReference('2.1'), CtsReference('2.2')),
            self.TEI.getValidReff(reference=CtsReference("2.1-2.2"), level=2),
            "It could be possible to ask for range References reference at the same level in between milestone")

        self.assertEqual(
            CtsReferenceSet(CtsReference(ref) for ref in ['1.38', '1.39', '2.pr', '2.1', '2.2']),
            self.TEI.getValidReff(reference=CtsReference("1.38-2.2"), level=2),
            "It could be possible to ask for range References reference at the same level in between milestone "
            "across higher levels")

        self.assertEqual(
            CtsReferenceSet(CtsReference(ref) for ref in ['1.1.1', '1.1.2', '1.1.3', '1.1.4']),
            self.TEI.getValidReff(reference=CtsReference("1.1.1-1.1.4"), level=3),
            "It could be possible to ask for range reffs in between at the same level cross higher level")

        # Test level too deep
        with self.assertRaises(MyCapytain.errors.CitationDepthError):
            "Asking for a level too deep should return nothing"
            self.TEI.getValidReff(reference=CtsReference("2.1.1"), level=3)

        # Test wrong citation
        with self.assertRaises(KeyError):
            self.TEI.getValidReff(reference=CtsReference("2.hellno"), level=3)

    def test_nested_dict(self):
        """ Check the nested dict export of a local.CtsTextMetadata object """
        nested = self.TEI.export(output=Mimetypes.PYTHON.NestedDict, exclude=["tei:note"])
        self.assertEqual(nested["1"]["3"]["8"], "Ibis ab excusso missus in astra sago. ",
                         "Check that notes are removed ")
        self.assertEqual(nested["1"]["pr"]["1"], "Spero me secutum in libellis meis tale temperamen-",
                         "Check that dictionary path is well done")
        self.assertEqual(nested["1"]["12"]["1"], "Itur ad Herculeas gelidi qua Tiburis arces ",
                         "Check that dictionary path works on more than one passage")
        self.assertEqual(nested["2"]["pr"]["1"], "'Quid nobis' inquis 'cum epistula? parum enim tibi ",
                         "Check that different fist level works as well")
        self.assertEqual(
            [list(nested.keys()), list(nested["1"].keys())[:3], list(nested["2"]["pr"].keys())[:3]],
            [["1", "2"], ["pr", "1", "2"], ["sa", "1", "2"]],
            "Ensure that text keeps its order")

    def test_warning(self):
        with open("tests/testing_data/texts/duplicate_references.xml") as xml:
            text = CapitainsCtsText(resource=xml)
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            for i in [1, 2, 3]:
                text.getValidReff(level=i, _debug=True)

        self.assertEqual(len(w), 3, "There should be warning on each level")
        self.assertEqual(issubclass(w[-1].category, MyCapytain.errors.DuplicateReference), True,
                         "Warning should be DuplicateReference")
        self.assertEqual(str(w[0].message), "1", "Warning message should be list of duplicate")

    def test_empty_ref_warning(self):
        with open("tests/testing_data/texts/empty_references.xml") as xml:
            text = CapitainsCtsText(resource=xml)
        with warnings.catch_warnings(record=True) as w:
            # Cause all warnings to always be triggered.
            warnings.simplefilter("always")
            for i in [1, 2, 3]:
                text.getValidReff(level=i, _debug=True)

        self.assertEqual(len(w), 3, "There should be warning on each level")
        self.assertEqual(issubclass(w[-1].category, MyCapytain.errors.EmptyReference), True,
                         "Warning should be EmptyReference")
        self.assertEqual([str(s.message) for s in w],
                         ["1 empty reference(s) at citation level 1",
                          "1 empty reference(s) at citation level 2",
                          "1 empty reference(s) at citation level 3"],
                         "Warning message should indicate number of references and the level at which they occur")

    def test_wrong_main_scope(self):
        with open("tests/testing_data/texts/sample2.xml", "rb") as f:
            with self.assertRaises(MyCapytain.errors.RefsDeclError):
                (CapitainsCtsText(resource=f)).test()

    def test_reffs(self):
        """ Check that every level is returned trough reffs property """
        self.assertEqual(("1" in list(map(lambda x: str(x), self.TEI.reffs))), True)
        self.assertEqual(("1.pr" in list(map(lambda x: str(x), self.TEI.reffs))), True)
        self.assertEqual(("2.40.8" in list(map(lambda x: str(x), self.TEI.reffs))), True)

    def test_complex_reffs(self):
        """ Test when there is a (something|something) xpath
        """
        self.assertEqual(("pr.1" in list(map(lambda x: str(x), self.text_complex.reffs))), True)

    def test_xml_no_refs_Decl(self):
        """ Test the result of parsing when there is no citation """
        with self.assertRaises(MyCapytain.errors.MissingRefsDecl):
            self.parse("tests/testing_data/texts/refsDeclButNoCTS.xml")

    def test_xml_with_xml_id(self):
        """ Test that xml:id is Citation xpath works fine in passage retriaval """
        text = self.parse("tests/testing_data/texts/xml_id.xml")
        self.assertEqual(
            text.citation.child.fill(["1", "2"]),
            "/tei:TEI/tei:text/tei:body/tei:lg/tei:l[@n='1']//tei:w[@xml:id='2']",
            "Filling of citation and citation detection should work"
        )
        self.assertIn(
            '<l n="1" xml:id="C_l_1"><q><w lemma="ce2"',
            text.getTextualNode(subreference="1.C_w_000001").export(Mimetypes.XML.TEI),
            "Word should be there !"
        )
        self.assertEqual(
            text.getReffs(level=2), CtsReferenceSet(CtsReference(ref) for ref in [
                '1.C_w_000001', '1.C_w_000002', '1.C_w_000003', '1.C_w_000004', '1.C_w_000005',
                '1.C_w_000006', '1.C_w_000007', '2.C_w_000008', '2.C_w_000009', '2.C_w_000010',
                '2.C_w_000011', '2.C_w_000012', '2.C_w_000013', '2.C_w_000014'
            ]),
            "XML:IDs and N should be retrieved."
        )

    def test_urn(self):
        """ Test setters and getters for urn """

        # Should work with string
        self.TEI.urn = "urn:cts:latinLit:tg.wk.v"
        self.assertEqual(isinstance(self.TEI.urn, URN), True)
        self.assertEqual(str(self.TEI.urn), "urn:cts:latinLit:tg.wk.v")

        # Test for URN
        self.TEI.urn = URN("urn:cts:latinLit:tg.wk.v2")
        self.assertEqual(isinstance(self.TEI.urn, URN), True)
        self.assertEqual(str(self.TEI.urn), "urn:cts:latinLit:tg.wk.v2")

        # Test it fails if not basestring or URN
        with self.assertRaises(TypeError):
            self.TEI.urn = 2

    @call_with_simple
    def test_get_passage(self, simple):
        a = self.TEI.getTextualNode(["1", "pr", "2"], simple=simple)
        self.assertEqual(a.export(output=Mimetypes.PLAINTEXT), "tum, ut de illis queri non possit quisquis de se bene ")
        # With reference
        a = self.TEI.getTextualNode(CtsReference("2.5.5"), simple=simple)
        self.assertEqual(a.export(output=Mimetypes.PLAINTEXT), "Saepe domi non es, cum sis quoque, saepe negaris: ")

    @call_with_simple
    def test_get_passage_autoparse(self, simple):
        a = self.TEI.getTextualNode(CtsReference("2.5.5"), simple=simple)
        self.assertEqual(
            a.export(output=Mimetypes.PLAINTEXT), "Saepe domi non es, cum sis quoque, saepe negaris: ",
            "CtsTextMetadata are automatically parsed in GetPassage hypercontext = False"
        )

    def test_get_Passage_context_no_double_slash(self):
        """ Check that get CapitainsCtsPassage contexts return right information """
        simple = self.TEI.getTextualNode(CtsReference("1.pr.2"))
        str_simple = simple.tostring(encoding=str)
        text = CapitainsCtsText(
            resource=str_simple,
            citation=self.TEI.citation
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1.pr.2"), simple=True).export(
                output=Mimetypes.PLAINTEXT).strip(),
            "tum, ut de illis queri non possit quisquis de se bene",
            "Ensure passage finding with context is fully TEI / Capitains compliant (One reference CapitainsCtsPassage)"
        )

        simple = self.TEI.getTextualNode(CtsReference("1.pr.2-1.pr.7"))
        str_simple = simple.tostring(encoding=str)
        text = CapitainsCtsText(
            resource=str_simple,
            citation=self.TEI.citation
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1.pr.2"), simple=True).export(
                output=Mimetypes.PLAINTEXT
            ).strip(),
            "tum, ut de illis queri non possit quisquis de se bene",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Same level same "
            "parent range CapitainsCtsPassage)"
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1.pr.3"), simple=True).export(
                output=Mimetypes.PLAINTEXT).strip(),
            "senserit, cum salva infimarum quoque personarum re-",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Same level same "
            "parent range CapitainsCtsPassage)"
        )
        self.assertEqual(
            list(map(lambda x: str(x), text.getValidReff(level=3))),
            ["1.pr.2", "1.pr.3", "1.pr.4", "1.pr.5", "1.pr.6", "1.pr.7"],
            "Ensure passage finding with context is fully TEI / Capitains compliant (Same level same "
            "parent range CapitainsCtsPassage)"
        )

        simple = self.TEI.getTextualNode(CtsReference("1.pr.2-1.1.6"))
        str_simple = simple.tostring(encoding=str)
        text = CapitainsCtsText(
            resource=str_simple,
            citation=self.TEI.citation
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1.pr.2"), simple=True).export(
                output=Mimetypes.PLAINTEXT).strip(),
            "tum, ut de illis queri non possit quisquis de se bene",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Same level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1.1.6"), simple=True).export(
                output=Mimetypes.PLAINTEXT).strip(),
            "Rari post cineres habent poetae.",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Same level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            list(map(lambda x: str(x), text.getValidReff(level=3))),
            [
                "1.pr.2", "1.pr.3", "1.pr.4", "1.pr.5", "1.pr.6", "1.pr.7",
                "1.pr.8", "1.pr.9", "1.pr.10", "1.pr.11", "1.pr.12", "1.pr.13",
                "1.pr.14", "1.pr.15", "1.pr.16", "1.pr.17", "1.pr.18", "1.pr.19",
                "1.pr.20", "1.pr.21", "1.pr.22",
                "1.1.1", "1.1.2", "1.1.3", "1.1.4", "1.1.5", "1.1.6",
            ],
            "Ensure passage finding with context is fully TEI / Capitains compliant (Same level range CapitainsCtsPassage)"
        )

        simple = self.TEI.getTextualNode(CtsReference("1.pr.2-1.2"))
        str_simple = simple.tostring(encoding=str)
        text = CapitainsCtsText(
            resource=str_simple,
            citation=self.TEI.citation
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1.pr.2"), simple=True).export(
                output=Mimetypes.PLAINTEXT).strip(),
            "tum, ut de illis queri non possit quisquis de se bene",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1.1.6"), simple=True).export(
                output=Mimetypes.PLAINTEXT).strip(),
            "Rari post cineres habent poetae.",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            list(map(lambda x: str(x), text.getValidReff(level=3))),
            [
                "1.pr.2", "1.pr.3", "1.pr.4", "1.pr.5", "1.pr.6", "1.pr.7",
                "1.pr.8", "1.pr.9", "1.pr.10", "1.pr.11", "1.pr.12", "1.pr.13",
                "1.pr.14", "1.pr.15", "1.pr.16", "1.pr.17", "1.pr.18", "1.pr.19",
                "1.pr.20", "1.pr.21", "1.pr.22",
                "1.1.1", "1.1.2", "1.1.3", "1.1.4", "1.1.5", "1.1.6",
                '1.2.1', '1.2.2', '1.2.3', '1.2.4', '1.2.5', '1.2.6', '1.2.7', '1.2.8'
            ],
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )

    @call_with_simple
    def test_get_passage_with_list(self, simple):
        """ In range, passage in between could be removed from the original text by error
        """
        simple = self.TEI.getTextualNode(["1", "pr", "2"], simple=simple)
        self.assertEqual(
            simple.export(output=Mimetypes.PLAINTEXT).strip(),
            "tum, ut de illis queri non possit quisquis de se bene",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )

    def test_type_accepted_reference_validreff(self):
        """ In range, passage in between could be removed from the original text by error
        """
        with self.assertRaises(TypeError):
            self.TEI.getValidReff(reference=["1", "pr", "2", "5"])

    @call_with_simple
    def test_citation_length_error(self, simple):
        """ In range, passage in between could be removed from the original text by error
        """
        with self.assertRaises(MyCapytain.errors.CitationDepthError):
            self.TEI.getTextualNode(["1", "pr", "2", "5"], simple=simple)

    def test_ensure_passage_is_not_removed(self):
        """ In range, passage in between could be removed from the original text by error
        """
        self.TEI.getTextualNode(CtsReference("1.pr.1-1.2.5"))
        orig_refs = self.TEI.getValidReff(level=3)
        self.assertIn("1.pr.1", orig_refs)
        self.assertIn("1.1.1", orig_refs)
        self.assertIn("1.2.4", orig_refs)
        self.assertIn("1.2.5", orig_refs)

        self.TEI.getTextualNode(CtsReference("1.pr-1.2"))
        orig_refs = self.TEI.getValidReff(level=3)
        self.assertIn("1.pr.1", orig_refs)
        self.assertIn("1.1.1", orig_refs)
        self.assertIn("1.2.4", orig_refs)
        self.assertIn("1.2.5", orig_refs)

    def test_get_passage_hypercontext_complex_xpath(self):
        simple = self.text_complex.getTextualNode(CtsReference("pr.1-1.2"))
        str_simple = simple.tostring(encoding=str)
        text = CapitainsCtsText(
            resource=str_simple,
            citation=self.text_complex.citation
        )
        self.assertIn(
            "Pervincis tandem",
            text.getTextualNode(CtsReference("pr.1"), simple=True).export(
                output=Mimetypes.PLAINTEXT,
                exclude=["tei:note"]).strip(),
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1.2"), simple=True).export(
                output=Mimetypes.PLAINTEXT).strip(),
            "lusimus quos in Suebae gratiam virgunculae,",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            list(map(lambda x: str(x), text.getValidReff(level=2))),
            [
                "pr.1", "1.1", "1.2"
            ],
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )

    @call_with_simple
    def test_Text_text_function(self, simple):
        simple = self.seneca.getTextualNode(CtsReference("1"), simple=simple)
        str_simple = simple.tostring(encoding=str)
        text = CapitainsCtsText(
            resource=str_simple,
            citation=self.seneca.citation
        )
        self.assertEqual(
            text.export(output=Mimetypes.PLAINTEXT, exclude=["tei:note"]).strip(),
            "Di coniugales tuque genialis tori,",
            "Ensure text methods works on CtsTextMetadata object"
        )

    def test_get_passage_hyper_context_double_slash_xpath(self):
        simple = self.seneca.getTextualNode(CtsReference("1-10"))
        str_simple = simple.export(
            output=Mimetypes.XML.Std
        )
        text = CapitainsCtsText(
            resource=str_simple,
            citation=self.seneca.citation
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1"), simple=True).export(
                output=Mimetypes.PLAINTEXT,
                exclude=["tei:note"]
            ).strip(),
            "Di coniugales tuque genialis tori,",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("10"), simple=True).export(
                output=Mimetypes.PLAINTEXT
            ).strip(),
            "aversa superis regna manesque impios",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            list(map(lambda x: str(x), text.getValidReff(level=1))),
            ["1", "2", "3", "4", "5", "6", "7", "8", "9", "10"],
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )

        simple = self.seneca.getTextualNode(CtsReference("1"))
        str_simple = simple.tostring(encoding=str)
        text = CapitainsCtsText(
            resource=str_simple,
            citation=self.seneca.citation
        )
        self.assertEqual(
            text.getTextualNode(CtsReference("1"), simple=True).export(
                output=Mimetypes.PLAINTEXT,
                exclude=["tei:note"]
            ).strip(),
            "Di coniugales tuque genialis tori,",
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )
        self.assertEqual(
            list(map(lambda x: str(x), text.getValidReff(level=1))),
            ["1"],
            "Ensure passage finding with context is fully TEI / Capitains compliant (Different level range CapitainsCtsPassage)"
        )


class CapitainsXmlPassageTests(TestCase):
    simple = True
    URN = None
    URN_2 = None
    TEI = None
    FULL_EPIGRAMMATA = None

    def __init__(self, *args, **kwargs):
        """ Small helper to prevent run while inheriting from TestCase """
        super(CapitainsXmlPassageTests, self).__init__(*args, **kwargs)
        self.helper = None
        # Kludge alert: We want this class to carry test cases without being run
        # by the unit test framework, so the `run' method is overridden to do
        # nothing.  But in order for sub-classes to be able to do something when
        # run is invoked, the constructor will rebind `run' from TestCase.
        if self.__class__ != CapitainsXmlPassageTests:
            # Rebind `run' from the parent class.
            self.run = TestCase.run.__get__(self, self.__class__)
        else:
            self.run = lambda self, *args, **kwargs: None

    @call_with_simple
    def test_urn(self, simple):
        """ Test URN and ids getters/setters """

        a = self.TEI.getTextualNode(["2", "40", "8"], simple=simple)
        self.assertEqual(
            str(a.reference), "2.40.8",
            "CapitainsCtsPassage should have a URN parameter"
        )

    @call_with_simple
    def test_next(self, simple):
        """ Test next property """
        # Normal passage checking
        # self.TEI.parse()
        p = self.TEI.getTextualNode("1.pr.1", simple=simple)
        self.assertEqual(str(p.next.reference), "1.pr.2")

        # End of lowest level passage checking but not end of parent level
        p = self.TEI.getTextualNode(["1", "pr", "22"], simple=simple)
        self.assertEqual(str(p.next.reference), "1.1.1")

        # End of lowest level passage and end of parent level
        p = self.TEI.getTextualNode(["1", "39", "8"], simple=simple)
        self.assertEqual(str(p.next.reference), "2.pr.sa")

        # Last line should always be None
        p = self.TEI.getTextualNode(["2", "40", "8"], simple=simple)
        self.assertIsNone(p.next)
        p = self.TEI.getTextualNode(["2", "40"], simple=simple)
        self.assertIsNone(p.next)
        p = self.TEI.getTextualNode(["2"], simple=simple)
        self.assertIsNone(p.next)

    @call_with_simple
    def test_children(self, simple):
        """ Test children property """
        # Normal children checking
        p = self.TEI.getTextualNode(["1", "pr"], simple=simple)
        self.assertEqual(
            [
                x for x in p.children if str(x.reference) == "1.pr.1"
                ][0].export(output=Mimetypes.PLAINTEXT),
            "Spero me secutum in libellis meis tale temperamen-",
            """ Ensure that children are text objects and retain there capacities """
        )

        p = self.TEI.getTextualNode(["1", "pr", "1"], simple=simple)
        self.assertEqual(len(list(p.children)), 0)

    @call_with_simple
    def test_first(self, simple):
        """ Test first property """
        # Test when there is one
        # self.TEI.parse()
        p = self.TEI.getTextualNode(["1", "1"], simple=simple)
        self.assertEqual(
            str(p.firstId), "1.1.1",
            "Property first Id should be the reference of the first item"
        )
        self.assertEqual(
            p.first.export(output=Mimetypes.PLAINTEXT), "Hic est quem legis ille, quem requiris, ",
            "First should be a passage with passage capacities"
        )
        # #And failing when no first
        p = self.TEI.getTextualNode(["1", "1", "1"], simple=simple)
        self.assertEqual(
            p.lastId, None,
            "Property such as ID should not raise error when there is no child"
        )

    @call_with_simple
    def test_last(self, simple):
        """ Test last property """
        # self.TEI.parse()
        # Test when there is one
        p = self.TEI.getTextualNode(["1", "pr"], simple=simple)
        self.assertEqual(p.last.export(
            output=Mimetypes.PLAINTEXT), "An ideo tantum veneras, ut exires? ",
            ".last should be a passage with passage capacities"
        )
        self.assertEqual(
            str(p.last.reference), "1.pr.22",
            "Property lastId should be the reference of the last item"
        )
        # #And failing when no last
        p = self.TEI.getTextualNode(["1", "pr", "1"], simple=simple)
        self.assertEqual(
            p.lastId, None,
            "Property such as ID should not raise error when there is no child"
        )

    @call_with_simple
    def test_prev(self, simple):
        """ Test prev property """
        # self.TEI.parse()
        # Normal passage checking
        p = self.TEI.getTextualNode(["2", "40", "8"], simple=simple)
        self.assertEqual(str(p.prev.reference), "2.40.7")
        p = self.TEI.getTextualNode(["2", "40"], simple=simple)
        self.assertEqual(str(p.prev.reference), "2.39")
        p = self.TEI.getTextualNode(["2"], simple=simple)
        self.assertEqual(str(p.prev.reference), "1")

        # test failing passage
        p = self.TEI.getTextualNode(["1", "pr", "1"], simple=simple)
        self.assertEqual(p.prev, None)
        p = self.TEI.getTextualNode(["1", "pr"], simple=simple)
        self.assertEqual(p.prev, None)
        p = self.TEI.getTextualNode(["1"], simple=simple)
        self.assertEqual(p.prev, None)

        # First child should get to parent's prev last child
        p = self.TEI.getTextualNode(["1", "1", "1"], simple=simple)
        self.assertEqual(str(p.prev.reference), "1.pr.22")

        # Beginning of lowest level passage and beginning of parent level
        p = self.TEI.getTextualNode(["2", "pr", "sa"], simple=simple)
        self.assertEqual(str(p.prev.reference), "1.39.8")

    @call_with_simple
    def test_siblingsId(self, simple):
        """ Test prev property """
        # Normal passage checking
        p, n = self.FULL_EPIGRAMMATA.getTextualNode(["2"], simple=simple).siblingsId
        self.assertEqual(("1", "3"), (str(p), str(n)), "Middle node should have right siblings")
        p, n = self.FULL_EPIGRAMMATA.getTextualNode(["1"], simple=simple).siblingsId
        self.assertEqual((None, "2"), (p, str(n)), "First node should have right siblings")
        p, n = self.FULL_EPIGRAMMATA.getTextualNode(["14"], simple=simple).siblingsId
        self.assertEqual(("13", None), (str(p), n), "Last node should have right siblings")
        # Ranges
        if simple is False:
            # Start
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("1-2"), simple=simple).siblingsId
            self.assertEqual((None, "3-4"), (p, str(n)), "First node should have right siblings")
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("1-5"), simple=simple).siblingsId
            self.assertEqual((None, "6-10"), (p, str(n)), "First node should have right siblings")
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("1-9"), simple=simple).siblingsId
            self.assertEqual((None, "10-14"), (p, str(n)), "First node should have right siblings")
            # End
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("12-14"), simple=simple).siblingsId
            self.assertEqual(("9-11", None), (str(p), n), "Last node should have right siblings")
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("11-14"), simple=simple).siblingsId
            self.assertEqual(("7-10", None), (str(p), n), "Last node should have right siblings")
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("5-14"), simple=simple).siblingsId
            self.assertEqual(("1-4", None), (str(p), n), "Should take the rest")
            # Middle
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("5-6"), simple=simple).siblingsId
            self.assertEqual(("3-4", "7-8"), (str(p), str(n)), "Middle node should have right siblings")
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("5-8"), simple=simple).siblingsId
            self.assertEqual(("1-4", "9-12"), (str(p), str(n)), "Middle node should have right siblings")
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("5-10"), simple=simple).siblingsId
            self.assertEqual(("1-4", "11-14"), (str(p), str(n)), "Middle node should have right siblings")
            # NONE !
            p, n = self.FULL_EPIGRAMMATA.getTextualNode(CtsReference("1-14"), simple=simple).siblingsId
            self.assertEqual((None, None), (p, n), "If whole range, nothing !")


class CapitainsXMLRangePassageTests(TestCase):
    text = None
    passage = None
    
    def __init__(self, *args, **kwargs):
        """ Small helper to prevent run while inheriting from TestCase """
        super(CapitainsXMLRangePassageTests, self).__init__(*args, **kwargs)
        self.helper = None
        # Kludge alert: We want this class to carry test cases without being run
        # by the unit test framework, so the `run' method is overridden to do
        # nothing.  But in order for sub-classes to be able to do something when
        # run is invoked, the constructor will rebind `run' from TestCase.
        if self.__class__ != CapitainsXMLRangePassageTests:
            # Rebind `run' from the parent class.
            self.run = TestCase.run.__get__(self, self.__class__)
        else:
            self.run = lambda self, *args, **kwargs: None

    def test_errors(self):
        """ Ensure that some results throws errors according to some standards """
        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("1.pr.2-1.2"))
        with self.assertRaises(MyCapytain.errors.InvalidSiblingRequest, msg="Different range passage have no siblings"):
            a = passage.next

        with self.assertRaises(MyCapytain.errors.InvalidSiblingRequest, msg="Different range passage have no siblings"):
            a = passage.prev

    def test_prevnext_on_first_passage(self):
        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("1.pr.1-1.2.1"))
        self.assertEqual(
            "1.2.2-1.5.2", str(passage.nextId),
            "Next reff should be the same length as sibling"
        )
        self.assertEqual(
            None, passage.prevId,
            "Prev reff should be none if we are on the first passage of the text"
        )

    def test_prevnext_on_close_to_first_passage(self):
        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("1.pr.10-1.2.1"))
        self.assertEqual(
            "1.2.2-1.4.1", str(passage.nextId),
            "Next reff should be the same length as sibling"
        )
        self.assertEqual(
            "1.pr.1-1.pr.9", str(passage.prevId),
            "Prev reff should start at the beginning of the text, no matter the length of the reference"
        )

    def test_prevnext_on_last_passage(self):
        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("2.39.2-2.40.8"))
        self.assertEqual(
            None, passage.nextId,
            "Next reff should be none if we are on the last passage of the text"
        )
        self.assertEqual(
            "2.37.6-2.39.1", str(passage.prevId),
            "Prev reff should be the same length as sibling"
        )

    def test_prevnext_on_close_to_last_passage(self):
        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("2.39.2-2.40.5"))
        self.assertEqual(
            "2.40.6-2.40.8", str(passage.nextId),
            "Next reff should finish at the end of the text, no matter the length of the reference"
        )
        self.assertEqual(
            "2.37.9-2.39.1", str(passage.prevId),
            "Prev reff should be the same length as sibling"
        )

    def test_prevnext(self):
        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("1.pr.5-1.pr.6"))
        self.assertEqual(
            "1.pr.7-1.pr.8", str(passage.nextId),
            "Next reff should be the same length as sibling"
        )
        self.assertEqual(
            "1.pr.3-1.pr.4", str(passage.prevId),
            "Prev reff should be the same length as sibling"
        )
        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("1.pr.5"))
        self.assertEqual(
            "1.pr.6", str(passage.nextId),
            "Next reff should be the same length as sibling"
        )
        self.assertEqual(
            "1.pr.4", str(passage.prevId),
            "Prev reff should be the same length as sibling"
        )

        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("1.pr"))
        self.assertEqual(
            "1.1", str(passage.nextId),
            "Next reff should be the same length as sibling"
        )
        self.assertEqual(
            None, passage.prevId,
            "Prev reff should be None when at the start"
        )

        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("2.40"))
        self.assertEqual(
            "2.39", str(passage.prevId),
            "Prev reff should be the same length as sibling"
        )
        self.assertEqual(
            None, passage.nextId,
            "Next reff should be None when at the start"
        )

    def test_first_list(self):
        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("2.39"))
        print(list(passage.children), str(passage.firstId))
        self.assertEqual(
            "2.39.1", str(passage.firstId),
            "First reff should be the first"
        )
        self.assertEqual(
            "2.39.2", str(passage.lastId),
            "Last reff should be the last"
        )

        passage = self.text.getTextualNode(MyCapytain.common.reference.CtsReference("2.39-2.40"))
        self.assertEqual(
            "2.39.1", str(passage.firstId),
            "First reff should be the first"
        )
        self.assertEqual(
            "2.40.8", str(passage.lastId),
            "Last reff should be the last"
        )
