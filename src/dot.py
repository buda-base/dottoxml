# coding: latin-1
# Copyright (c) 2009 Dirk Baechle.
# www: http://www.mydarc.de/dl9obn/programming/python/dottoxml
# mail: dl9obn AT darc.de
#
# This program is free software; you can redistribute it and/or modify it under
# the terms of the GNU General Public License as published by the Free Software
# Foundation; either version 2 of the License, or (at your option) any later
# version.
#
# This program is distributed in the hope that it will be useful, but WITHOUT
# ANY WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE. See the GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License along with
# this program; if not, write to the Free Software Foundation, Inc.,
# 59 Temple Place - Suite 330, Boston, MA  02111-1307, USA.
"""
  Helper classes and functions for the dottoxml.py tool
"""

import re
import X11Colors

r_label = re.compile(r'label\s*=\s*"\s*\{[^\}]*\}\s*"\s*')
r_labelstart = re.compile(r'label\s*=\s*"\s*\{')
r_labelclose = re.compile(r'\}\s*"')

def compileAttributes(attribs):
    """ return the list of attributes as a DOT text string """
    atxt = ""
    first = True
    for key, value in attribs.iteritems():
        if not first:
            atxt += ", %s=\"%s\"" % (key, value)
        else:
            atxt += "%s=\"%s\"" % (key, value)
            first = False
            
    return "[%s]" % atxt

def parseAttributes(attribs):
    """ parse the attribute list and return a key/value dict for it """
    adict = {}
    tlist = []
    lmode = False
    ltext = ''
    # First pass: split entries by ,
    for a in attribs.split(','):
        if r_label.findall(a):
            tlist.append(a)
        elif r_labelstart.findall(a):
            ltext = a
            lmode = True
        else:
            if lmode:
                ltext += ",%s" % a
                if r_labelclose.findall(a):
                    lmode = False
                    tlist.append(ltext)
            else:
                tlist.append(a)

    # Second pass: split keys from values by =
    for t in tlist:
        apos = t.find('=')
        if apos > 0:
            adict[t[:apos].strip()] = t[apos+1:].strip().strip('"')

    return adict

def getLabelAttributes(label):
    """ return the sections of the label attributes in a list structure """
    sections = []
    slist = label.split('|')
    for s in slist:
        mlist = []
        s = s.replace('\\r','\\l')
        s = s.replace('\\n','\\l')
        alist = s.split('\\l')
        for a in alist:
            a = a.strip()
            if a != "":
                mlist.append(a)
        sections.append(mlist)
    return sections

def colorNameToRgb(fcol, defaultcol):
    """ convert the color name fcol to an RGB string, if required """
    if not fcol.startswith('#'):
        return X11Colors.color_map.get(fcol, defaultcol)
    else:
        return fcol
    
def getColorAttribute(attribs, key, defaultcol, conf):
    """ extract the color for the attribute key and convert it
        to RGB format if required
    """
    if conf.Colors:
        if attribs.has_key(key):
            return colorNameToRgb(attribs[key], defaultcol)
    return defaultcol

def escapeNewlines(label):
    """ convert the newline escape sequences in the given label """
    l = label.replace('\\n','\n')
    l = l.replace('\\l','\n')
    l = l.replace('\\r','\n')
    return l

