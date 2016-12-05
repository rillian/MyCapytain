# -*- coding: utf-8 -*-

from __future__ import unicode_literals

from six import text_type as str

from MyCapytain.common.metadata import Metadata
from MyCapytain.common.utils import Mimetypes, xmlparser, NS
from MyCapytain.common.reference import Citation, URN, Reference
from MyCapytain.resources.collections import cts as CTSCollection
from MyCapytain.resources.prototypes import text as prototypes
from MyCapytain.resources.texts.encodings import TEIResource
from MyCapytain.retrievers.prototypes import CitableTextServiceRetriever
from MyCapytain.errors import MissingAttribute


class __SharedMethod__(prototypes.InteractiveTextualNode):
    """ Set of methods shared by Text and Passage

    :param retriever: CitableTextServiceRetriever
    """

    def __init__(self, retriever=None, *args, **kwargs):
        super(__SharedMethod__, self).__init__(*args, **kwargs)
        self.__retriever__ = retriever
        self.__first__ = False
        self.__last__ = False
        if retriever is None:
            raise MissingAttribute("Object has not retriever")

        if "metadata" in kwargs and isinstance(kwargs["metadata"], Metadata):
            self.metadata = kwargs["metadata"]
        else:
            self.metadata = Metadata(keys=[
                "groupname", "label", "title"
            ])

    @property
    def retriever(self):
        return self.__retriever__

    def getValidReff(self, level=1, reference=None):
        """ Given a resource, CitableText will compute valid reffs

        :param level: Depth required. If not set, should retrieve first encountered level (1 based)
        :type level: Int
        :param reference: Passage reference
        :type reference: Reference
        :rtype: list(str)
        :returns: List of levels
        """
        if reference:
            urn = "{0}:{1}".format(self.urn, reference)
        else:
            urn = str(self.urn)

        if level == -1:
            level = len(self.citation)

        xml = self.retriever.getValidReff(
            level=level,
            urn=urn
        )
        xml = xmlparser(xml)
        self.__parse_request__(xml.xpath("//ti:request", namespaces=NS)[0])

        return [ref for ref in xml.xpath("//ti:reply//ti:urn/text()", namespaces=NS)]

    def getPassage(self, reference=None):
        """ Retrieve a passage and store it in the object

        :param reference: Reference of the passage
        :type reference: Reference, or URN, or str or list(str)
        :rtype: Passage
        :returns: Object representing the passage
        :raises: *TypeError* when reference is not a list or a Reference
        """
        if isinstance(reference, URN):
            urn = str(reference)
        elif isinstance(reference, Reference):
            urn = "{0}:{1}".format(self.urn, str(reference))
        elif isinstance(reference, str):
            if ":" in reference:
                urn = reference
            else:
                urn = "{0}:{1}".format(self.urn, reference)
        elif isinstance(reference, list):
            urn = "{0}:{1}".format(self.urn, ".".join(reference))
        else:
            urn = str(self.urn)

        response = xmlparser(self.retriever.getPassage(urn=urn))

        self.__parse_request__(response.xpath("//ti:request", namespaces=NS)[0])
        return Passage(urn=urn, resource=response, retriever=self.retriever)

    def getReffs(self, level=1, reference=None):
        """ Reference available at a given level

        :param level: Depth required. If not set, should retrieve first encountered level (1 based)
        :type level: Int
        :param passage: Subreference (optional)
        :type passage: Reference
        :rtype: List.basestring
        :returns: List of levels
        """
        if hasattr(self, "__depth__"):
            level = level + self.depth

        return self.getValidReff(level, reference)

    def getPassagePlus(self, reference=None):
        """ Retrieve a passage and informations around it and store it in the object

        :param reference: Reference of the passage
        :type reference: Reference or List of basestring
        :rtype: Passage
        :returns: Object representing the passage
        :raises: *TypeError* when reference is not a list or a Reference
        """
        if reference:
            urn = "{0}:{1}".format(self.urn, reference)
        else:
            urn = str(self.urn)

        response = xmlparser(self.retriever.getPassagePlus(urn=urn))

        self.__parse_request__(response.xpath("//ti:reply/ti:label", namespaces=NS)[0])
        passage = Passage(urn=urn, resource=response, retriever=self.retriever)
        passage.metadata, passage.citation = self.metadata, self.citation
        return passage

    def __parse_request__(self, xml):
        """ Parse a request with metadata information

        :param xml: LXML Object
        :type xml: Union[lxml.etree._Element]
        """
        for node in xml.xpath(".//ti:groupname", namespaces=NS):
            lang = node.get("xml:lang") or Text.DEFAULT_LANG
            self.metadata["groupname"][lang] = node.text

        for node in xml.xpath(".//ti:title", namespaces=NS):
            lang = node.get("xml:lang") or Text.DEFAULT_LANG
            self.metadata["title"][lang] = node.text

        for node in xml.xpath(".//ti:label", namespaces=NS):
            lang = node.get("xml:lang") or Text.DEFAULT_LANG
            self.metadata["label"][lang] = node.text

        # Need to code that p
        if self.citation.isEmpty() and xml.xpath("//ti:citation", namespaces=NS):
            self.citation = CTSCollection.Citation.ingest(
                xml,
                xpath=".//ti:citation[not(ancestor::ti:citation)]"
            )

    def getLabel(self):
        """ Retrieve metadata about the text

        :rtype: Metadata
        :returns: Dictionary with label informations
        """
        response = xmlparser(
            self.retriever.getLabel(urn=str(self.urn))
        )

        self.__parse_request__(
            response.xpath("//ti:reply/ti:label", namespaces=NS)[0]
        )

        return self.metadata

    def getPrevNextUrn(self, reference):
        """ Get the previous URN of a reference of the text

        :param reference: Reference from which to find siblings
        :type reference: Reference
        :return: (Previous Passage Reference,Next Passage Reference)
        """
        _prev, _next = __SharedMethod__.prevnext(
            self.retriever.getPrevNextUrn(
                urn="{}:{}".format(
                    str(
                        URN(
                            str(self.urn)).upTo(URN.NO_PASSAGE)
                    ),
                    str(reference)
                )
            )
        )
        return _prev, _next

    def getFirstUrn(self, reference=None):
        """ Get the first children URN for a given resource

        :param reference: Reference from which to find child (If None, find first reference)
        :type reference: Reference, str
        :return: Children URN
        :rtype: URN
        """
        if reference is not None:
            if ":" in reference:
                urn = reference
            else:
                urn = "{}:{}".format(
                    str(URN(str(self.urn)).upTo(URN.NO_PASSAGE)),
                    str(reference)
                )
        else:
            urn = str(self.urn)
        _first = __SharedMethod__.firstUrn(
            self.retriever.getFirstUrn(
                urn
            )
        )
        return _first

    @property
    def firstId(self):
        """ Children passage

        :rtype: str
        :returns: First children of the graph. Shortcut to self.graph.children[0]
        """
        if self.__first__ is False:
            # Request the next urn
            self.__first__ = self.getFirstUrn()
        return self.__first__

    @property
    def lastId(self):
        """ Children passage

        :rtype: str
        :returns: First children of the graph. Shortcut to self.graph.children[0]
        """
        if self.__last__ is False:
            # Request the next urn
            self.__last__ = self.childIds[-1]
        return self.__last__

    @staticmethod
    def firstUrn(resource):
        """ Parse a resource to get the first URN

        :param resource: XML Resource
        :type resource: etree._Element
        :return: Tuple representing previous and next urn
        :rtype: str
        """
        resource = xmlparser(resource)
        urn = resource.xpath("//ti:reply/ti:urn/text()", namespaces=NS, magic_string=True)

        if len(urn) > 0:
            urn = str(urn[0])
            return urn

    @staticmethod
    def prevnext(resource):
        """ Parse a resource to get the prev and next urn

        :param resource: XML Resource
        :type resource: etree._Element
        :return: Tuple representing previous and next urn
        :rtype: (str, str)
        """
        _prev, _next = False, False
        resource = xmlparser(resource)
        prevnext = resource.xpath("//ti:prevnext", namespaces=NS)

        if len(prevnext) > 0:
            _next, _prev = None, None
            prevnext = prevnext[0]
            _next_xpath = prevnext.xpath("ti:next/ti:urn/text()", namespaces=NS, smart_strings=False)
            _prev_xpath = prevnext.xpath("ti:prev/ti:urn/text()", namespaces=NS, smart_strings=False)

            if len(_next_xpath):
                _next = _next_xpath[0]

            if len(_prev_xpath):
                _prev = _prev_xpath[0]

        return _prev, _next


