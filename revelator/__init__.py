# (C) Michael DeHaan, 2014.
#
# This file is part of Relevator
#
# Revelator is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
#
# Relevator is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with Ansible.  If not, see <http://www.gnu.org/licenses/>.

__version__ = '0.1'
__author__ = 'Michael DeHaan'

import shlex
import yaml
import StringIO


REVEAL_HEADER = """
<!doctype html>
<html lang="en">

        <head>
                <meta charset="utf-8">

                <title>%(title)s</title>

                <meta name="description" content="%(description)s">
                <meta name="author" content="%(author)s">

                <meta name="apple-mobile-web-app-capable" content="yes" />
                <meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />

                <meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">

                <link rel="stylesheet" href="css/reveal.css">
                <link rel="stylesheet" href="css/theme/default.css" id="theme">

                <!-- For syntax highlighting -->
                <link rel="stylesheet" href="lib/css/zenburn.css">

                <!-- If the query includes 'print-pdf', use the PDF print sheet -->
                <script>
                  if( window.location.search.match( /print-pdf/gi ) ) {
                    var link = document.createElement( 'link' );
                    link.rel = 'stylesheet';
                    link.type = 'text/css';
                    link.href = 'css/print/pdf.css';
                    document.getElementsByTagName( 'head' )[0].appendChild( link );
                  }
                </script>

                <!--[if lt IE 9]>
                <script src="lib/js/html5shiv.js"></script>
                <![endif]-->
        </head>

        <body>

     <div class="reveal">

                        <!-- Any section element inside of this container is displayed as a slide -->
                        <div class="slides">

"""

REVEAL_FOOTER = """

                       </div>

                </div>

                <script src="lib/js/head.min.js"></script>
                <script src="js/reveal.min.js"></script>

                <script>

                        // Full list of configuration options available here:
                        // https://github.com/hakimel/reveal.js#configuration
                        Reveal.initialize({
                                controls: true,
                                progress: true,
                                history: true,
                                center: true,
                                width: '%s',

                                theme: Reveal.getQueryHash().theme, // available themes are in /css/theme
                                transition: Reveal.getQueryHash().transition || 'default', // default/cube/page/concave/zoom/linear/fade/none

                                // Parallax scrolling
                                // parallaxBackgroundImage: 'https://s3.amazonaws.com/hakim-static/reveal-js/reveal-parallax-1.jpg',
                                // parallaxBackgroundSize: '2100px 900px',

                                // Optional libraries used to extend on reveal.js
                                dependencies: [
                                        { src: 'lib/js/classList.js', condition: function() { return !document.body.classList; } },
                                        { src: 'plugin/markdown/marked.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },
                                        { src: 'plugin/markdown/markdown.js', condition: function() { return !!document.querySelector( '[data-markdown]' ); } },
                                        { src: 'plugin/highlight/highlight.js', async: true, callback: function() { hljs.initHighlightingOnLoad(); } },
                                        { src: 'plugin/zoom-js/zoom.js', async: true, condition: function() { return !!document.body.classList; } },
                                        { src: 'plugin/notes/notes.js', async: true, condition: function() { return !!document.body.classList; } }
                                ]
                        });

                </script>

        </body>
</html>


"""

DEFAULT_AUTHOR = "Default Author"
DEFAULT_TITLE = "Default Title"
DEFAULT_DESCRIPTION = "Default Description"

