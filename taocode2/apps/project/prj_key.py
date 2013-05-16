import marshal
from taocode2.helper.utils import q_get
from taocode2.models import ProjectProfile

UPLOAD_LIMIT_SIZE = 'upload_limit_size'
UPLOAD_LIMIT_COUNT = 'upload_limit_count'

WIKI_INDEX = 'wiki_index'

def get(project, name, default = None):
    v = q_get(ProjectProfile, project = project, name__iexact = name)
    if v is None:
        return default
    return marshal.loads(v.value)

def put(project, name, val):
    v = q_get(ProjectProfile, project = project , name__iexact = name)
    if v is None:
        v = ProjectProfile(project = project,
                           name = name)
    
    v.value = marshal.dumps(val)
    v.save()