class Text(__SharedMethod__, prototypes.CitableText):
    """ API Text object

    :param urn: A URN identifier
    :type urn: Union[URN, str, unicode]
    :param resource: An API endpoint
    :type resource: CitableTextServiceRetriever
    :param citation: Citation for children level
    :type citation: Citation
    :param id: Identifier of the subreference without URN informations
    :type id: List

    """

    DEFAULT_LANG = "eng"

    def __init__(self, urn, retriever, citation=None, **kwargs):
        super(Text, self).__init__(retriever=retriever, urn=urn, citation=citation, **kwargs)

    @property
    def reffs(self):
        """ Get all valid reffs for every part of the CitableText

        :rtype: MyCapytain.resources.texts.tei.Citation
        """
        if self.citation.isEmpty():
            self.getLabel()
        return [
            reff for reffs in [self.getValidReff(level=i) for i in range(1, len(self.citation) + 1)] for reff in reffs
        ]

    @property
    def nextId(self):
        raise NotImplementedError

    @property
    def next(self):
        raise NotImplementedError

    @property
    def prev(self):
        raise NotImplementedError

    @property
    def prevId(self):
        raise NotImplementedError

    @property
    def siblingsId(self):
        raise NotImplementedError

    def export(self, output=None, exclude=None):
        """ Export the collection item in the Mimetype required.

        ..note:: If current implementation does not have special mimetypes, reuses default_export method

        :param output: Mimetype to export to (Uses Mimetypes)
        :type output: str
        :param exclude: Informations to exclude. Specific to implementations
        :type exclude: [str]
        :return: Object using a different representation
        """
        return self.getPassage().export(output, exclude)


