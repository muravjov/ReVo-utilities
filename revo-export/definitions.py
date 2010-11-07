# -*- coding: utf-8 -*-
from utilities import clean_string
from words import get_word_root, get_words_from_kap, tld_to_string

class Definition:
    """Every definition consists of a primary definition (either a
    non-empty string or None) and optionally subdefinitions. Note we
    never have subsubdefinitions.

    """
    def __init__(self, primary_definition=None, subdefinitions=None,
                 examples=None):
        self.primary = primary_definition

        if subdefinitions is None:
            self.subdefinitions = []
        else:
            self.subdefinitions = subdefinitions

        if examples is None:
            self.examples = []
        else:
            self.examples = examples

    def __eq__(self, other):
        if self.primary != other.primary:
            return False
        if self.subdefinitions != other.subdefinitions:
            return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def is_empty(self):
        if self.primary is None and self.subdefinitions == []:
            return True
        return False

    def get_all(self):
        """Convenience function for JSON export."""
        return (self.primary, self.examples, self.subdefinitions)

def get_reference_to_another(ref_node):
    """If a word is only defined by a reference to another (a <ref>),
    return a string that describes the reference. Note that there are other
    ways in which <ref> are used which are not relevant here.

    """
    assert ref_node.attrib['tip'] == 'dif' or ref_node.tag == 'refgrp'
    
    reference = ""

    if ref_node.text:
        reference += ref_node.text
    for node in ref_node:
        if node.tag == 'tld':
            reference += get_word_root(node)
        if node.text is not None:
            reference += node.text
        if node.tail is not None:
            reference += node.tail

    reference = "Vidu " + reference.strip()
    if not reference.endswith('.'):
        reference += '.'

    return reference

def get_definition_string(dif_node):
    """Convert a definition node to a simple unicode string (this
    requires us to flatten it), and handle any references we
    encounter.

    """
    definition = ""

    if dif_node.text is not None:
        definition += dif_node.text
    for node in dif_node:
        if node.tag == 'ekz':
            # skip examples
            continue
        if node.tag == 'tld':
            definition += get_word_root(node)
        if node.tag == 'refgrp':
            definition += get_reference_to_another(node)
        if node.tag == 'ref' and 'tip' in node.attrib \
                and node.attrib['tip'] == 'dif':
            definition += get_reference_to_another(node)
        if node.text is not None:
            definition += node.text
        if node.tail is not None:
            definition += node.tail
    
    final_string = clean_string(definition)

    # if this definition has examples, it ends with a colon not a full stop
    # however we don't want those as we deal with examples separately
    if final_string.endswith(':'):
        final_string = final_string[:-1] + '.'

    return final_string

def get_transitivity(node):
    assert node.tag == 'drv' or node.tag == 'snc'

    for child in node.getchildren():
        if child.tag == 'gra':
            vspec_node = child.getchildren()[0]
            assert vspec_node.tag == 'vspec', 'Expected vspec inside <gra>'
            if vspec_node.text == 'tr':
                return "(transitiva)"
            elif vspec_node.text == 'ntr':
                return "(netransitiva)"
            else:
                return None # adv (presumable adverb) and so on

    return None

def flatten_example(ekz_node):
    """Get the contents of an <ekz>, discarding <fnt> but replacing
    <tld>. Since a series of examples are often written in the form
    'foo; bar; baz.' we also discard trailing full stops or
    semicolons.

    An example:

    <ekz>
      kion vi legas mia princo? <tld/>ojn, <tld/>ojn, <tld/>ojn
      <fnt>Z</fnt>!
    </ekz>

    <ekz>
      <ctl>popolo</ctl>, <ctl>foliaro</ctl>, <ctl>herbo</ctl>,
      <ctl>armeo</ctl> estas ar<tld/>oj.
    </ekz>
    (both from vort.xml)

    <ekz>
      <tld/>o de reno
    </ekz>;
    (from ablaci.xml)

    <ekz>
      <ind>saluton!</ind>
      [...]
    </ekz>
    (from salut.xml)
    """
    flat_string = ""

    if ekz_node.text:
        flat_string += ekz_node.text
    for child in ekz_node.getchildren():
        if child.tag == 'tld':
            flat_string += tld_to_string(child)
        if child.tag == 'ctl':
            # ctl = citilo = quotation mark, we use the same as vikipedio
            flat_string += u"«%s»" % child.text

        if child.tag == 'ind':
            flat_string += child.text

        if child.tail:
            flat_string += child.tail

    flat_string = clean_string(flat_string)

    # remove trailing semicolon/full stop due to the examples being
    # written as a series
    if flat_string.endswith(';') or flat_string.endswith('.'):
        flat_string = flat_string[:-1]

    return flat_string

