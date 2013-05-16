import sys,os
sys.path.append('..')
from taocode2.models import *
from taocode2.helper.utils import *
from django.contrib.auth import authenticate

def authapp(env, start_response):
    try:
        resp = do_auth(env)
        start_response(resp, [])
        return []
    except:
        import traceback
        traceback.print_exc()
        start_response('500 Server Error', [])
        return []

def do_daemon(pidfile):
    try:   
        pid = os.fork()   
        if pid > 0:  
            # exit first parent  
            sys.exit(0)   
    except OSError, e:   
        print >>sys.stderr, "fork #1 failed: %d (%s)" % (e.errno, e.strerror)   
        sys.exit(1)  
    # decouple from parent environment  
    os.chdir("/")   
    os.setsid()   
    os.umask(0)   
    # do second fork  
    try:   
        pid = os.fork()   
        if pid > 0:  
            # exit from second parent, print eventual PID before  
            file(pidfile, 'w').write(str(pid))
            sys.exit(0)   
    except OSError, e:   
        print >>sys.stderr, "fork #2 failed: %d (%s)" % (e.errno, e.strerror)   
        sys.exit(1)  
    

def do_auth(env):

    username = env.get('REMOTE_USER', '')
    password = env.get('REMOTE_PASSWD', '')
    rule   = env.get('FCGI_APACHE_ROLE', None)

    uri = env['REQUEST_URI']
    mtd = env['REQUEST_METHOD']
    
    pname = uri.split('/', 3)

    prj = None

    if len(pname) >= 3:
        prj = q_get(Project, name=pname[2])

    if prj is None:    
        return '404 Not Found'

    if prj.is_public and mtd in ('GET','PROPFIND','OPTIONS','REPORT'):
        # read only
        if prj.is_public:  
            return '200 Ok'

    user = authenticate(username=username, password=password)
    if user is None:
        return '401 Authentication Required'

    if prj.owner == user:  
        return '200 Ok'

    pm = q_get(ProjectMember, project = prj, user = user)
    if pm is not None: 
        return '200 Ok'

    return '401 Authentication Required'

if __name__ == '__main__':
    from flup.server.fcgi import WSGIServer
    from flup.server.fcgi_base import FCGI_RESPONDER , FCGI_AUTHORIZER
    addr = sys.argv[1]



    if addr.find(':') != -1:
        addr = addr.split(':')
        addr[1] = int(addr[1])
        addr = tuple(addr)

    if len(sys.argv) >= 3 and sys.argv[2] == '-d':
        do_daemon(sys.argv[3])

    print 'serve in', sys.argv[1], '...'

    WSGIServer(authapp, 
               bindAddress=addr,
               roles=[FCGI_RESPONDER , FCGI_AUTHORIZER]).run()
    
