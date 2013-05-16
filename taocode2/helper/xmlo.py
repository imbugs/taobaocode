# -*- coding: utf-8 -*-
#
# Copyright (C) 2011 Taobao .Inc
# All rights reserved.
#
# This software is licensed as described in the file COPYING, which
# you should have received as part of this distribution. The terms
# are also available at http://code.taobao.org/license.html.
#
# This software consists of voluntary contributions made by many
# individuals. For the exact contribution history, see the revision
# history and logs, available at http://code.taobao.org/.


__author__ = 'luqi@taobao.com'

from xml.dom.minidom import parseString
import xml.dom

class DOMIterator:
    def __init__(self, nodes):
        self.index = 0
        self.nodes = nodes

    def next(self):
        if self.index >= len(self.nodes):
            raise StopIteration()

        v = self.nodes[self.index]
        self.index += 1
        return v
        
class DOMObject:
    def __init__(self, d):
        self.dom = d

    def __str__(self):
        if len(self.dom.childNodes) > 0:
            return self.dom.childNodes[0].data
        return ''

    def __len__(self):
        return self.dom.length
    
    def __getitem__(self, name):
        attr = self.dom.attributes.get(name, None)
        if attr is None:
            return None
        return attr.value

    def __getattr__(self, name):
        elms = self.dom.getElementsByTagName(name)
        if len(elms) <= 0:
            raise AttributeError("not found " + name)
        if len(elms) == 1:
            return DOMObject(elms[0])
        return [DOMObject(v) for v in elms]

    def __iter__(self):
        nodes = []
        for v in self.dom.childNodes:
            if v.nodeType ==  v.ELEMENT_NODE:
                nodes.append(DOMObject(v))
        return DOMIterator(nodes)

def loads(s):
    d = parseString(s)
    return DOMObject(d)

def test():
    text = """
<users>
  <user age="20">
     <name>hello</name>
  </user>
  <user age='20'>
     <name>test</name>
  </user>
</users>
    """
    o = loads(text)
    
    for u in o.users:
        print u.name, u['age']

if __name__ == '__main__':
    test()