def get_examples(dif_node):
    """Get all examples from a dif node. This is inlined text of the
    following form:

    <ekz>
      simpla, kunmetita, dubsenca <tld/>o;
    </ekz><ekz>
      uzi la &gcirc;ustan, konvenan <tld/>on;
    </ekz><ekz>
      la bildoj elvokitaj de la <tld/>oj;
    </ekz><ekz>
      <tld/>ordo.
    </ekz>

    """
    examples = []
    for child in dif_node.getchildren():
        if child.tag == 'ekz':
            examples.append(flatten_example(child))

    return examples

def get_definition(snc_node):
    """Build a Definition from this <snc> and add any subdefinitions if
    present and any examples if present.

    Every <snc> contains a primary definition (a <dif>), a reference
    (i.e. a 'see foo' definition, a <ref>) or a subdefinitions (<dif>s
    inside <subsnc>s).

    """
    # we gradually populate the Deifinition
    definition = Definition()

    for child in snc_node.getchildren():
        if child.tag == 'dif':
            definition.primary = get_definition_string(child)
            definition.examples = get_examples(child)

    # if no <dif>, may have a <ref> that points to another word
    if definition.primary is None:
        for child in snc_node.getchildren():
            if child.tag == 'ref' and 'tip' in child.attrib and \
                    child.attrib['tip'] == 'dif':
                definition.primary = get_reference_to_another(child)
            elif child.tag == 'refgrp':
                definition.primary = get_reference_to_another(child)
            
    # note: may not have either <dif> or <ref> (e.g. sxilin.xml)

    # add transitivity notes if present, could be on <snc> or on <drv>
    transitivity = get_transitivity(snc_node)
    if not transitivity:
        transitivity = get_transitivity(snc_node.getparent())
    if definition.primary and transitivity:
        definition.primary = transitivity + ' ' + definition.primary

    # if the primary definition is an empty string then we've done
    # something wrong or there's something wrong with the data (eg
    # bulgari.xml which is completely devoid of a definition)
    if definition.primary == '':
        kap_node = snc_node.getparent().find('kap')
        print "Warning: '%s' has an example-only definition, skipping." % get_words_from_kap(kap_node)[0]
        return Definition()

    # get any subdefinitions
    subdefinitions = []
    for child in snc_node.getchildren():
        if child.tag == 'subsnc':
            # either a dif or a ref to another word
            dif_node = child.find('dif')
            if dif_node is not None:
                subdefinitions.append(get_definition_string(dif_node))
            else:
                for grandchild in child.getchildren():
                    if child.tag == 'ref' and 'tip' in child.attrib and \
                            child.attrib['tip'] == 'dif':
                        subdefinitions.append(get_reference_to_another(grandchild))

    definition.subdefinitions = subdefinitions

    return definition

def get_all_definitions(drv_node):
    """For a given entry (which is a single <drv> node), get all its
    definitions. I have tested this as far as possible but bugs may
    remain given the complexity and variability of the XML.

    Generally, a primary definition is a <dif> inside a <snc> and a
    subdefinition is a <dif> inside a <subsnc> inside a <snc>.

    Some representative examples are:
    sxiling.xml and vort.xml for subsenses
    apetit.xml for notes that the term is figurative
    jakobi1.xml only <ref>, no <dif> node
    frakci.xml only <ref> but huge and complex
    ad.xml has a load of stuff, some of which is not documented
    
    """
    definitions = []

    # there may be a definition outside of a <snc> (yes, this isn't simple)
    for node in drv_node.getchildren():
        if node.tag == 'dif':
            # outside a <snc> we do not have subdefinitions
            definitions.append(Definition(get_definition_string(node)))

    for sense in drv_node.findall('snc'):
        definitions.append(get_definition(sense))

    # remove any duplicates (happens with multiple <ref>s
    # e.g. direkt3.xml) or empty definitions (happens with example
    # only senses, such as purigi in pur.xml)
    no_duplicates = []
    for definition in definitions:
        if definition not in no_duplicates and not definition.is_empty():
            no_duplicates.append(definition)
    
    return no_duplicates
