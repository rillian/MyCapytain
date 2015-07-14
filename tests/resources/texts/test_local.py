# -*- coding: utf-8 -*-
from __future__ import unicode_literals

import unittest
from six import text_type as str
from io import open
import xmlunittest

import MyCapytain.resources.texts.local
import MyCapytain.resources.texts.tei
import MyCapytain.common.reference

class TestLocalXMLImplementation(unittest.TestCase, xmlunittest.XmlTestMixin):

    """ Test XML Implementation of resources found in local file """

    def setUp(self):
        self.text = open("tests/testing_data/texts/sample.xml", "rb")
        self.TEI = MyCapytain.resources.texts.local.Text(resource=self.text)

    def tearDown(self):
        self.text.close()

    def testFindCitation(self):
        self.assertEqual(
            str(self.TEI.citation),
            '<tei:cRefPattern n="book" matchPattern="(\\w+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n=\\\'$1\\\'])"><tei:p>This pointer pattern extracts book</tei:p></tei:cRefPattern>'
        )
        self.assertEqual(
            str(self.TEI.citation.child),
            '<tei:cRefPattern n="poem" matchPattern="(\\w+)\.(\\w+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n=\\\'$1\\\']/tei:div[@n=\\\'$2\\\'])"><tei:p>This pointer pattern extracts poem</tei:p></tei:cRefPattern>'
        )
        self.assertEqual(
            str(self.TEI.citation.child.child),
            '<tei:cRefPattern n="line" matchPattern="(\\w+)\.(\\w+)\.(\\w+)" replacementPattern="#xpath(/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n=\\\'$1\\\']/tei:div[@n=\\\'$2\\\']/tei:l[@n=\\\'$3\\\'])"><tei:p>This pointer pattern extracts line</tei:p></tei:cRefPattern>'
        )

        self.assertEqual(len(self.TEI.citation), 3)

    def testCitationSetters(self):
        d = MyCapytain.resources.texts.tei.Citation()
        c = MyCapytain.common.reference.Citation(name="ahah", refsDecl="/tei:TEI/tei:text/tei:body/tei:div/tei:div[@n='$1']", child=None)
        b = MyCapytain.resources.texts.tei.Citation()
        a = MyCapytain.resources.texts.local.Text(citation=b)
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

    def testFindCitation(self):
        self.assertEqual(self.TEI.getValidReff(), ["1", "2"])
        self.assertEqual(self.TEI.getValidReff(level=2)[0], "1.pr")
        self.assertEqual(self.TEI.getValidReff(level=3)[0], "1.pr.1")
        self.assertEqual(self.TEI.getValidReff(level=3)[-1], "2.40.8")
        self.assertEqual(self.TEI.getValidReff(passage=MyCapytain.common.reference.Reference("2.1"),level=3)[1], "2.1.2")
        self.assertEqual(self.TEI.getValidReff(passage=MyCapytain.common.reference.Reference("2.1"),level=3)[-1], "2.1.12")
        self.assertEqual(self.TEI.getValidReff(passage=MyCapytain.common.reference.Reference("2.1.1"),level=3), [])