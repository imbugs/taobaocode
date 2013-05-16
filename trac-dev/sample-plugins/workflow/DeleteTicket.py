from genshi.builder import tag

from trac.core import implements,Component
from trac.ticket.api import ITicketActionController
from trac.perm import IPermissionRequestor

revision = "$Rev: 6326 $"
url = "$URL: http://svn.edgewall.org/repos/trac/tags/trac-0.11.7/sample-plugins/workflow/DeleteTicket.py $"

class DeleteTicketActionController(Component):
    """Provides the admin with a way to delete a ticket.

    Illustrates how to create an action controller with side-effects.

    Don't forget to add `DeleteTicketActionController` to the workflow
    option in [ticket].
    If there is no workflow option, the line will look like this:

    workflow = ConfigurableTicketWorkflow,DeleteTicketActionController
    """

    implements(ITicketActionController, IPermissionRequestor)

    # IPermissionRequestor methods

    def get_permission_actions(self):
        return ['TICKET_DELETE']

    # ITicketActionController methods

    def get_ticket_actions(self, req, ticket):
        actions = []
        if 'TICKET_DELETE' in req.perm(ticket.resource):
            actions.append((0,'delete'))
        return actions

    def get_all_status(self):
        return []

    def render_ticket_action_control(self, req, ticket, action):
        return ("delete ticket", '', "This ticket will be deleted.")

    def get_ticket_changes(self, req, ticket, action):
        return {}

    def apply_action_side_effects(self, req, ticket, action):
        # Be paranoid here, as this should only be called when
        # action is delete...
        if action == 'delete': 
            ticket.delete()