class Node:
    """ a single node in the graph """
    def __init__(self):
        self.label = ""
        self.id = 0
        self.attribs = {}
        self.referenced = False
        self.sections = []

    def initFromString(self, line):
        """ extract node info from the given text line """
        spos = line.find('[')
        atts = ""
        if spos >= 0:
            atts = line[spos+1:]
            line = line[:spos].strip()
        # Process label
        self.label = line.strip('"')
        # Process attributes
        if len(atts):
            spos = atts.rfind(']')
            if spos > 0:
                atts = atts[:spos]
                self.attribs = parseAttributes(atts)
        # Process sections
        if self.attribs.has_key("label"):
            tlabel = self.attribs["label"]
            if (tlabel != "" and     
                tlabel.startswith('{') and
                tlabel.endswith('}')):
                tlabel = tlabel[1:-1]
                self.sections = getLabelAttributes(tlabel)

    def getLabel(self, conf, multiline=False):
        """ return the label of the node """
        if conf.NodeLabels:
            if self.attribs.has_key('label'):
                if len(self.sections) > 0:
                    if multiline:
                        return '\n'.join(self.sections[0])
                    else:
                        return ','.join(self.sections[0])
                else:
                    return self.attribs['label']
            else:
                return self.label
        else:
            return ""

    def getLabelWidth(self, conf, multiline=False):
        """ return the maximum width label of the node label"""
        if conf.NodeLabels:
            if self.attribs.has_key('label'):
                if len(self.sections) > 0:
                    if multiline:
                        # Find maximum label width
                        width = 1
                        for s in self.sections[0]:
                            if len(s) > width:
                                width = len(s)
                        for s in self.sections[1]:
                            if len(s) > width:
                                width = len(s)
                        for s in self.sections[2]:
                            if len(s) > width:
                                width = len(s)
                        return width
                    else:
                        return len(','.join(self.sections[0]))
                else:
                    return len(self.attribs['label'])
            else:
                return len(self.label)
        else:
            return 0

    def complementAttributes(self, node):
        """ from node copy all new attributes, that do not exist in self """
        for a in node.attribs:
            if not self.attribs.has_key(a):
                self.attribs[k] = node.attribs[k]
                
    def exportDot(self, o, nodes, conf):
        """ write the node in DOT format to the given file """
        if len(self.attribs) > 0:
            o.write("\"%s\" %s;\n" % (self.label, compileAttributes(self.attribs)))
        else:
            o.write("\"%s\";\n" % (self.label))

    def exportGDF(self, o, conf):
        """ write the node in GDF format to the given file """
        tlabel = self.getLabel(conf)
        if tlabel == "":
            tlabel = "n%d" % self.id
        o.write("%s\n" % tlabel)

    def exportGML(self, o, conf):
        """ write the node in GML format to the given file """
        o.write("  node [\n")
        o.write("    id %d\n" % self.id)
        o.write("    label\n")
        o.write("    \"%s\"\n" % self.getLabel(conf))
        o.write("  ]\n")

    def exportGraphml(self, doc, parent, conf):        
        """ export the node in Graphml format and append it to the parent XML node """
        node = doc.createElement(u'node')
        node.setAttribute(u'id',u'n%d' % self.id)
        
        data0 = doc.createElement(u'data')
        data0.setAttribute(u'key', u'd0')

        exportUml = False
        if len(self.sections) > 0 and conf.NodeUml == True and not conf.LumpAttributes:
            exportUml = True
            snode = doc.createElement(u'y:UMLClassNode')
        else:
            snode = doc.createElement(u'y:ShapeNode')
        geom = doc.createElement(u'y:Geometry')
        geom.setAttribute(u'height',u'30.0')
        geom.setAttribute(u'width',u'30.0')
        geom.setAttribute(u'x',u'0.0')
        geom.setAttribute(u'y',u'0.0')
        snode.appendChild(geom)
        color = getColorAttribute(self.attribs, 'color', conf.DefaultNodeColor, conf)
        fill = doc.createElement(u'y:Fill')
        fill.setAttribute(u'color',u'%s' % color)
        fill.setAttribute(u'transparent',u'false')
        snode.appendChild(fill)
        border = doc.createElement(u'y:BorderStyle')
        border.setAttribute(u'color',u'#000000')
        border.setAttribute(u'type',u'line')
        border.setAttribute(u'width',u'1.0')
        snode.appendChild(border)
        color = getColorAttribute(self.attribs, 'fontcolor', conf.DefaultNodeTextColor, conf)        
        label = doc.createElement(u'y:NodeLabel')
        if conf.LumpAttributes:
            label.setAttribute(u'alignment',u'left')
        else:
            label.setAttribute(u'alignment',u'center')
        label.setAttribute(u'autoSizePolicy',u'content')
        label.setAttribute(u'fontFamily',u'Dialog')
        label.setAttribute(u'fontSize',u'12')
        label.setAttribute(u'fontStyle',u'plain')
        label.setAttribute(u'hasBackgroundColor',u'false')
        label.setAttribute(u'hasLineColor',u'false')
        label.setAttribute(u'modelName',u'internal')
        label.setAttribute(u'modelPosition',u'c')
        label.setAttribute(u'textColor',u'%s' % color)
        label.setAttribute(u'visible',u'true')
        nodeLabelText = escapeNewlines(self.getLabel(conf, True))
        if conf.LumpAttributes:
            # Find maximum label width
            width = self.getLabelWidth(conf, True)
            nodeLabelText += '\n' + conf.SepChar*width + '\n'
            nodeLabelText += u'%s\n' % '\n'.join(self.sections[1])
            nodeLabelText += conf.SepChar*width + '\n'
            nodeLabelText += u'%s' % '\n'.join(self.sections[2])
        label.appendChild(doc.createTextNode(u'%s' % nodeLabelText))        
        snode.appendChild(label)
        if exportUml and not conf.LumpAttributes:
            shape = doc.createElement(u'y:UML')
            shape.setAttribute(u'clipContent',u'true')
            shape.setAttribute(u'constraint',u'')
            shape.setAttribute(u'omitDetails',u'false')
            shape.setAttribute(u'stereotype',u'') 
            shape.setAttribute(u'use3DEffect',u'true')
     
            alabel = doc.createElement(u'y:AttributeLabel')
            alabel.appendChild(doc.createTextNode(u'%s' % '\n'.join(self.sections[1])))
            shape.appendChild(alabel)
            mlabel = doc.createElement(u'y:MethodLabel')
            mlabel.appendChild(doc.createTextNode(u'%s' % '\n'.join(self.sections[2])))
            shape.appendChild(mlabel)
        else:
            shape = doc.createElement(u'y:Shape')
            shape.setAttribute(u'type',u'rectangle')
        snode.appendChild(shape)
        data0.appendChild(snode)
        node.appendChild(data0)

        data1 = doc.createElement(u'data')
        data1.setAttribute(u'key', u'd1')
        node.appendChild(data1)
        
        parent.appendChild(node)

