"""Example macro."""

revision = "$Rev: 6326 $"
url = "$URL: http://svn.edgewall.org/repos/trac/tags/trac-0.11.7/sample-plugins/HelloWorld.py $"

#
# The following shows the code for macro, old-style.
#
# The `execute` function serves no purpose other than to illustrate
# the example, it will not be used anymore.
#
# ---- (ignore in your own macro) ----
# --
from trac.util import escape

def execute(hdf, txt, env):
    # Currently hdf is set only when the macro is called
    # From a wiki page
    if hdf:
        hdf['wiki.macro.greeting'] = 'Hello World'
        
    # args will be `None` if the macro is called without parenthesis.
    args = txt or 'No arguments'

    # then, as `txt` comes from the user, it's important to guard against
    # the possibility to inject malicious HTML/Javascript, by using `escape()`:
    return 'Hello World, args = ' + escape(args)
# --
# ---- (ignore in your own macro) ----


#
# The following is the converted new-style macro
#
# ---- (reuse for your own macro) ----
# --
from trac.wiki.macros import WikiMacroBase

class HelloWorldMacro(WikiMacroBase):
    """Simple HelloWorld macro.

    Note that the name of the class is meaningful:
     - it must end with "Macro"
     - what comes before "Macro" ends up being the macro name

    The documentation of the class (i.e. what you're reading)
    will become the documentation of the macro, as shown by
    the !MacroList macro (usually used in the TracWikiMacros page).
    """

    def expand_macro(self, formatter, name, args):
        """Return some output that will be displayed in the Wiki content.

        `name` is the actual name of the macro (no surprise, here it'll be
        `'HelloWorld'`),
        `args` is the text enclosed in parenthesis at the call of the macro.
          Note that if there are ''no'' parenthesis (like in, e.g.
          [[HelloWorld]]), then `args` is `None`.
        """
        return 'Hello World, args = ' + unicode(args)
    
    # Note that there's no need to HTML escape the returned data,
    # as the template engine (Genshi) will do it for us.
# --
# ---- (reuse for your own macro) ----