class Passage(__SharedMethod__, prototypes.Passage, TEIResource):
    """ Passage representing

    :param urn:
    :param resource:
    :param retriever:
    :param args:
    :param kwargs:
    """

    def __init__(self, urn, resource, *args, **kwargs):
        SuperKwargs = {key: value for key, value in kwargs.items() if key not in ["parent"]}
        super(Passage, self).__init__(resource=resource, *args, **SuperKwargs)
        self.urn = urn

        # Could be set during parsing
        self.__next__ = False
        self.__prev__ = False
        self.__first__ = False
        self.__last__ = False

        self.__parse__()

    @property
    def prevId(self):
        """ Previous passage

        :rtype: Passage
        :returns: Previous passage at same level
        """
        if self.__prev__ is False:
            # Request the next urn
            self.__prev__, self.__next__ = self.getPrevNextUrn(reference=self.urn.reference)
        return self.__prev__

    @property
    def nextId(self):
        """ Shortcut for getting the following passage

        :rtype: Reference
        :returns: Following passage reference
        """
        if self.__next__ is False:
            # Request the next urn
            self.__prev__, self.__next__ = self.getPrevNextUrn(reference=self.urn.reference)
        return self.__next__

    def __parse__(self):
        """ Given self.resource, split informations from the CTS API

        :return: None
        """
        self.response = self.resource
        self.resource = self.resource.xpath("//ti:passage/tei:TEI", namespaces=NS)[0]

        self.__prev__, self.__next__ = __SharedMethod__.prevnext(self.response)

        if self.citation.isEmpty():
            self.citation = CTSCollection.Citation.ingest(
                self.response,
                xpath=".//ti:citation[not(ancestor::ti:citation)]"
            )