class Edge:
    """ a single edge in the graph """
    def __init__(self):
        self.id = 0
        self.src = ""
        self.dest = ""
        self.attribs = {}

    def initFromString(self, line):
        """ extract edge info from the given text line """
        spos = line.find('[')
        atts = ""
        if spos >= 0:
            atts = line[spos+1:]
            line = line[:spos].strip()

        # Process labels
        ll = line.split()
        if len(ll) == 3:
            self.src = ll[0].strip('"')
            self.dest = ll[2].rstrip(';').strip('"')
        # Process attributes
        if len(atts):
            spos = atts.rfind(']')
            if spos > 0:
                atts = atts[:spos]
                self.attribs = parseAttributes(atts)
                        
    def getLabel(self, nodes, conf):
        """ return the label of the edge """
        if conf.EdgeLabels:
            if self.attribs.has_key('label'):
                return self.attribs['label']
            else:
                if conf.EdgeLabelsAutoComplete:
                    srclink = self.src
                    destlink = self.dest
                    if (nodes[self.src].attribs.has_key('label')):
                        srclink = nodes[self.src].attribs['label']
                    if (nodes[self.dest].attribs.has_key('label')):
                        destlink = nodes[self.dest].attribs['label']
                    return "%s -> %s" % (srclink, destlink)
                else:
                    return ""
        else:
            return ""

    def complementAttributes(self, edge):
        """ from edge copy all new attributes, that do not exist in self """
        for a in node.attribs:
            if not self.attribs.has_key(a):
                self.attribs[k] = node.attribs[k]
                
    def exportDot(self, o, nodes, conf):
        """ write the edge in DOT format to the given file """
        if len(self.attribs) > 0:
            o.write("\"%s\" -> \"%s\" %s;\n" % (self.src, self.dest, compileAttributes(self.attribs)))
        else:
            o.write("\"%s\" -> \"%s\";\n" % (self.src, self.dest))

    def exportGDF(self, o, nodes, conf):
        """ write the edge in GDF format to the given file """
        slabel = self.src.getLabel(conf)
        if slabel == "":
            slabel = "n%d" % self.src.id
        dlabel = self.dest.getLabel(conf)
        if dlabel == "":
            dlabel = "n%d" % self.dest.id
        o.write("%s,%s\n" % (slabel, dlabel))

    def exportGML(self, o, nodes, conf):
        """ write the edge in GML format to the given file """
        o.write("  edge [\n")
        o.write("    source %d\n" % nodes[self.src].id)
        o.write("    target %d\n" % nodes[self.dest].id)
        o.write("    label\n")
        o.write("    \"%s\"\n" % self.getLabel(nodes, conf))
        o.write("  ]\n")

    def exportGraphml(self, doc, parent, nodes, conf):
        """ export the edge in Graphml format and append it to the parent XML node """
        edge = doc.createElement(u'edge')
        edge.setAttribute(u'id',u'e%d' % self.id)
        edge.setAttribute(u'source',u'n%d' % nodes[self.src].id)
        edge.setAttribute(u'target',u'n%d' % nodes[self.dest].id)
        
        data2 = doc.createElement(u'data')
        data2.setAttribute(u'key', u'd2')

        pedge = doc.createElement(u'y:PolyLineEdge')
        line = doc.createElement(u'y:LineStyle')      
        color = getColorAttribute(self.attribs, 'color', conf.DefaultEdgeColor, conf)
        line.setAttribute(u'color',u'%s' % color)
        line.setAttribute(u'type', u'line')
        line.setAttribute(u'width', u'1.0')
        pedge.appendChild(line)
        arrow = doc.createElement(u'y:Arrows')
        arrow_tail = "none"
        arrow_head = "none"
        if conf.Arrows:
            if self.attribs.has_key('arrowtail'):
                arrow_head = self.attribs['arrowtail']
            if self.attribs.has_key('arrowhead'):
                arrow_tail = self.attribs['arrowhead']
        arrow.setAttribute(u'source',u'%s' % arrow_head)                
        arrow.setAttribute(u'target',u'%s' % arrow_tail)                
        pedge.appendChild(arrow)
        if conf.EdgeLabels:
            tlabel = self.getLabel(nodes, conf)
            if tlabel != "":
                label = doc.createElement(u'y:EdgeLabel')
                color = getColorAttribute(self.attribs, 'fontcolor', conf.DefaultEdgeTextColor, conf)
                label.setAttribute(u'alignment',u'center')
                label.setAttribute(u'distance',u'2.0')
                label.setAttribute(u'fontFamily',u'Dialog')
                label.setAttribute(u'fontSize',u'12')
                label.setAttribute(u'fontStyle',u'plain')
                label.setAttribute(u'hasBackgroundColor',u'false')
                label.setAttribute(u'hasLineColor',u'false')
                label.setAttribute(u'modelName',u'six_pos')
                label.setAttribute(u'modelPosition',u'tail')
                label.setAttribute(u'textColor',u'%s' % color)
                label.setAttribute(u'visible',u'true')
                label.setAttribute(u'preferredPlacement',u'anywhere')
                label.setAttribute(u'ratio',u'0.5')
                label.appendChild(doc.createTextNode(u'%s' % escapeNewlines(tlabel)))        
                pedge.appendChild(label)
        bend = doc.createElement(u'y:BendStyle')      
        bend.setAttribute(u'smoothed', u'false')
        pedge.appendChild(bend)
        data2.appendChild(pedge)
        edge.appendChild(data2)

        data3 = doc.createElement(u'data')
        data3.setAttribute(u'key', u'd3')
        edge.appendChild(data3)
        
        parent.appendChild(edge)
