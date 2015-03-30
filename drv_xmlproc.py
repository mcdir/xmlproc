"""
A SAX driver for xmlproc

$Id: drv_xmlproc.py,v 1.9 1999/10/15 07:55:33 larsga Exp $
"""

version="0.95"

from xml.sax import saxlib,saxutils,saxmisc
from xml.parsers.xmlproc import xmlproc

import os

pre_parse_properties={"http://xml.org/sax/properties/namespace-sep":1,
                      "http://xml.org/sax/handlers/DeclHandler":1,
                      "http://xml.org/sax/handlers/LexicalHandler":1,
                      "http://xml.org/sax/handlers/NamespaceHandler":1}

# Todo:
# - must actually use catalog file
# - document interplay between reset and SAX2
# - fix bugs:
#    - startDTD must be called
# - do namespace processing, if it is requested
# - support more features and properties

XCATALOG =1
SOCATALOG=2

# --- SAX_XPParser

class SAX_XPParser(saxlib.Parser,xmlproc.Application,xmlproc.DTDConsumer,
                   xmlproc.ErrorHandler,xmlproc.PubIdResolver):

    def __init__(self):
	saxlib.Parser.__init__(self)
        self.reset()
        self.declHandler=saxmisc.DeclHandler()
        self.lexicalHandler=saxmisc.LexicalHandler()
        self.namespaceHandler=saxmisc.NamespaceHandler()
        self.ns_separator=" "
        self.locator=1
        self.is_parsing=0
        self.stop_on_error=1
        self.catalog_file=None
        self.catalog_type=None
    
    def parse(self,sysID):
        self.reset()
        try:
            self.is_parsing=1
            self.parser.parse_resource(sysID)
        finally:
            self.is_parsing=0

    def parseFile(self,file):
        self.reset()
        try:
            self.is_parsing=1
            self.parser.read_from(file)
            self.parser.flush()
            self.parser.parseEnd()
        finally:
            self.is_parsing=0
        
    def _create_parser(self):
	return xmlproc.XMLProcessor()

    def setLocale(self, locale):
        try:
            self.parser.set_error_language(locale)
        except KeyError:
            raise saxlib.SAXNotSupportedException("Locale '%s' not supported" % locale)
        
    # --- data event methods
    
    def doc_start(self):
        if self.locator:
            self.doc_handler.setDocumentLocator(self)
	self.doc_handler.startDocument()

    def doc_end(self):
	self.doc_handler.endDocument()

    def handle_data(self,data,start,end):
	self.doc_handler.characters(data,start,end-start)

    def handle_ignorable_data(self,data,start,end):
	self.doc_handler.ignorableWhitespace(data,start,end-start)

    def handle_pi(self, target, data):
	self.doc_handler.processingInstruction(target,data)

    def handle_start_tag(self, name, attrs):
	self.doc_handler.startElement(name,saxutils.AttributeMap(attrs))

    def handle_end_tag(self, name):
	self.doc_handler.endElement(name)

    def handle_comment(self,content):
        self.lexicalHandler.comment(content,0,len(content))

    # --- pubid resolution
        
    def resolve_entity_pubid(self,pubid,sysid):
        return self.ent_handler.resolveEntity(pubid,sysid)

    def resolve_doctype_pubid(self,pubid,sysid):
        return self.ent_handler.resolveEntity(pubid,sysid)
    
    # --- error handling

    def warning(self,msg):
	self.err_handler.warning(saxlib.SAXParseException(msg,None,self))

    def error(self,msg):
	self.err_handler.error(saxlib.SAXParseException(msg,None,self))

    def fatal(self,msg):
	self.err_handler.fatalError(saxlib.SAXParseException(msg,None,self))

    # --- location handling

    def getColumnNumber(self):
	return self.parser.get_column()

    def getLineNumber(self):
	return self.parser.get_line()

    def getSystemId(self):
	return self.parser.get_current_sysid()

    # --- DTD parsing

    def new_external_entity(self,name,pubid,sysid,ndata):
        if ndata!="":
            self.dtd_handler.unparsedEntityDecl(name,pubid,sysid,ndata)
        else:
            # FIXME: ensure that only first decl is passed on
            self.declHandler.externalEntityDecl(name,pubid,sysid)

    def new_notation(self,name,pubid,sysid):
        self.dtd_handler.notationDecl(name,pubid,sysid)

    def dtd_start(self):
	self.lexicalHandler.startDTD("","","")
    
    def dtd_end(self):
	self.lexicalHandler.endDTD()
    
    def new_general_entity(self,name,val):
        # FIXME: ensure that only first decl is passed on
	self.declHandler.internalEntityDecl(name,val)
	
    def new_element_type(self,elem_name,elem_cont):
        # FIXME: only first
        self.declHandler.elementDecl(elem_name,elem_cont)
	    
    def new_attribute(self,elem,attr,a_type,a_decl,a_def):
        # FIXME: only first
        if a_decl=="#DEFAULT": a_decl=None
        self.declHandler.attributeDecl(elem,attr,a_type,a_decl,a_def)
        
    # --- entity events

    def resolve_entity(self,pubid,sysid):
        newsysid=self.ent_handler.resolveEntity(pubid,sysid)
        if newsysid==None:
            return sysid
        else:
            return newsysid

    # --- EXPERIMENTAL PYTHON SAX EXTENSIONS:

    def get_parser_name(self):
        return "xmlproc"

    def get_parser_version(self):
        return xmlproc.version

    def get_driver_version(self):
        return version
    
    def is_validating(self):
        return 0

    def is_dtd_reading(self):
        return 1

    def reset(self):
        if hasattr(self, "parser"):
            self.parser.deref()
        self.parser=self._create_parser()
        self.parser.set_application(self)
        self.parser.set_dtd_listener(self) # FIXME: Should we always do this?
	self.parser.set_error_handler(self)
        self.parser.set_pubid_resolver(self)
	self.parser.reset()
    
    def feed(self,data):
        self.parser.feed(data)

    def close(self):
        self.parser.close()
        self.parser.deref()
        # Dereferencing to avoid circular references (grrrr)
 	self.err_handler = self.dtd_handler = self.doc_handler = None
 	self.parser = self.locator = self.ent_handler = None

    # --- Configurable methods

    def getFeature(self, featureId):
        if featureId=="http://xml.org/sax/features/use-locator":
            return self.locator
        elif featureId=="http://xml.org/sax/features/validation":
            return 0
        elif featureId=="http://garshol.priv.no/sax/stop-on-error":
            return self.stop_on_error
        elif featureId=="http://garshol.priv.no/sax/use-catalog":
            return self.catalog_file
        elif featureId=="http://xml.org/sax/features/external-general-entities" or \
           featureId=="http://xml.org/sax/features/external-parameter-entities" or \
           featureId=="http://xml.org/sax/features/namespaces" or \
           featureId=="http://xml.org/sax/features/normalize-text":
            raise saxlib.SAXNotSupportedException("Feature %s not supported" %
                                                  featureId)
        else:
            raise saxlib.SAXNotRecognizedException("Feature %s not recognized"
                                                   % featureId)       

    def setFeature(self, featureId, state):
        if featureId=="http://xml.org/sax/features/use-locator":
            self.locator=state
        elif featureId=="http://garshol.priv.no/sax/stop-on-error":
            self.stop_on_error=state
            self.parser.set_data_after_wf_error(state)
        elif featureId=="http://garshol.priv.no/sax/use-catalog":
            if state:
                if os.environ.has_key("XMLXCATALOG"):
                    self.catalog_file=os.environ["XMLXCATALOG"]
                    self.catalog_type=XCATALOG
                elif os.environ.has_key("XMLSOCATALOG"):
                    self.catalog_file=os.environ["XMLSOCATALOG"]
                    self.catalog_type=SOCATALOG
                else:
                    raise saxlib.SAXException("Neither XMLXCATALOG nor "
                                              "XMLSOCATALOG variables set")
        elif featureId=="http://xml.org/sax/features/validation" or \
           featureId=="http://xml.org/sax/features/external-general-entities" or \
           featureId=="http://xml.org/sax/features/external-parameter-entities" or \
           featureId=="http://xml.org/sax/features/namespaces" or \
           featureId=="http://xml.org/sax/features/normalize-text":
            raise saxlib.SAXNotSupportedException("Feature %s not supported" %
                                                  featureId)
        else:
            raise saxlib.SAXNotRecognizedException("Feature %s not recognized"
                                                   % featureId)

    def getProperty(self, propertyId):
        if propertyId=="http://xml.org/sax/properties/namespace-sep":
            return self.ns_separator
        elif propertyId=="http://xml.org/sax/handlers/DeclHandler":
            return self.declHandler
        elif propertyId=="http://xml.org/sax/handlers/LexicalHandler":
            return self.lexicalHandler
        elif propertyId=="http://xml.org/sax/handlers/NamespaceHandler":
            return self.namespaceHandler
        elif propertyId=="http://xml.org/sax/properties/dom-node" or \
             propertyId=="http://xml.org/sax/properties/xml-string":
            raise saxlib.SAXNotSupportedException("Property %s not supported" %
                                                  propertyId)
        elif propertyId=="http://garshol.priv.no/sax/xmlproc/dtdobj":
            return self.parser.get_dtd()
        elif propertyId=="http://garshol.priv.no/sax/catalog-file":
            return self.catalog_file
        else:
            raise saxlib.SAXNotRecognizedException("Property %s not recognized"
                                                   % propertyId)

    def setProperty(self, propertyId, value):
        if pre_parse_properties.has_key(propertyId) and self.is_parsing:
            raise saxlib.SAXNotSupportedException("Not allowed to set "
                                                  "property %s during parsing"
                                                  % propertyId)
        
        if propertyId=="http://xml.org/sax/properties/namespace-sep":
            self.ns_separator=value
        elif propertyId=="http://xml.org/sax/handlers/DeclHandler":
            self.declHandler=value
        elif propertyId=="http://xml.org/sax/handlers/LexicalHandler":
            self.lexicalHandler=value
        elif propertyId=="http://xml.org/sax/handlers/NamespaceHandler":
            self.namespaceHandler=value
        elif propertyId=="http://garshol.priv.no/sax/catalog-file":
            self.catalog_file=value
        elif propertyId=="http://xml.org/sax/properties/dom-node" or \
             propertyId=="http://garshol.priv.no/sax/xmlproc/dtdobj" or \
             propertyId=="http://xml.org/sax/properties/xml-string":
            raise saxlib.SAXNotSupportedException("Property is read-only")
        else:
            raise saxlib.SAXNotRecognizedException("Property %s not recognized"
                                                   % propertyId)
	
# --- Global functions

def create_parser():
    return SAX_XPParser()