class Deck(object):

   def __init__(self, filename):
       ''' Construct a new Deck object.  Takes a YAML filename as input '''

       self.filename = filename
       self.defaults = dict(
           transition = 'linear',
           fragment = None,
           frag_class = "",
           background = '#000000',
       )
       fh = open(self.filename, 'r')
       self.data = yaml.load(fh.read())
       self.io = StringIO.StringIO()
       fh.close()       
 
   def run(self):
       ''' Return the Reveal JS HTML from processing the YAML file ''' 

       self.write_header(self.data.get('header',{}))
       self.write_slides(self.data['slides'])
       self.write_footer(self.data.get('footer',{}))
       return self.io.getvalue()

   def write_slides(self, data, nested=False):
       ''' Given a list of slide data structures, write them '''

       nested_io = StringIO.StringIO()
       for x in data:
           if type(x) == dict:
               for (k,v) in x.iteritems():
                   if k == 'set_global':
                       self.defaults.update(v)

                       if self.defaults['fragment'] is not None:
                           self.defaults["frag_class"] = self.compute_fragment_class(self.defaults)
                   else:
                       raise Exception("unknown key: %s, value: %s" % (k,v))
           elif type(x) == list: 
               if not nested:
                   self.io.write(self.write_slide(x, nested=nested))
               else:
                   nested_io.write(self.write_slide(x, nested=nested))
       if nested:
           return nested_io.getvalue()


   def write_header(self, data):
       ''' Write the reveal JS header, plugging in some data from the filename '''

       self.io.write(REVEAL_HEADER % dict(
           author = data.get('author', DEFAULT_AUTHOR),
           title = data.get('title', DEFAULT_TITLE),
           description = data.get('description', DEFAULT_DESCRIPTION),
       ))

   def write_footer(self, data):
       ''' Write the reveal JS footer '''

       self.io.write(REVEAL_FOOTER % data.get('width','960'))

   def write_slide(self, slide_data, nested=False, recursive=False):
       ''' Logic to write any given slide '''

       slide_io = StringIO.StringIO()

       if not recursive:
           if not nested:
               slide_io.write("<section data-background='%(background)s' data-transition='%(transition)s'>\n" % (self.defaults))
           else:
               slide_io.write("<section>\n")

       # for each element in the slide
       for elem in slide_data:

           if type(elem) != dict:
               raise Exception("expected a list of dicts, got %s" % elem)           

           for (k,v) in elem.iteritems():

               parts = shlex.split(k)
               tag = parts[0]
               extra_style = ""
               if len(parts) > 1:
                   for part in parts[1:]:
                       if '=' in part:
                           (style, style_value) = part.split('=', 1)
                       else:
                           style = part
                           style_value = ""
                       extra_style = "%s: %s; %s" % (style, style_value, extra_style)
            
               if tag in [ 'ol', 'ul' ] :

                   # ordered lists
                   slide_io.write('<%s style="%s">' % (tag, extra_style)) 
                   for v2 in v:
                       # recursive tags
                       if isinstance(v2, list):
                           value = self.write_slide(v2, recursive=True)
                       else:
                           value = v2
                       slide_io.write("<li %s>%s</li>" % (self.defaults['frag_class'], value))
                   slide_io.write("</%s>" % tag)

               else:

                   # regular tags
                   start_key = '<%s style="%s" %s>\n' % (tag, extra_style, self.defaults['frag_class'])
                   end_key = "</%s>\n" % tag

                   # recursive tags
                   if tag != 'nested' and isinstance(v, list):
                       value = self.write_slide(v, recursive=True)
                   elif tag == 'nested':
                       start_key = ''
                       end_key = ''
                       value = self.write_slides(v, nested=True)
                   elif tag == 'raw':
                       print("raw value is: %s" % v)
                       start_key = ''
                       end_key = ''
                       value = v
                   else:
                       value = v

                   # special handling
                   if tag == 'class_notes':
                       # class notes
                       start_key = '<aside class=\'notes\'>\n'
                       end_key = '\n</aside>'

                   elif tag == 'code':
                       start_key = '<pre><code style="%s" %s>\n' % (extra_style, self.defaults['frag_class'])
                       end_key = "\n</code></pre>\n"

                   elif tag == 'link':
                       (name, link) = v
                       start_key = "<p><a href='%s' style='%s' %s>\n" % (link, extra_style, self.defaults['frag_class'])
                       end_key = "\n</a></p>\n"
                       value = name

                   elif tag == 'image':
                       start_key = "<img src='%s' style='border:0px;background-color:%s;%s' %s>" % (v, self.defaults['background'], extra_style, self.defaults['frag_class'])
                       end_key = ""
                       value = ""

                   elif tag == 'quote':
                       start_key = '<blockquote style="%s" %s>' % (extra_style, self.defaults['frag_class'])
                       end_key = '</blockquote>'

                   slide_io.write("%s%s%s" % (start_key, value, end_key))

       if not recursive:
           # end section
           slide_io.write("</section>\n")

       return slide_io.getvalue()

   def compute_fragment_class(self, defaults):
        """  Returns fragment HTML class= string. """

        if "fragment" not in defaults:
            # not specified so take the default: no fragments
            return ""
  
        elif str(defaults["fragment"]).lower().startswith("false"):
            # force no fragments
            return ""
  
        elif str(defaults["fragment"]).lower().startswith("true"):
            # want fragments but didn't specify class
            return ' class="fragment"' 
  
        else:  
            # want fragments and specified class
            return ' class="fragment %s" ' % defaults["fragment"] 
