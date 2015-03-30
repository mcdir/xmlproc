"""
A parser filter that automatically makes the parser pull in external
documents referred to by parsed, auto-actuated XLinks.

$Id: xlink.py,v 2.1 2000/01/18 21:43:15 larsga Exp $
"""

import namespace, xmlutils, xmlproc

# --- Constants

xlink_namespace = "http://www.w3.org/XML/XLink/0.9"
xlink_version   = "WD-xlink/19990726"

xlink_simple    = xlink_namespace + " simple"
xlink_type      = xlink_namespace + " type"
xlink_show      = xlink_namespace + " show"
xlink_actuate   = xlink_namespace + " actuate"
xlink_href      = xlink_namespace + " href"

# --- Filter

class XLinkFilter(namespace.ParserFilter):
    """An xmlproc filter that invisibly pulls in external documents
    referred to by parsed, auto-actuated XLinks."""

    def __init__(self, parser):
        namespace.ParserFilter.__init__(self)
        self.source = namespace.NamespaceFilter(parser)
        self.source.set_report_ns_attributes(0)
        self.source.set_application(self)

        self.parser = parser
        self.parser.set_application(self.source)
        
        self.elem_stack = []
        
    def handle_start_tag(self, name, attrs):
        if (name == xlink_simple or attrs.get(xlink_type) == "simple") and \
           attrs.get(xlink_show) == "parsed" and \
           attrs.get(xlink_actuate) == "auto" and \
           attrs.get(xlink_href):

            sysid = xmlutils.join_sysids(self.parser.get_current_sysid(),
                                         attrs.get(xlink_href))
            self.__parse(sysid)
            
            self.elem_stack.append(0)
        else:
            self.app.handle_start_tag(name, attrs)
            self.elem_stack.append(1)

    def handle_end_tag(self, name):
        if self.elem_stack[-1]:
            self.app.handle_end_tag(name)

        del self.elem_stack[-1]
        
    def __parse(self, sysid):
        p = xmlproc.XMLProcessor()
        p.set_application(self.source)
        # FIXME: we _need_ other handlers here (isf, pubid ...)
        #        make filter encapsulate parser?
        p.parse_resource(sysid)
        p.deref()
