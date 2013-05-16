import os,sys
sys.path.append(os.path.join(os.path.split(__file__)[0], '../../../../'))
sys.path.append(os.path.join(os.path.split(__file__)[0], '../../../'))

from taocode2.models import *
from taocode2.helper import xmlo
from taocode2.helper.utils import q_get
from taocode2.apps.repos import svn
from taocode2.apps.user import activity
f = file('/tmp/hooks.log','w')
def work():
    if len(sys.argv) != 3:
        sys.exit(1)
    
    name = sys.argv[1]
    rev = sys.argv[2]
    print svn.ADMIN_REPOS(name)
    o = svn.LOG(svn.ADMIN_REPOS(name), rev)
    msg = o.log.logentry.msg
    author = getattr(o.log.logentry, 'author', None)
    if author is None:
        print 'author is None',author
        return
    
    u = q_get(User, name = str(author))
    if u is None:
        print 'user not exist!',author
        return

    prj = q_get(Project, name = name)
    if prj is None:
        print 'prj is None',name
        return
    
    activity.new_commit(prj, u, rev, str(msg))

if __name__ == '__main__':
    pass

    """
    try:
        work()
    except:
        import sys
        import traceback
        traceback.print_exc(f)
        traceback.print_exc()
     """
