from django.contrib.auth.decorators import login_required
from taocode2.models import *
from taocode2.helper.utils import *
from taocode2.helper import consts

from django.db.models import Count, Q
from django.core.paginator import Paginator

from tracwiki.formatter import HtmlFormatter



def t(req):
    print HtmlFormatter.build( "'''abc'''").generate()
    print HtmlFormatter.build( "[abc http://www.g.cn]").generate()
    print HtmlFormatter.build( " * x \r ** y  \r ** z ").generate()
    print HtmlFormatter.build(  """ >> ... (I said)
    > (he replied)""").generate()
    print HtmlFormatter.build(  """{{{
  #!td colspan=2
   {{{
   def hello():
     print "A and B!"
   }}}
  }}}""").generate()
    from tracwiki.tests import tests
    from cStringIO import StringIO
    from django.http import HttpResponse
    out = StringIO()
    tests.test(HtmlFormatter, out ) 
    return HttpResponse(out.getvalue())