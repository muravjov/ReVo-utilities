# -*- coding: utf-8 -*-
from words import tld_to_string
from utilities import clean_string

"""Flatten methods, node-specific. We use reflection to pick the right
one.

These methods are catch-alls, but for some nodes (such as definitions)
we have written custom methods outside of this module.

"""

class SkipNodes(Exception):
    """If we have reached a node that we want to skip, and we want to
    skip its children we throw this exception.

    """
    pass
def _flatten_tld(tld_node):
    """<tld/> means the root for this word.

    """
    return tld_to_string(tld_node)

def _flatten_ctl(ctl_node):
    """<ctl> means quotation mark ('citilo'). We've chosen to use the
    same type of quotation mark as the Esperanto wikipedia. Note
    clean_string has to deal with cases where literal quotes are used.

    """
    if ctl_node.text:
        return u"«%s»" % ctl_node.text
    else:
        return ""

def _flatten_ind(ind_node):
    """Relates to a ReVo index somehow. The ReVo index isn't relevant
    to us but the content of the node is.

    """
    if ind_node.text:
        return ind_node.text
    else:
        return ""

def _flatten_rim(rim_node):
    """A remark.

    Example input:

    <rim>
      La vorto aperas en la Fundamento nur en la formo
      <ctl>L. L. Zamenhof</ctl>.
    </rim>
    (from zamenhof.xml)

    """
    remark_string = "Rimarko: "
    if rim_node.text:
        remark_string += rim_node.text

    return remark_string

def _flatten_ref(ref_node):
    """A <ref> is a reference to another word. This may be an inline
    reference that we just treat as text, or may be a 'see also' /
    synonym / antonym which we add text to say so (ReVo just uses
    symbols for this).

    <ref>s that we just treat as text are often labelled as to how
    they relate (e.g. x is a part of y uses tip='prt') but this is not
    relevant to us.

    """
    reference = ""

    if ref_node.text:
        reference += ref_node.text

    # attributes can be on <ref> or parent <refgrp>, so get all
    # (lxml attrib is dict-like but doesn't have a proper update method)
    attributes = dict(ref_node.attrib)
    if ref_node.getparent().tag == 'refgrp':
        parent_attributes = ref_node.getparent().attrib
        attributes.update(dict(parent_attributes))

    # add 'see also' if appropriate
    if attributes.get('tip') in ['dif', 'vid']:
        reference = "Vidu: " + reference.strip()

    # add synonym note if appropriate
    if attributes.get('tip') == 'sin':
        reference = "Sinonimo: " + reference.strip()

    # add antonym note if appropriate
    if attributes.get('tip') == 'ant':
        reference = "Antonimo: " + reference.strip()

    return reference

def _flatten_generic(node):
    """Flatten a node for which we don't have any corner cases to deal
    with.

    """
    if node.text:
        return node.text
    else:
        return ""

def get_flatten_method(node):
    """Use reflection to find a node type specific flattener if
    one exists, otherwise return a generic flattener.
    
    """
    # try to find a method defined for this node type
    flatten_method_name = '_flatten_' + node.tag
    if flatten_method_name in globals():
        return globals()[flatten_method_name]
    else:
        return _flatten_generic

def _flatten(node, skip_tags=None):
    """Recursively flatten this structure. If we've defined a
    flatten method for this type of node, we use reflection to get
    it.

    """
    if skip_tags:
        if node.tag in skip_tags:
            return ""

    # get and apply the matching flatten method
    flat_string = get_flatten_method(node)(node)

    # flatten children
    for child in node.getchildren():
        flat_string += _flatten(child, skip_tags)

    # add any trailing text
    if node.tail:
        flat_string += node.tail

    return flat_string


# high level method:
def flatten_node(node, skip_tags=None):
    """Return a friendly string representing the contents of this node
    and its children. This method is generic although occasionally we
    need methods which are specific to a certain node type.

    skip_tags specifies node tags for a node which we don't recurse
    into.

    Some examples:

    <rim>
      La tuta terminologio pri <tld/>oj, <tld/>-vektoroj kaj -subspacoj
      de endomorfio ekzistas anka&ubreve; 
      por <frm>(<k>n</k>,<k>n</k>)</frm>-matrico, konvencie
      identigita kun la endomorfio, kies matrico rilate al la kanona bazo
      de <frm><g>K</g><sup><k>n</k></sup></frm> &gcirc;i estas.
    </rim>
    (from ajgen.xml)

    <ekz>
      <ctl>popolo</ctl>, <ctl>foliaro</ctl>, <ctl>herbo</ctl>,
      <ctl>armeo</ctl> estas ar<tld/>oj.
    </ekz>
    (from vort.xml)

    <ekz>
      <ind>saluton!</ind>
      [...]
    </ekz>
    (from salut.xml)

    <klr>(de <ref cel="polino.0o">polinomo</ref>)</klr>
    (from radik.xml)

    """
    flat_string = get_flatten_method(node)(node)
    
    for child in node.getchildren():
        flat_string += _flatten(child, skip_tags)

    return clean_string(flat_string)

