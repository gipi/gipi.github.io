from docutils import nodes, utils
from docutils.parsers.rst import directives, roles
from django.conf import settings
import texrender
 
def get_img(formula,render_func):
    if settings.DEBUG:
        print 'DEBUG of formula: ', formula
    return render_func(formula, settings.TEX_MEDIA)

def get_latex_img(formula):
    return get_img(formula, texrender.tex_render_formula)

def get_tikz_img(formula):
    return get_img(formula, texrender.tikz_render_formula)



"""
TeX & Tikz directives
"""
def directive(get_img_func, name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    imagename = get_img_func('\n'.join(content))
    if imagename == 'error.png':
        error = state_machine.reporter.error(
                'ERROR: "%s"' % content,
                nodes.literal_block(block_text, block_text), line=lineno)
        return [error]


    url = settings.TEX_MEDIA_URL + imagename
    return [nodes.raw('', '<img class="tikz" src="%s" alt="tex generated images"/>' % url, format='html')]

def latex_directive(name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    return directive(get_latex_img, name, arguments, options, content,
            lineno, content_offset, block_text, state, state_machine)

def tikz_directive(name, arguments, options, content, lineno,
        content_offset, block_text, state, state_machine):
    return directive(get_tikz_img, name, arguments, options, content,
            lineno, content_offset, block_text, state, state_machine)


latex_directive.content = 1
directives.register_directive('latex', latex_directive)

tikz_directive.content = 1
directives.register_directive('tikz', tikz_directive)

"""
Roles
"""
def tex_role(name, rawtext, text, lineno, inliner, options={}, content=[]):
    src = rawtext.split('`')[1]
    imagename = get_latex_img(src)
    if imagename == 'error.png':
        msg = inliner.reporter.error(
                'Something goes wrong with your text: \'%s\'' % text,
                line=lineno)
        prb = inliner.problematic(rawtext, rawtext, msg)
        return [prb], [msg]


    url = settings.TEX_MEDIA_URL + imagename
    return [nodes.raw(rawtext,
        '<img class="inline tikz" src="%s" />' % url, format='html')],[]

roles.register_canonical_role('tex', tex_role)